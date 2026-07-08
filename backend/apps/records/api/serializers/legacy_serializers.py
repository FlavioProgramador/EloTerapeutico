"""
apps/records/serializers.py
Serializers do módulo de Prontuários Eletrônicos.

Estrutura:
- AnamnesisSerializer: leitura/escrita completa da anamnese
- EvolutionListSerializer: listagem resumida (sem conteúdo clínico)
- EvolutionDetailSerializer: detalhe completo (conteúdo já descriptografado pelo field)
- EvolutionCreateSerializer: criação com validação de duplicata por data
- EvolutionUpdateSerializer: edição parcial (bloqueada após 48h)
- EvolutionAddendumSerializer: criação de aditivos

NOTA DE SEGURANÇA: Os campos EncryptedTextField retornam o valor já
descriptografado pelo método from_db_value() do campo. Portanto, os
serializers simplesmente lêem e escrevem texto puro — a criptografia
é transparente.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.patients.services.access_control import can_access_patient
from apps.records.models import Anamnesis, Evolution, EvolutionAddendum

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# Serializer auxiliar de usuário (somente leitura)
# ─────────────────────────────────────────────────────────────────────────────


class UserSummarySerializer(serializers.ModelSerializer):
    """Representação mínima e somente-leitura de um usuário (para campos created_by)."""

    class Meta:
        model = User
        fields = ("id", "full_name", "email")
        read_only_fields = ("id", "full_name", "email")


# ─────────────────────────────────────────────────────────────────────────────
# Anamnesis
# ─────────────────────────────────────────────────────────────────────────────


class AnamnesisSerializer(serializers.ModelSerializer):
    """
    Serializer completo da Anamnese.

    Usado tanto para leitura quanto para criação e atualização.
    O campo 'created_by' é somente-leitura e preenchido automaticamente
    pela view com o usuário autenticado.
    """

    created_by = UserSummarySerializer(read_only=True)
    # Campo auxiliar write-only para receber apenas o ID do patient na criação
    patient_id = serializers.PrimaryKeyRelatedField(
        source="patient",
        queryset=__import__("apps.patients.models", fromlist=["Patient"]).Patient.objects.all(),
        write_only=True,
        label="ID do Paciente",
    )

    class Meta:
        model = Anamnesis
        fields = (
            "id",
            "patient_id",
            "chief_complaint",
            "history",
            "medications",
            "family_history",
            "observations",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at")

    def validate(self, attrs):
        """
        Valida que a anamnese não está sendo criada para um paciente
        sem que o usuário tenha permissão de acesso.
        """
        request = self.context.get("request")
        patient = attrs.get("patient")
        if request and patient and not can_access_patient(request.user, patient):
            raise serializers.ValidationError(
                {"patient_id": "Você não tem permissão para criar anamnese para este paciente."}
            )
        return attrs


# ─────────────────────────────────────────────────────────────────────────────
# Evolution – Listagem (resumida, sem conteúdo clínico)
# ─────────────────────────────────────────────────────────────────────────────


class EvolutionListSerializer(serializers.ModelSerializer):
    """
    Serializer para listagem de evoluções.

    Omite o campo 'content' (conteúdo clínico) intencionalmente:
    - Evita descriptografia em massa para longas listas
    - Expõe apenas metadados suficientes para seleção pelo frontend
    """

    created_by_name = serializers.CharField(
        source="created_by.full_name",
        read_only=True,
        label="Nome do terapeuta",
    )
    is_editable = serializers.SerializerMethodField(
        help_text="True se a evolução ainda pode ser editada (criada há < 48h e não bloqueada).",
    )
    addenda_count = serializers.IntegerField(
        source="addenda.count",
        read_only=True,
        label="Quantidade de aditivos",
    )

    class Meta:
        model = Evolution
        fields = (
            "id",
            "patient",
            "session_date",
            "cid10",
            "is_locked",
            "locked_at",
            "is_editable",
            "addenda_count",
            "created_by",
            "created_by_name",
            "created_at",
        )
        read_only_fields = fields

    def get_is_editable(self, obj: Evolution) -> bool:
        return obj.can_be_edited()


# ─────────────────────────────────────────────────────────────────────────────
# Evolution – Detalhe (com conteúdo clínico descriptografado)
# ─────────────────────────────────────────────────────────────────────────────


class EvolutionDetailSerializer(serializers.ModelSerializer):
    """
    Serializer de detalhe da evolução.

    Inclui o campo 'content' (criptografado em banco, descriptografado
    automaticamente pelo EncryptedTextField.from_db_value antes de chegar aqui).

    O campo 'is_editable' indica ao frontend se o botão de edição deve
    ser exibido para este usuário.
    """

    created_by = UserSummarySerializer(read_only=True)
    is_editable = serializers.SerializerMethodField(
        help_text="True se a evolução ainda pode ser editada pelo usuário atual.",
    )
    addenda = serializers.SerializerMethodField(
        help_text="Lista de aditivos vinculados a esta evolução.",
    )

    class Meta:
        model = Evolution
        fields = (
            "id",
            "patient",
            "appointment",
            "content",  # já descriptografado pelo field
            "cid10",
            "session_date",
            "is_locked",
            "locked_at",
            "is_editable",
            "addenda",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields  # Detalhe é somente-leitura; use Update para editar

    def get_is_editable(self, obj: Evolution) -> bool:
        """
        Verifica editabilidade considerando também o usuário logado:
        somente o criador pode editar.
        """
        request = self.context.get("request")
        if request is None:
            return False
        if not obj.can_be_edited():
            return False
        return obj.created_by_id == request.user.id

    def get_addenda(self, obj: Evolution) -> list:
        """Retorna os aditivos da evolução já serializados."""
        qs = obj.addenda.select_related("created_by").order_by("created_at")
        return EvolutionAddendumSerializer(qs, many=True, context=self.context).data


# ─────────────────────────────────────────────────────────────────────────────
# Evolution – Criação
# ─────────────────────────────────────────────────────────────────────────────


class EvolutionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de uma nova evolução.

    Validações:
    1. Duplicata por data: um paciente não pode ter duas evoluções na mesma data
       criadas pelo mesmo terapeuta.
    2. Permissão de paciente: só o terapeuta responsável pode criar evoluções.
    """

    class Meta:
        model = Evolution
        fields = (
            "id",
            "patient",
            "appointment",
            "content",
            "cid10",
            "session_date",
        )
        read_only_fields = ("id",)

    def validate(self, attrs):
        request = self.context.get("request")
        patient = attrs.get("patient")
        session_date = attrs.get("session_date")

        # Verificação 1: o usuário tem acesso ao paciente
        if request and patient and not can_access_patient(request.user, patient):
            raise serializers.ValidationError(
                {"patient": ("Você não tem permissão para registrar evoluções para este paciente.")}
            )

        # Verificação 2: duplicata por data
        if patient and session_date:
            duplicata_existe = Evolution.objects.filter(
                patient=patient,
                session_date=session_date,
                created_by=request.user if request else None,
            ).exists()
            if duplicata_existe:
                raise serializers.ValidationError(
                    {
                        "session_date": (
                            f"Já existe uma evolução para este paciente na data "
                            f"{session_date:%d/%m/%Y}. "
                            "Para complementar, use a ação de aditivo."
                        )
                    }
                )

        return attrs


