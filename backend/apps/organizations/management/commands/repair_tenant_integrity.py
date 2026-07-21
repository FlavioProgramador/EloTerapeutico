"""Reparos conservadores para invariantes multi-tenant comprováveis."""

from __future__ import annotations

from typing import cast

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import models, transaction
from django.utils import timezone

from apps.organizations.models import (
    Organization,
    OrganizationMembership,
    OrganizationSettings,
    ProfessionalProfile,
)


class Command(BaseCommand):
    help = "Repara somente vínculos de tenant determinísticos; ambiguidades permanecem para revisão."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--organization-id")

    def handle(self, *args, **options):
        organizations = Organization.objects.all().order_by("created_at")
        if options.get("organization_id"):
            organizations = organizations.filter(pk=options["organization_id"])

        counters = {"owners": 0, "settings": 0, "profiles": 0, "records": 0}
        with transaction.atomic():
            for organization in organizations:
                membership = self._ensure_owner(organization, counters)
                _, created = OrganizationSettings.objects.get_or_create(
                    organization=organization,
                    defaults={
                        "default_timezone": organization.timezone,
                        "business_name_on_documents": organization.name,
                    },
                )
                counters["settings"] += int(created)
                if membership is not None:
                    _, created = ProfessionalProfile.objects.get_or_create(
                        membership=membership,
                        defaults={
                            "display_name": getattr(membership.user, "display_name", "")
                            or membership.user.full_name,
                            "public_email": membership.user.email,
                            "default_appointment_duration": getattr(
                                membership.user,
                                "default_session_duration",
                                50,
                            ),
                            "default_session_value": getattr(
                                membership.user,
                                "default_session_value",
                                0,
                            ),
                        },
                    )
                    counters["profiles"] += int(created)
            counters["records"] += self._repair_relations()
            if options["dry_run"]:
                transaction.set_rollback(True)

        self.stdout.write(
            self.style.SUCCESS(
                "Reparo concluído: "
                f"owners={counters['owners']}, settings={counters['settings']}, "
                f"profiles={counters['profiles']}, registros={counters['records']}."
            )
        )

    def _ensure_owner(self, organization, counters):
        owner = (
            organization.memberships.filter(
                role=OrganizationMembership.Role.OWNER,
                status=OrganizationMembership.Status.ACTIVE,
            )
            .select_related("user")
            .first()
        )
        if owner is not None:
            return owner
        if organization.created_by_id is None:
            return None
        membership, created = OrganizationMembership.objects.get_or_create(
            organization=organization,
            user_id=organization.created_by_id,
            defaults={
                "role": OrganizationMembership.Role.OWNER,
                "status": OrganizationMembership.Status.ACTIVE,
                "joined_at": timezone.now(),
            },
        )
        if not created:
            membership.role = OrganizationMembership.Role.OWNER
            membership.status = OrganizationMembership.Status.ACTIVE
            if membership.joined_at is None:
                membership.joined_at = timezone.now()
            membership.save(update_fields=["role", "status", "joined_at", "updated_at"])
        counters["owners"] += 1
        return membership

    def _repair_relations(self) -> int:
        total = 0
        relation_candidates = ("patient", "appointment", "package", "membership")
        for model in apps.get_models():
            field_names = {field.name for field in model._meta.get_fields()}
            if "organization" not in field_names or model._meta.app_label == "organizations":
                continue
            pending = model._default_manager.filter(organization__isnull=True)
            for relation in relation_candidates:
                if relation not in field_names:
                    continue
                related_model = cast(type[models.Model], model._meta.get_field(relation).related_model)
                related_fields = {field.name for field in related_model._meta.get_fields()}
                if "organization" not in related_fields:
                    continue
                for object_id, organization_id in pending.exclude(
                    **{f"{relation}__organization__isnull": True}
                ).values_list("pk", f"{relation}__organization_id").iterator(chunk_size=500):
                    total += model._default_manager.filter(
                        pk=object_id,
                        organization__isnull=True,
                    ).update(organization_id=organization_id)
                pending = model._default_manager.filter(organization__isnull=True)
                if not pending.exists():
                    break
        return total
