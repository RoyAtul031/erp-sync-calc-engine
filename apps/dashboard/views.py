from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from apps.data_warehouse.models import Facility, FacilityUtilityRecord, WorkforceMetricRecord
from apps.erp_connector.models import ERPConnection, SyncBatch
from apps.calculation_engine.models import (
    ComplianceFramework,
    EmissionFactor,
    CalculationMethodology,
    FormulaRule,
    CalculationRun,
    CalculatedRecord,
)


def ensure_demo_users():
    """Ensure standard enterprise role accounts exist in the database."""
    demo_accounts = [
        {"username": "cso@enterprise.com", "first_name": "Elena", "last_name": "Vance", "role": "Chief Sustainability Officer"},
        {"username": "analyst@enterprise.com", "first_name": "Marcus", "last_name": "Chen", "role": "Senior ESG Analyst"},
        {"username": "auditor@deloitte-audit.com", "first_name": "Sarah", "last_name": "Jenkins", "role": "Lead Statutory Auditor"},
    ]
    for acc in demo_accounts:
        if not User.objects.filter(username=acc["username"]).exists():
            u = User.objects.create_user(
                username=acc["username"],
                email=acc["username"],
                password="Enterprise2026!",
                first_name=acc["first_name"],
                last_name=acc["last_name"]
            )


class LandingLoginView(View):
    template_name = "dashboard/landing.html"

    def get(self, request):
        ensure_demo_users()
        latest_run = CalculationRun.objects.filter(status="COMPLETED").first()
        connections = ERPConnection.objects.all()
        facilities = Facility.objects.all()

        context = {
            "latest_run": latest_run,
            "connections_count": connections.count(),
            "facilities_count": facilities.count(),
            "total_ghg": latest_run.total_ghg_emissions_tco2e if latest_run else 672.7,
            "diversity_pct": latest_run.avg_gender_diversity_pct if latest_run else 43.0,
            "ltifr": latest_run.avg_ltifr if latest_run else 4.06,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        # Check demo quick-login or real credentials
        if not email:
            email = "cso@enterprise.com"
        if not password:
            password = "Enterprise2026!"

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect("/dashboard/")
        else:
            # Fallback auto-provision demo user for instant seamless experience
            user, _ = User.objects.get_or_create(username=email, defaults={"email": email})
            user.set_password(password)
            user.save()
            login(request, user)
            return redirect("/dashboard/")


class LogoutUserView(View):
    def get(self, request):
        logout(request)
        return redirect("/")


class DashboardView(TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Facilities & Summary
        facilities = Facility.objects.all()
        connections = ERPConnection.objects.all()
        latest_run = CalculationRun.objects.filter(status="COMPLETED").first()
        recent_batches = SyncBatch.objects.all().order_by("-started_at")[:8]
        frameworks = ComplianceFramework.objects.all()
        methodologies = CalculationMethodology.objects.all().prefetch_related("formula_rules")
        active_methodology = methodologies.filter(is_active=True).first() or methodologies.first()
        calculated_records = CalculatedRecord.objects.all().select_related("facility", "utility_record").order_by("-created_at")[:25]

        context.update({
            "facilities": facilities,
            "connections": connections,
            "latest_run": latest_run,
            "recent_batches": recent_batches,
            "frameworks": frameworks,
            "methodologies": methodologies,
            "active_methodology": active_methodology,
            "calculated_records": calculated_records,
            "total_utility_records": FacilityUtilityRecord.objects.count(),
            "total_workforce_records": WorkforceMetricRecord.objects.count(),
            "user": self.request.user,
        })
        return context
