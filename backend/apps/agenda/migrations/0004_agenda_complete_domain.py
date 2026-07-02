# Generated manually for the complete Agenda domain.

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):
    dependencies = [
        ("agenda", "0003_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Room",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=120, verbose_name="Nome")),
                (
                    "location",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="Localização"
                    ),
                ),
                (
                    "capacity",
                    models.PositiveSmallIntegerField(
                        default=1, verbose_name="Capacidade"
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Ativa"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "therapist",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agenda_rooms",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Responsável",
                    ),
                ),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.AddConstraint(
            model_name="room",
            constraint=models.UniqueConstraint(
                fields=("therapist", "name"), name="uniq_room_owner_name"
            ),
        ),
        migrations.CreateModel(
            name="AppointmentRecurrence",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "frequency",
                    models.CharField(
                        choices=[
                            ("weekly", "Semanal"),
                            ("biweekly", "Quinzenal"),
                            ("monthly", "Mensal"),
                            ("custom", "Personalizada"),
                        ],
                        max_length=20,
                    ),
                ),
                ("interval", models.PositiveSmallIntegerField(default=1)),
                ("weekdays", models.JSONField(blank=True, default=list)),
                ("starts_on", models.DateField()),
                ("ends_on", models.DateField(blank=True, null=True)),
                (
                    "max_occurrences",
                    models.PositiveIntegerField(blank=True, null=True),
                ),
                ("start_time", models.TimeField()),
                ("duration_minutes", models.PositiveIntegerField(default=50)),
                (
                    "timezone_name",
                    models.CharField(
                        default="America/Sao_Paulo", max_length=64
                    ),
                ),
                (
                    "modality",
                    models.CharField(default="in_person", max_length=20),
                ),
                (
                    "appointment_type",
                    models.CharField(default="psychotherapy", max_length=30),
                ),
                (
                    "session_value",
                    models.DecimalField(
                        decimal_places=2, default=0, max_digits=10
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Ativa"),
                            ("paused", "Pausada"),
                            ("ended", "Encerrada"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_appointment_recurrences",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="appointment_recurrences",
                        to="patients.patient",
                    ),
                ),
                (
                    "room",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="recurrences",
                        to="agenda.room",
                    ),
                ),
                (
                    "therapist",
                    models.ForeignKey(
                        limit_choices_to={"role": "therapist"},
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="appointment_recurrences",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["therapist", "status"],
                        name="rec_owner_status_idx",
                    ),
                    models.Index(
                        fields=["patient", "status"],
                        name="rec_patient_status_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="PatientPackage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=160)),
                ("description", models.TextField(blank=True)),
                ("sessions_contracted", models.PositiveIntegerField()),
                ("sessions_used", models.PositiveIntegerField(default=0)),
                (
                    "total_value",
                    models.DecimalField(
                        decimal_places=2, default=0, max_digits=10
                    ),
                ),
                ("valid_from", models.DateField(default=timezone.localdate)),
                ("valid_until", models.DateField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Ativo"),
                            ("paused", "Pausado"),
                            ("completed", "Concluído"),
                            ("expired", "Expirado"),
                            ("cancelled", "Cancelado"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("generate_charge", models.BooleanField(default=False)),
                ("send_charge", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_session_packages",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="session_packages",
                        to="patients.patient",
                    ),
                ),
                (
                    "therapist",
                    models.ForeignKey(
                        limit_choices_to={"role": "therapist"},
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="session_packages",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["therapist", "status"],
                        name="pkg_owner_status_idx",
                    ),
                    models.Index(
                        fields=["patient", "status"],
                        name="pkg_patient_status_idx",
                    ),
                ],
            },
        ),
        migrations.AlterField(
            model_name="appointment",
            name="status",
            field=models.CharField(
                choices=[
                    ("scheduled", "Agendada"),
                    ("confirmed", "Confirmada"),
                    ("completed", "Realizada"),
                    ("missed", "Faltou"),
                    ("cancelled", "Cancelada"),
                    ("rescheduled", "Reagendada"),
                ],
                db_index=True,
                default="scheduled",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="appointment",
            name="session_value",
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AddField(
            model_name="appointment",
            name="appointment_type",
            field=models.CharField(
                choices=[
                    ("assessment", "Avaliação"),
                    ("psychotherapy", "Psicoterapia"),
                    ("follow_up", "Retorno"),
                    ("guidance", "Orientação"),
                    ("group", "Sessão em grupo"),
                    ("other", "Outro"),
                ],
                default="psychotherapy",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_appointments",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="modality",
            field=models.CharField(
                choices=[
                    ("in_person", "Presencial"),
                    ("online", "Online"),
                    ("hybrid", "Híbrida"),
                ],
                default="in_person",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="origin",
            field=models.CharField(
                choices=[
                    ("manual", "Manual"),
                    ("recurrence", "Recorrência"),
                    ("package", "Pacote"),
                    ("reschedule", "Remarcação"),
                ],
                default="manual",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="package",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="appointments",
                to="agenda.patientpackage",
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="participants",
            field=models.ManyToManyField(
                blank=True,
                related_name="group_appointments",
                to="patients.patient",
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="recurrence",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="appointments",
                to="agenda.appointmentrecurrence",
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="room",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="appointments",
                to="agenda.room",
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="updated_appointments",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["room", "start_time"], name="appt_room_start_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["recurrence", "start_time"],
                name="appt_rec_start_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="appointment",
            constraint=models.CheckConstraint(
                condition=models.Q(("end_time__gt", models.F("start_time"))),
                name="appt_end_after_start",
            ),
        ),
        migrations.AddConstraint(
            model_name="appointment",
            constraint=models.CheckConstraint(
                condition=models.Q(("session_value__gte", 0)),
                name="appt_value_non_negative",
            ),
        ),
        migrations.CreateModel(
            name="ScheduleBlock",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("start_time", models.DateTimeField()),
                ("end_time", models.DateTimeField()),
                (
                    "reason",
                    models.CharField(
                        choices=[
                            ("lunch", "Almoço"),
                            ("meeting", "Reunião"),
                            ("vacation", "Férias"),
                            ("external", "Atendimento externo"),
                            ("appointment", "Compromisso"),
                            ("other", "Outro"),
                        ],
                        default="other",
                        max_length=20,
                    ),
                ),
                ("notes", models.CharField(blank=True, max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("recurrence_rule", models.CharField(blank=True, max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_schedule_blocks",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "parent_block",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="occurrences",
                        to="agenda.scheduleblock",
                    ),
                ),
                (
                    "therapist",
                    models.ForeignKey(
                        limit_choices_to={"role": "therapist"},
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="schedule_blocks",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["start_time"],
                "indexes": [
                    models.Index(
                        fields=["therapist", "start_time"],
                        name="block_owner_start_idx",
                    )
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="scheduleblock",
            constraint=models.CheckConstraint(
                condition=models.Q(("end_time__gt", models.F("start_time"))),
                name="block_end_after_start",
            ),
        ),
        migrations.CreateModel(
            name="PackageSession",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("scheduled_for", models.DateTimeField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("scheduled", "Agendada"),
                            ("confirmed", "Confirmada"),
                            ("completed", "Realizada"),
                            ("missed", "Falta"),
                            ("cancelled", "Cancelada"),
                            ("rescheduled", "Remarcada"),
                        ],
                        default="scheduled",
                        max_length=20,
                    ),
                ),
                ("consumed", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "appointment",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="package_session",
                        to="agenda.appointment",
                    ),
                ),
                (
                    "package",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="package_sessions",
                        to="agenda.patientpackage",
                    ),
                ),
            ],
            options={"ordering": ["scheduled_for"]},
        ),
        migrations.AddConstraint(
            model_name="packagesession",
            constraint=models.UniqueConstraint(
                fields=("package", "scheduled_for"),
                name="uniq_pkg_session_datetime",
            ),
        ),
        migrations.CreateModel(
            name="TelemedicineRoom",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "patient_token",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, unique=True
                    ),
                ),
                (
                    "professional_token",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, unique=True
                    ),
                ),
                ("expires_at", models.DateTimeField()),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendente"),
                            ("available", "Disponível"),
                            ("in_progress", "Em andamento"),
                            ("finished", "Finalizada"),
                            ("cancelled", "Cancelada"),
                            ("expired", "Expirada"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "appointment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="telemedicine_room",
                        to="agenda.appointment",
                    ),
                ),
            ],
            options={"ordering": ["appointment__start_time"]},
        ),
        migrations.CreateModel(
            name="AppointmentReminder",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "channel",
                    models.CharField(
                        choices=[
                            ("whatsapp", "WhatsApp"),
                            ("email", "E-mail"),
                        ],
                        default="whatsapp",
                        max_length=20,
                    ),
                ),
                ("scheduled_for", models.DateTimeField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendente"),
                            ("sent", "Enviado"),
                            ("failed", "Falhou"),
                            ("cancelled", "Cancelado"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                (
                    "recipient_masked",
                    models.CharField(blank=True, max_length=32),
                ),
                (
                    "error_message",
                    models.CharField(blank=True, max_length=255),
                ),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "appointment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reminders",
                        to="agenda.appointment",
                    ),
                ),
            ],
            options={
                "ordering": ["scheduled_for"],
                "indexes": [
                    models.Index(
                        fields=["status", "scheduled_for"],
                        name="reminder_status_time_idx",
                    )
                ],
            },
        ),
    ]
