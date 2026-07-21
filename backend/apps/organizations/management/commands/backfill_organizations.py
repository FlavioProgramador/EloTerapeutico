"""Backfill idempotente de organizações e vínculos tenant-owned."""

from __future__ import annotations

import json
from pathlib import Path

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.organizations.models import (
    Organization,
    OrganizationMembership,
    OrganizationSettings,
    ProfessionalProfile,
)
from apps.organizations.services.organizations import create_organization


class Command(BaseCommand):
    help = "Cria organizações individuais e associa registros existentes ao tenant correto."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--batch-size", type=int, default=200)
        parser.add_argument("--user-id", type=int)
        parser.add_argument("--organization-id")
        parser.add_argument("--report-file")
        parser.add_argument("--resume", action="store_true")

    def handle(self, *args, **options):
        batch_size = max(int(options["batch_size"]), 1)
        report_path = Path(options["report_file"]) if options.get("report_file") else None
        report = self._load_report(report_path, resume=options["resume"])
        processed_ids = set(report.get("processed_user_ids", []))

        users = get_user_model().objects.filter(is_active=True).order_by("pk")
        if options.get("user_id"):
            users = users.filter(pk=options["user_id"])
        if not users.exists():
            raise CommandError("Nenhum usuário ativo foi encontrado para o backfill.")

        requested_organization = None
        if options.get("organization_id"):
            try:
                requested_organization = Organization.objects.get(pk=options["organization_id"])
            except (Organization.DoesNotExist, ValueError) as exc:
                raise CommandError("A organização informada não existe.") from exc
            if not options.get("user_id"):
                raise CommandError("--organization-id exige --user-id para evitar associação ambígua.")

        dry_run = bool(options["dry_run"])
        total = users.count()
        self.stdout.write(f"Processando {total} usuário(s); dry-run={dry_run}.")

        with transaction.atomic():
            for offset in range(0, total, batch_size):
                for user in users[offset : offset + batch_size]:
                    if options["resume"] and user.pk in processed_ids:
                        continue
                    organization = self._ensure_user_organization(
                        user=user,
                        requested_organization=requested_organization,
                        report=report,
                    )
                    self._backfill_owned_models(user=user, organization=organization, report=report)
                    report.setdefault("processed_user_ids", []).append(user.pk)
                    processed_ids.add(user.pk)
                self._write_report(report_path, report)

            self._backfill_relational_models(report)
            report["finished_at"] = timezone.now().isoformat()
            report["dry_run"] = dry_run
            self._write_report(report_path, report)
            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write(
            self.style.SUCCESS(
                "Backfill concluído. "
                f"Organizações criadas: {report.get('organizations_created', 0)}; "
                f"registros associados: {sum(report.get('models_updated', {}).values())}."
            )
        )

    def _load_report(self, path: Path | None, *, resume: bool) -> dict:
        if resume and path and path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    return payload
            except (OSError, json.JSONDecodeError) as exc:
                raise CommandError("Não foi possível retomar o relatório informado.") from exc
        return {
            "started_at": timezone.now().isoformat(),
            "organizations_created": 0,
            "memberships_created": 0,
            "profiles_created": 0,
            "settings_created": 0,
            "models_updated": {},
            "ambiguous_records": {},
            "processed_user_ids": [],
        }

    def _write_report(self, path: Path | None, report: dict) -> None:
        if not path:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    def _ensure_user_organization(self, *, user, requested_organization, report: dict):
        membership = (
            OrganizationMembership.objects.filter(
                user=user,
                status=OrganizationMembership.Status.ACTIVE,
            )
            .select_related("organization")
            .order_by("-is_default", "created_at")
            .first()
        )
        if requested_organization is not None:
            membership, created = OrganizationMembership.objects.get_or_create(
                organization=requested_organization,
                user=user,
                defaults={
                    "role": OrganizationMembership.Role.OWNER,
                    "status": OrganizationMembership.Status.ACTIVE,
                    "is_default": not OrganizationMembership.objects.filter(
                        user=user,
                        is_default=True,
                    ).exists(),
                    "joined_at": timezone.now(),
                },
            )
            if created:
                report["memberships_created"] += 1
            organization = requested_organization
        elif membership is not None:
            organization = membership.organization
        else:
            display_name = getattr(user, "full_name", "") or getattr(user, "email", "Profissional")
            organization = create_organization(
                actor=user,
                data={
                    "name": f"Consultório de {display_name}"[:160],
                    "organization_type": Organization.Type.INDIVIDUAL,
                    "email": getattr(user, "email", ""),
                    "phone": getattr(user, "phone", ""),
                    "timezone": getattr(user, "timezone", "America/Sao_Paulo"),
                },
            )
            report["organizations_created"] += 1
            report["memberships_created"] += 1
            report["profiles_created"] += 1
            report["settings_created"] += 1
            membership = OrganizationMembership.objects.get(organization=organization, user=user)

        _, settings_created = OrganizationSettings.objects.get_or_create(
            organization=organization,
            defaults={
                "default_timezone": organization.timezone,
                "business_name_on_documents": organization.name,
            },
        )
        _, profile_created = ProfessionalProfile.objects.get_or_create(
            membership=membership,
            defaults={
                "display_name": getattr(user, "display_name", "") or getattr(user, "full_name", ""),
                "professional_title": getattr(user, "profession", ""),
                "council_type": "CRP" if getattr(user, "crp_number", "") else "",
                "council_number": getattr(user, "crp_number", ""),
                "specialties": [getattr(user, "specialty", "")] if getattr(user, "specialty", "") else [],
                "bio": getattr(user, "bio", ""),
                "phone": getattr(user, "phone", ""),
                "public_email": getattr(user, "email", ""),
                "default_appointment_duration": getattr(user, "default_session_duration", 50),
                "default_session_value": getattr(user, "default_session_value", 0),
                "accepts_online": getattr(user, "default_modality", "") in {"online", "hybrid"},
                "accepts_in_person": getattr(user, "default_modality", "in_person") in {"in_person", "hybrid"},
            },
        )
        if settings_created:
            report["settings_created"] += 1
        if profile_created:
            report["profiles_created"] += 1
        return organization

    def _tenant_models(self):
        for model in apps.get_models():
            if model._meta.app_label in {"organizations", "auth", "contenttypes", "sessions", "admin"}:
                continue
            field_names = {field.name for field in model._meta.get_fields()}
            if "organization" in field_names:
                yield model, field_names

    def _backfill_owned_models(self, *, user, organization, report: dict) -> None:
        for model, field_names in self._tenant_models():
            ownership_filter = None
            if "therapist" in field_names:
                ownership_filter = {"therapist_id": user.pk}
            elif "owner" in field_names:
                ownership_filter = {"owner_id": user.pk}
            elif "user" in field_names and model._meta.app_label not in {"audit"}:
                ownership_filter = {"user_id": user.pk}
            if not ownership_filter:
                continue
            updated = model._default_manager.filter(
                organization__isnull=True,
                **ownership_filter,
            ).update(organization=organization)
            if updated:
                label = model._meta.label_lower
                report["models_updated"][label] = report["models_updated"].get(label, 0) + updated

    def _backfill_relational_models(self, report: dict) -> None:
        relation_candidates = ("patient", "appointment", "package", "communication", "membership")
        for model, field_names in self._tenant_models():
            pending = model._default_manager.filter(organization__isnull=True)
            for relation in relation_candidates:
                if relation not in field_names:
                    continue
                relation_model = model._meta.get_field(relation).related_model
                related_fields = {field.name for field in relation_model._meta.get_fields()}
                if "organization" not in related_fields:
                    continue
                ids = list(
                    pending.exclude(**{f"{relation}__organization__isnull": True})
                    .values_list("pk", f"{relation}__organization_id")
                    .iterator(chunk_size=500)
                )
                for object_id, organization_id in ids:
                    updated = model._default_manager.filter(
                        pk=object_id,
                        organization__isnull=True,
                    ).update(organization_id=organization_id)
                    if updated:
                        label = model._meta.label_lower
                        report["models_updated"][label] = report["models_updated"].get(label, 0) + updated
                pending = model._default_manager.filter(organization__isnull=True)
                if not pending.exists():
                    break
            remaining = list(pending.values_list("pk", flat=True)[:100])
            if remaining:
                report["ambiguous_records"][model._meta.label_lower] = remaining
