"""Services de templates de documentos."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.documents.models import DocumentTemplate


class DocumentDomainError(Exception):
    """Erro de domínio seguro para exposição pela API."""

    # TODO: mover para core.exceptions quando o app core tiver um
    # módulo de exceções compartilhadas. Hoje só documents e agenda
    # definem DocumentDomainError localmente.


@dataclass(frozen=True)
class PlaceholderDefinition:
    key: str
    label: str
    group: str
    description: str


class DocumentPlaceholderService:
    """Definições, validação, renderização e contextos de placeholders."""

    PATTERN = re.compile(r"{{\s*([a-zA-Z0-9_.]+)\s*}}")
    MAX_LENGTH = 50_000

    DEFINITIONS = (
        PlaceholderDefinition("paciente.nome", "Nome do paciente", "Paciente", "Nome preferencial do paciente."),
        PlaceholderDefinition("paciente.nome_completo", "Nome completo", "Paciente", "Nome civil completo."),
        PlaceholderDefinition("paciente.nome_social", "Nome social", "Paciente", "Nome social, quando informado."),
        PlaceholderDefinition("paciente.cpf", "CPF", "Paciente", "CPF formatado do paciente."),
        PlaceholderDefinition(
            "paciente.data_nascimento", "Data de nascimento", "Paciente", "Data no formato brasileiro."
        ),
        PlaceholderDefinition("paciente.idade", "Idade", "Paciente", "Idade calculada na data de emissão."),
        PlaceholderDefinition(
            "paciente.responsavel_nome", "Responsável legal", "Paciente", "Nome do responsável legal."
        ),
        PlaceholderDefinition(
            "profissional.nome", "Nome do profissional", "Profissional", "Nome completo do profissional emissor."
        ),
        PlaceholderDefinition(
            "profissional.registro_profissional",
            "Registro profissional",
            "Profissional",
            "Número de registro cadastrado.",
        ),
        PlaceholderDefinition(
            "profissional.especialidade", "Especialidade", "Profissional", "Especialidade cadastrada."
        ),
        PlaceholderDefinition(
            "clinica.nome", "Nome da clínica", "Clínica", "Nome configurado para emissão de documentos."
        ),
        PlaceholderDefinition(
            "clinica.endereco", "Endereço da clínica", "Clínica", "Endereço configurado no ambiente."
        ),
        PlaceholderDefinition(
            "clinica.telefone", "Telefone da clínica", "Clínica", "Telefone configurado no ambiente."
        ),
        PlaceholderDefinition(
            "documento.data_emissao", "Data de emissão", "Documento", "Data atual no formato brasileiro."
        ),
        PlaceholderDefinition(
            "documento.local_emissao", "Local de emissão", "Documento", "Local informado no momento da geração."
        ),
        PlaceholderDefinition(
            "documento.numero",
            "Número do documento",
            "Documento",
            "Identificador único dentro do escopo do profissional.",
        ),
    )

    ALLOWED = {definition.key for definition in DEFINITIONS}

    @staticmethod
    def list_all() -> list[dict[str, str]]:
        return [
            {
                "key": definition.key,
                "token": "{{" + definition.key + "}}",
                "label": definition.label,
                "group": definition.group,
                "description": definition.description,
            }
            for definition in DocumentPlaceholderService.DEFINITIONS
        ]

    @staticmethod
    def extract(content: str) -> set[str]:
        return set(DocumentPlaceholderService.PATTERN.findall(content or ""))

    @staticmethod
    def validate_content(content: str) -> str:
        content = (content or "").strip()
        if not content:
            raise ValidationError("O conteúdo do template é obrigatório.")
        if len(content) > DocumentPlaceholderService.MAX_LENGTH:
            raise ValidationError(
                f"O conteúdo deve possuir no máximo {DocumentPlaceholderService.MAX_LENGTH} caracteres."
            )
        unknown = sorted(DocumentPlaceholderService.extract(content) - DocumentPlaceholderService.ALLOWED)
        if unknown:
            raise ValidationError("Marcadores não reconhecidos: " + ", ".join(f"{{{{{item}}}}}" for item in unknown))
        return content

    @staticmethod
    def _format_date(value: date | None) -> str:
        return value.strftime("%d/%m/%Y") if value else ""

    @staticmethod
    def build_context(*, patient, professional, document_number: str, local_emissao: str = "") -> dict[str, str]:
        today = timezone.localdate()
        return {
            "paciente.nome": patient.display_name,
            "paciente.nome_completo": patient.full_name,
            "paciente.nome_social": patient.social_name or "",
            "paciente.cpf": patient.formatted_cpf,
            "paciente.data_nascimento": DocumentPlaceholderService._format_date(patient.birth_date),
            "paciente.idade": str(patient.age) if patient.age is not None else "",
            "paciente.responsavel_nome": patient.guardian_name or "",
            "profissional.nome": professional.full_name,
            "profissional.registro_profissional": professional.crp_number or "",
            "profissional.especialidade": professional.specialty or "",
            "clinica.nome": getattr(settings, "DOCUMENT_CLINIC_NAME", "Elo Terapêutico"),
            "clinica.endereco": getattr(settings, "DOCUMENT_CLINIC_ADDRESS", ""),
            "clinica.telefone": getattr(settings, "DOCUMENT_CLINIC_PHONE", ""),
            "documento.data_emissao": DocumentPlaceholderService._format_date(today),
            "documento.local_emissao": local_emissao.strip(),
            "documento.numero": document_number,
        }

    @staticmethod
    def _replace(content: str, context: dict[str, Any]) -> str:
        DocumentPlaceholderService.validate_content(content)

        def replace(match: re.Match[str]) -> str:
            key = match.group(1)
            return str(context.get(key, ""))

        return DocumentPlaceholderService.PATTERN.sub(replace, content)

    @staticmethod
    def render(content: str, context: dict[str, Any]) -> str:
        text = DocumentPlaceholderService._replace(content, context)
        escaped = html.escape(text, quote=True)
        lines = escaped.splitlines()
        rendered: list[str] = []
        list_open = False

        def close_list() -> None:
            nonlocal list_open
            if list_open:
                rendered.append("</ul>")
                list_open = False

        for raw_line in lines:
            line = raw_line.strip()
            if line == "[[QUEBRA_DE_PAGINA]]":
                close_list()
                rendered.append('<div class="page-break"></div>')
                continue
            if line.startswith("### "):
                close_list()
                rendered.append(f"<h3>{line[4:]}</h3>")
                continue
            if line.startswith("## "):
                close_list()
                rendered.append(f"<h2>{line[3:]}</h2>")
                continue
            if line.startswith("# "):
                close_list()
                rendered.append(f"<h1>{line[2:]}</h1>")
                continue
            if line.startswith(("- ", "* ")):
                if not list_open:
                    rendered.append("<ul>")
                    list_open = True
                rendered.append(f"<li>{line[2:]}</li>")
                continue
            close_list()
            if not line:
                rendered.append("<p>&nbsp;</p>")
            else:
                rendered.append(f"<p>{line}</p>")

        close_list()
        output = "\n".join(rendered)
        output = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", output)
        output = re.sub(r"(?<!\*)\*(.+?)\*(?!\*)", r"<em>\1</em>", output)
        return output

    @staticmethod
    def sample_context() -> dict[str, str]:
        return {
            "paciente.nome": "Nome do paciente",
            "paciente.nome_completo": "Nome completo do paciente",
            "paciente.nome_social": "",
            "paciente.cpf": "000.000.000-00",
            "paciente.data_nascimento": "01/01/2000",
            "paciente.idade": "26",
            "paciente.responsavel_nome": "Nome do responsável",
            "profissional.nome": "Nome do profissional",
            "profissional.registro_profissional": "00/000000",
            "profissional.especialidade": "Especialidade",
            "clinica.nome": getattr(settings, "DOCUMENT_CLINIC_NAME", "Elo Terapêutico"),
            "clinica.endereco": getattr(settings, "DOCUMENT_CLINIC_ADDRESS", ""),
            "clinica.telefone": getattr(settings, "DOCUMENT_CLINIC_PHONE", ""),
            "documento.data_emissao": DocumentPlaceholderService._format_date(timezone.localdate()),
            "documento.local_emissao": "Cidade/UF",
            "documento.numero": "DOC-AAAA-000000",
        }


class DocumentTemplateService:
    """Operações de domínio para templates de documentos."""

    @staticmethod
    def ensure_access(*, actor, template: DocumentTemplate) -> None:
        if template.status != DocumentTemplate.Status.ACTIVE:
            raise DocumentDomainError("O template selecionado não está ativo.")
        if template.is_library_template:
            raise DocumentDomainError("Importe o template da biblioteca antes de utilizá-lo.")
        if template.owner_id != actor.id:
            raise DocumentDomainError("Template não autorizado.")

    @staticmethod
    def ensure_private_ownership(*, actor, template: DocumentTemplate) -> None:
        if template.is_library_template or template.owner_id != actor.id:
            raise DocumentDomainError("Template não autorizado.")

    @staticmethod
    def archive(*, actor, template: DocumentTemplate) -> DocumentTemplate:
        DocumentTemplateService.ensure_private_ownership(actor=actor, template=template)
        template.archive()
        return template

    @staticmethod
    def activate(*, actor, template: DocumentTemplate) -> DocumentTemplate:
        DocumentTemplateService.ensure_private_ownership(actor=actor, template=template)
        template.status = DocumentTemplate.Status.ACTIVE
        template.archived_at = None
        template.updated_by = actor
        template.save(update_fields=["status", "archived_at", "updated_by", "updated_at"])
        return template

    @staticmethod
    def deactivate(*, actor, template: DocumentTemplate) -> DocumentTemplate:
        DocumentTemplateService.ensure_private_ownership(actor=actor, template=template)
        template.status = DocumentTemplate.Status.INACTIVE
        template.updated_by = actor
        template.save(update_fields=["status", "updated_by", "updated_at"])
        return template

    @staticmethod
    def resolve_removal(*, actor, template: DocumentTemplate) -> tuple[str, DocumentTemplate]:
        DocumentTemplateService.ensure_private_ownership(actor=actor, template=template)
        if template.generated_documents.exists() or template.source_library_template_id:
            template.archive()
            return "archived", template
        return "deleted", template

    @staticmethod
    @transaction.atomic
    def import_from_library(*, actor, library_template: DocumentTemplate) -> tuple[DocumentTemplate, bool]:
        if not library_template.is_library_template or library_template.owner_id is not None:
            raise DocumentDomainError("Template de biblioteca inválido.")
        existing = DocumentTemplate.objects.imported_from(actor, library_template).first()
        if existing:
            return existing, False

        base_name = library_template.name
        name = base_name
        suffix = 2
        while DocumentTemplate.objects.active_named_for(actor, name).exists():
            name = f"{base_name} ({suffix})"
            suffix += 1

        template = DocumentTemplate.objects.create(
            owner=actor,
            source_library_template=library_template,
            name=name,
            description=library_template.description,
            category=library_template.category,
            document_type=library_template.document_type,
            specialty=library_template.specialty,
            content=library_template.content,
            header_content=library_template.header_content,
            footer_content=library_template.footer_content,
            include_professional_identification=library_template.include_professional_identification,
            include_clinic_identification=library_template.include_clinic_identification,
            requires_signature=library_template.requires_signature,
            status=DocumentTemplate.Status.ACTIVE,
            is_library_template=False,
            version=1,
            created_by=actor,
            updated_by=actor,
        )
        return template, True

    @staticmethod
    @transaction.atomic
    def duplicate(*, actor, template: DocumentTemplate) -> DocumentTemplate:
        DocumentTemplateService.ensure_access(actor=actor, template=template)
        base_name = f"Cópia de {template.name}"
        name = base_name
        suffix = 2
        while DocumentTemplate.objects.active_named_for(actor, name).exists():
            name = f"{base_name} ({suffix})"
            suffix += 1
        return DocumentTemplate.objects.create(
            owner=actor,
            source_library_template=template.source_library_template,
            name=name,
            description=template.description,
            category=template.category,
            document_type=template.document_type,
            specialty=template.specialty,
            content=template.content,
            header_content=template.header_content,
            footer_content=template.footer_content,
            include_professional_identification=template.include_professional_identification,
            include_clinic_identification=template.include_clinic_identification,
            requires_signature=template.requires_signature,
            status=DocumentTemplate.Status.ACTIVE,
            created_by=actor,
            updated_by=actor,
        )

    @staticmethod
    def preview(*, actor, template: DocumentTemplate, patient_id: int | None, local_emissao: str = "") -> dict:
        from apps.patients.models import Patient

        if not patient_id:
            context = DocumentPlaceholderService.sample_context()
        else:
            patient = Patient.objects.filter(
                pk=patient_id,
                therapist=actor,
                deleted_at__isnull=True,
            ).first()
            if not patient:
                raise DocumentDomainError("Paciente não autorizado.")
            context = DocumentPlaceholderService.build_context(
                patient=patient,
                professional=actor,
                document_number="PRÉVIA",
                local_emissao=local_emissao,
            )
        return {
            "title": template.name,
            "header_html": (
                DocumentPlaceholderService.render(template.header_content, context) if template.header_content else ""
            ),
            "content_html": DocumentPlaceholderService.render(template.content, context),
            "footer_html": (
                DocumentPlaceholderService.render(template.footer_content, context) if template.footer_content else ""
            ),
        }
