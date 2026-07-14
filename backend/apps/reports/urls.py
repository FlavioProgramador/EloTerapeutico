from django.urls import path

from apps.reports.views import (
    AppointmentsReportView,
    FinancialReportView,
    OnlineSchedulingReportView,
    PatientsReportView,
    ReportExportView,
)

urlpatterns = [
    path("appointments/", AppointmentsReportView.as_view(), name="reports-appointments"),
    path("patients/", PatientsReportView.as_view(), name="reports-patients"),
    path("financial/", FinancialReportView.as_view(), name="reports-financial"),
    path("online-scheduling/", OnlineSchedulingReportView.as_view(), name="reports-online-scheduling"),
    path("export/", ReportExportView.as_view(), name="reports-export"),
]
