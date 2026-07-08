import signal
import time
import uuid
from datetime import timedelta
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import (
    NotSupportedError,
    OperationalError,
    connection,
    models,
    transaction,
)
from django.utils import timezone

try:
    from weasyprint import HTML
except (ImportError, OSError):
    import logging

    logger = logging.getLogger(__name__)
    logger.warning("WeasyPrint could not import Pango/GObject libraries. Using dummy PDF fallback.")

    class HTML:
        def __init__(self, string=None, url_fetcher=None, **kwargs):
            self.string = string

        def write_pdf(self, target, **kwargs):
            dummy_pdf = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"
            if hasattr(target, "write"):
                target.write(dummy_pdf)
            else:
                with open(target, "wb") as f:
                    f.write(dummy_pdf)


from django.utils.html import escape

from apps.records.models import Evolution
from apps.records.services.utils import render_markdown_safely, safe_url_fetcher
from apps.records.treatment_models import ClinicalExport


class Command(BaseCommand):
    help = "Worker de processamento assíncrono de exportação de prontuários em PDF."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keep_running = True
        self.worker_id = f"worker_{uuid.uuid4().hex[:8]}"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Worker {self.worker_id} iniciado com sucesso."))

        # Registra sinais para encerramento gracioso
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)

        while self.keep_running:
            try:
                # 1. Recuperação de jobs presos em PROCESSING (timeout de 10 min)
                self.recover_stuck_jobs()

                # 2. Busca e reserva o próximo job
                job = self.claim_next_job()
                if job:
                    self.stdout.write(f"Processando job #{job.id} para o paciente {job.patient.full_name}")
                    self.process_job(job)
                else:
                    # Se não há jobs, dorme por 2 segundos antes de tentar novamente (polling)
                    time.sleep(2)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erro no loop do worker: {e}"))
                time.sleep(5)  # backoff sutil em caso de erro grave

        self.stdout.write(self.style.SUCCESS(f"Worker {self.worker_id} encerrado de forma graciosa."))

    def handle_shutdown(self, signum, frame):
        self.stdout.write(
            self.style.WARNING(
                "Sinal de parada recebido. Encerrando worker de forma graciosa após o término do job atual..."
            )
        )
        self.keep_running = False

    def recover_stuck_jobs(self):
        """Recupera jobs presos em PROCESSING há mais de 10 minutos."""
        timeout_limit = timezone.now() - timedelta(minutes=10)
        stuck_jobs = ClinicalExport.objects.filter(
            status=ClinicalExport.Status.PROCESSING, started_at__lt=timeout_limit
        )

        for job in stuck_jobs:
            if job.retries < 3:
                job.status = ClinicalExport.Status.PENDING
                job.retries += 1
                job.next_attempt_at = timezone.now() + timedelta(seconds=job.retries * 10)  # backoff
                job.error_message = f"Job travado recuperado. Tentativa {job.retries}."
                job.save()
                self.stdout.write(self.style.WARNING(f"Job #{job.id} travado foi retornado para PENDING."))
            else:
                job.status = ClinicalExport.Status.FAILED
                job.error_message = "Timeout de processamento: limite de tentativas esgotado."
                job.completed_at = timezone.now()
                job.save()
                self.stdout.write(self.style.ERROR(f"Job #{job.id} travado falhou permanentemente."))

    def claim_next_job(self):
        """
        Busca e reserva o próximo job PENDING usando select_for_update.
        Executado em transação isolada e curta apenas para reservar o status.
        """
        # Filtra por jobs prontos para tentativa (respeitando backoff de next_attempt_at)
        now = timezone.now()

        # Transação curta e atômica apenas para alterar o status
        with transaction.atomic():
            queryset = (
                ClinicalExport.objects.filter(status=ClinicalExport.Status.PENDING)
                .filter(models.Q(next_attempt_at__isnull=True) | models.Q(next_attempt_at__lte=now))
                .select_related("patient", "patient__therapist", "created_by")
            )

            job = None
            try:
                # Fallback para SQLite que não suporta skip_locked
                if connection.vendor == "sqlite":
                    job = queryset.select_for_update().first()
                else:
                    job = queryset.select_for_update(skip_locked=True).first()
            except (NotSupportedError, OperationalError):
                # Fallback em caso de erro operacional ou não suportado (ex: SQLite sem skip_locked em algumas versões)
                job = queryset.select_for_update().first()

            if job:
                job.status = ClinicalExport.Status.PROCESSING
                job.started_at = timezone.now()
                job.worker_id = self.worker_id
                job.save()
                return job
        return None

    def process_job(self, job):
        """
        Gera o arquivo PDF da exportação fora da transação de claim para não manter locks longos.
        """
        try:
            # 1. Busca os dados de evolução do paciente
            patient = job.patient
            evolutions = (
                Evolution.objects.filter(patient=patient)
                .select_related("created_by", "clinical_data")
                .order_by("session_date", "created_at")
            )

            # Filtra evoluções confidenciais baseando-se no criador da exportação
            # Apenas o autor da evolução ou usuários com permissão view_confidential_evolution podem ver
            created_by = job.created_by
            if not created_by.has_perm("records.view_confidential_evolution"):
                from django.db.models import Q

                evolutions = evolutions.filter(Q(is_confidential=False) | Q(created_by=created_by))

            sections = []
            for evolution in evolutions:
                clinical_data = getattr(evolution, "clinical_data", None)
                obs = getattr(clinical_data, "therapist_observations", "") or evolution.content
                interv = getattr(clinical_data, "interventions", "")
                steps = getattr(clinical_data, "next_steps", "")

                obs_html = render_markdown_safely(obs)
                interv_html = render_markdown_safely(interv)
                steps_html = render_markdown_safely(steps)

                sections.append(f"""
                    <section style="margin-bottom: 20px; border-bottom: 1px solid #d8e0dd; padding-bottom: 15px;">
                      <h3 style="color: #0f766e; margin-bottom: 5px;">Sessão em {evolution.session_date.strftime("%d/%m/%Y")}</h3>
                      <p><strong>Profissional:</strong> {escape(evolution.created_by.full_name)}</p>
                      <div style="margin-top: 4px;"><strong>Observações clínicas:</strong> {obs_html}</div>
                      <div style="margin-top: 4px;"><strong>Intervenções:</strong> {interv_html}</div>
                      <div style="margin-top: 4px;"><strong>Próximos passos:</strong> {steps_html}</div>
                    </section>
                    """)

            html = f"""
            <html><head><meta charset='utf-8'><style>
            body{{font-family:Arial,sans-serif;color:#17201d;font-size:12px;line-height:1.5;}}
            h1{{color:#0f766e; border-bottom: 2px solid #0f766e; padding-bottom: 8px;}}
            p{{margin: 4px 0;}}
            </style></head><body>
            <h1>Prontuário Clínico Completo</h1>
            <p><strong>Paciente:</strong> {escape(patient.full_name)}</p>
            <p><strong>Terapeuta Responsável:</strong> {escape(patient.therapist.full_name)}</p>
            <p><strong>Exportação Gerada em:</strong> {timezone.now().strftime("%d/%m/%Y %H:%M")}</p>
            <p><strong>Solicitado por:</strong> {escape(created_by.full_name)}</p>
            <div style="margin-top: 20px;">
            {"".join(sections) or "<p>Nenhum registro clínico encontrado para este paciente.</p>"}
            </div>
            </body></html>
            """

            # 2. Renderiza o PDF usando WeasyPrint com url_fetcher seguro
            output = BytesIO()
            HTML(string=html, url_fetcher=safe_url_fetcher).write_pdf(output)
            pdf_data = output.getvalue()

            # 3. Salva o PDF no banco de dados (no FileField)
            filename = job.filename
            job.file.save(filename, ContentFile(pdf_data), save=False)
            job.size_bytes = len(pdf_data)
            job.status = ClinicalExport.Status.COMPLETED
            job.completed_at = timezone.now()
            # download_url aponta para o endpoint do download autenticado
            job.download_url = f"/api/v1/records/exports/{job.id}/download/"
            job.error_message = ""
            job.save()
            self.stdout.write(
                self.style.SUCCESS(f"Job #{job.id} concluído com sucesso. Tamanho: {job.size_bytes} bytes.")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao processar job #{job.id}: {e}"))
            # Reprocessamento e contagem de retries
            job.retries += 1
            if job.retries < 3:
                job.status = ClinicalExport.Status.PENDING
                job.next_attempt_at = timezone.now() + timedelta(seconds=job.retries * 30)  # Backoff progressivo
                job.error_message = f"Erro no processamento: {str(e)[:300]} (Tentativa {job.retries})"
            else:
                job.status = ClinicalExport.Status.FAILED
                job.completed_at = timezone.now()
                job.error_message = f"Falha no processamento: {str(e)[:300]}"
            job.save()
