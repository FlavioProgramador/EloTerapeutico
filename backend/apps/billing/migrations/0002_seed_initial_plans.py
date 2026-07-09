from typing import Any

from django.db import migrations


PlanSeed = dict[str, Any]


def seed_plans(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    plans: list[PlanSeed] = [
        {
            "name": "Essencial",
            "slug": "essencial",
            "description": "Para terapeutas que estão começando a organizar agenda, pacientes e prontuários.",
            "price": "49.90",
            "max_patients": 20,
            "max_storage_mb": 512,
            "has_agenda": True,
            "has_patients": True,
            "has_clinical_records": True,
            "has_financial": False,
            "has_documents": True,
            "has_forms": False,
            "has_reports": False,
            "has_ai": False,
        },
        {
            "name": "Profissional",
            "slug": "profissional",
            "description": "Plano recomendado para consultórios com financeiro, documentos, formulários e relatórios.",
            "price": "89.90",
            "max_patients": None,
            "max_storage_mb": 2048,
            "has_agenda": True,
            "has_patients": True,
            "has_clinical_records": True,
            "has_financial": True,
            "has_documents": True,
            "has_forms": True,
            "has_reports": True,
            "has_ai": False,
        },
        {
            "name": "Premium",
            "slug": "premium",
            "description": "Para quem precisa de todos os módulos, relatórios completos e recursos de IA.",
            "price": "149.90",
            "max_patients": None,
            "max_storage_mb": None,
            "has_agenda": True,
            "has_patients": True,
            "has_clinical_records": True,
            "has_financial": True,
            "has_documents": True,
            "has_forms": True,
            "has_reports": True,
            "has_ai": True,
        },
    ]
    for data in plans:
        defaults = {
            "currency": "BRL",
            "billing_cycle": "MONTHLY",
            "is_active": True,
            **data,
        }
        Plan.objects.update_or_create(slug=str(data["slug"]), defaults=defaults)


def remove_seeded_plans(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    Plan.objects.filter(slug__in=["essencial", "profissional", "premium"]).delete()


class Migration(migrations.Migration):
    dependencies = [("billing", "0001_initial")]

    operations = [migrations.RunPython(seed_plans, reverse_code=remove_seeded_plans)]