# ─────────────────────────────────────────────────────────────────────────────
# Evolution – Atualização parcial
# ─────────────────────────────────────────────────────────────────────────────


class EvolutionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para edição parcial de uma evolução ainda não bloqueada.

    Permite atualizar apenas content, cid10 e session_date.
    Não é possível reatribuir paciente ou terapeuta via este serializer.
    """

    class Meta:
        model = Evolution
        fields = ("content", "cid10", "session_date")

    def validate(self, attrs):
        """Garante que a evolução ainda pode ser editada antes de aceitar dados."""
        instance = self.instance
        if instance and not instance.can_be_edited():
            raise serializers.ValidationError(
                "Esta evolução está bloqueada e não pode ser editada. "
                "Utilize a ação de aditivo para complementar o registro."
            )
        return attrs


# ─────────────────────────────────────────────────────────────────────────────
# EvolutionAddendum
# ─────────────────────────────────────────────────────────────────────────────


class EvolutionAddendumSerializer(serializers.ModelSerializer):
    """
    Serializer de Aditivo de Evolução.

    Leitura e criação. Aditivos são imutáveis após criação.
    O campo 'content' é descriptografado automaticamente pelo field.
    """

    created_by = UserSummarySerializer(read_only=True)

    class Meta:
        model = EvolutionAddendum
        fields = (
            "id",
            "evolution",
            "reason",
            "content",  # descriptografado pelo EncryptedTextField
            "created_by",
            "created_at",
        )
        read_only_fields = ("id", "evolution", "created_by", "created_at")

    def validate(self, attrs):
        """
        Verifica que a evolução-alvo está bloqueada.
        Aditivos só podem ser criados para evoluções bloqueadas.
        """
        evolution = self.context.get("evolution")
        if evolution and not evolution.is_locked:
            raise serializers.ValidationError(
                {
                    "evolution": (
                        "Aditivos só podem ser criados para evoluções bloqueadas. "
                        "Se a evolução ainda pode ser editada, use a edição direta."
                    )
                }
            )
        return attrs
