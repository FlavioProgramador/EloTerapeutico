"""Auditoria de integridade multi-tenant sem expor dados clínicos."""

from __future__ import annotations

import json
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Q
from django.utils import timezone

from apps.organizations.models import Organization, OrganizationMembership


class Command(BaseCommand):
    help = "Verifica ausência de tenant, relações cruzadas e invariantes de memberships."

    def add_arguments(self, parser):
        parser.add_argument("--fail-on-error", action="store_true")
        parser.add_argument("--format", choices=("text", "json"), default="text")
        parser.add_argument("--report-file")

    def handle(self, *args, **options):
        report = {
            "checked_at": timezone.now().isoformat(),
            "errors": [],
            "warnings": [],
            "models": {},
        }
        self._check_memberships(report)
        self._check_tenant_models(report)

        payload = json.dumps(report, ensure_ascii=False, indent=2)
        if options.get("report_file"):
            path = Path(options["report_file"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(payload, encoding="utf-8")
        if options["format"] == "json":
            self.stdout.write(payload)
        else:
            self.stdout.write(
                f"Integridade tenant: {len(report['errors'])} erro(s), "
                f"{len(report['warnings'])} alerta(s)."
            )
            for item in report["errors"]:
                self.stdout.write(self.style.ERROR(f"- {item['code']}: {item['count']}"))
            for item in report["warnings"]:
                self.stdout.write(self.style.WARNING(f"- {item['code']}: {item['count']}"))
        if report["errors"] and options["fail_on_error"]:
            raise CommandError("A auditoria encontrou violações de isolamento por tenant.")

    def _add(self, report: dict, bucket: str, code: str, count: int, model: str = ""):
        if count:
            report[bucket].append({"code": code, "count": count, "model": model})

    def _check_memberships(self, report: dict) -> None:
        organizations_without_owner = Organization.objects.exclude(status=Organization.Status.ARCHIVED).filter(
            ~Q(
                memberships__role=OrganizationMembership.Role.OWNER,
                memberships__status=OrganizationMembership.Status.ACTIVE,
            )
        ).count()
        duplicate_defaults = (
            OrganizationMembership.objects.filter(is_default=True)
            .values("user_id")
            .annotate(total=Count("pk"))
            .filter(total__gt=1)
            .count()
        )
        active_memberships_in_archived = OrganizationMembership.objects.filter(
            organization__status=Organization.Status.ARCHIVED,
            status=OrganizationMembership.Status.ACTIVE,
        ).count()
        self._add(report, "errors", "ORGANIZATION_WITHOUT_ACTIVE_OWNER", organizations_without_owner)
        self._add(report, "errors", "MULTIPLE_DEFAULT_MEMBERSHIPS", duplicate_defaults)
        self._add(report, "warnings", "ACTIVE_MEMBERSHIP_IN_ARCHIVED_ORGANIZATION", active_memberships_in_archived)

    def _check_tenant_models(self, report: dict) -> None:
        relation_candidates = ("patient", "appointment", "package", "membership")
        ignored_apps = {"organizations", "auth", "contenttypes", "sessions", "admin"}
        for model in apps.get_models():
            if model._meta.app_label in ignored_apps:
                continue
            field_names = {field.name for field in model._meta.get_fields()}
            if "organization" not in field_names:
                continue
            label = model._meta.label_lower
            missing = model._default_manager.filter(organization__isnull=True).count()
            report["models"][label] = {"without_organization": missing, "cross_tenant": 0}
            self._add(report, "errors", "MISSING_ORGANIZATION", missing, label)

            cross_total = 0
            for relation in relation_candidates:
                if relation not in field_names:
                    continue
                related_model = model._meta.get_field(relation).related_model
                related_fields = {field.name for field in related_model._meta.get_fields()}
                if "organization" not in related_fields:
                    continue
                cross_total += model._default_manager.exclude(organization__isnull=True).exclude(
                    **{f"{relation}__organization_id": models_f("organization_id")}
                ).count()
            report["models"][label]["cross_tenant"] = cross_total
            self._add(report, "errors", "CROSS_TENANT_RELATION", cross_total, label)


def models_f(field_name: str):
    from django.db.models import F

    return F(field_name)
