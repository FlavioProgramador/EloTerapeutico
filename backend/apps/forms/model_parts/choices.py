"""Choices compartilhados do módulo de formulários."""

from django.db import models


class FormCategory(models.TextChoices):
    ANAMNESIS = "anamnese", "Anamnese"
    ASSESSMENT = "avaliacao", "Avaliação"
    EVOLUTION = "evolucao", "Evolução"
    SCALES = "escalas", "Escalas"
    QUESTIONNAIRE = "questionario", "Questionário"
    OTHER = "outro", "Outro"


class FieldType(models.TextChoices):
    SHORT_TEXT = "short_text", "Texto curto"
    LONG_TEXT = "long_text", "Texto longo"
    NUMBER = "number", "Número"
    DATE = "date", "Data"
    SELECT = "select", "Seleção"
    RADIO = "radio", "Múltipla escolha"
    CHECKBOX = "checkbox", "Caixas de seleção"
    SCALE = "scale", "Escala"
    HEADING = "heading", "Título"
