import uuid
from django.db import models


class Facility(models.Model):
    """
    Physical operational site / plant / office reporting ESG utility and workforce data.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=64, unique=True, help_text="e.g. SAP Plant Code 'PLANT-TX-01' or 'HQ-MUNICH'")
    name = models.CharField(max_length=255)
    facility_type = models.CharField(
        max_length=64,
        choices=[
            ("MANUFACTURING", "Manufacturing & Assembly"),
            ("DATA_CENTER", "Data Center / R&D"),
            ("OFFICE", "Corporate Headquarters / Office"),
            ("WAREHOUSE", "Warehouse & Logistics Hub"),
            ("RETAIL", "Retail Branch / Store"),
        ],
        default="MANUFACTURING"
    )
    country = models.CharField(max_length=64, default="USA")
    region_state = models.CharField(max_length=64, blank=True, help_text="e.g. Texas, Bavaria, Karnataka")
    grid_subregion = models.CharField(
        max_length=64,
        default="US_ERCOT",
        help_text="Grid subregion for Scope 2 emission factor matching (e.g. US_ERCOT, US_CAMX, DE_GRID, IN_SOUTHERN, UK_GRID)"
    )
    gross_area_sqft = models.DecimalField(max_digits=12, decimal_places=2, default=150000.0)
    baseline_headcount = models.PositiveIntegerField(default=500)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Facility"
        verbose_name_plural = "Facilities"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name} ({self.country})"


class FacilityUtilityRecord(models.Model):
    """
    Normalized utility consumption ingested from ERP (SAP Material Documents, Utility Invoices, IoT Meters).
    """
    UTILITY_TYPES = [
        ("DIESEL_GENERATOR", "Diesel (Stationary Generator / Backup)"),
        ("DIESEL_FLEET", "Diesel (Mobile Fleet / Logistics)"),
        ("NATURAL_GAS", "Natural Gas (Heating / Boilers)"),
        ("ELECTRICITY_PURCHASED", "Purchased Grid Electricity"),
        ("REFRIGERANT_R410A", "Refrigerant Refill (R-410A Fugitive)"),
        ("WATER_CONSUMPTION", "Municipal Water Supply"),
    ]

    SCOPE_CATEGORIES = [
        ("SCOPE_1", "Scope 1 (Direct Emissions)"),
        ("SCOPE_2_LOCATION", "Scope 2 (Indirect - Location-based Grid)"),
        ("SCOPE_2_MARKET", "Scope 2 (Indirect - Market-based / PPA / REC)"),
        ("WATER", "Water Consumption (m³)"),
    ]

    UNIT_CHOICES = [
        ("KWH", "Kilowatt Hours (kWh)"),
        ("MWH", "Megawatt Hours (MWh)"),
        ("LITERS", "Liters (L)"),
        ("GALLONS", "Gallons (gal)"),
        ("M3", "Cubic Meters (m³)"),
        ("THERMS", "Therms"),
        ("KG", "Kilograms (kg)"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="utility_records")
    utility_type = models.CharField(max_length=64, choices=UTILITY_TYPES)
    scope_category = models.CharField(max_length=32, choices=SCOPE_CATEGORIES, default="SCOPE_1")
    
    start_date = models.DateField(help_text="Billing or metering period start")
    end_date = models.DateField(help_text="Billing or metering period end")

    consumption_value = models.DecimalField(max_digits=16, decimal_places=4, help_text="Raw quantity measured")
    consumption_unit = models.CharField(max_length=16, choices=UNIT_CHOICES)

    # ERP Metadata & Lineage
    source_erp_system = models.CharField(max_length=64, default="SAP_S4HANA")
    sap_document_number = models.CharField(max_length=128, blank=True, db_index=True, help_text="SAP Material Document / Invoice Reference")
    meter_identifier = models.CharField(max_length=128, blank=True, help_text="Hardware / Smart Meter serial number")
    is_renewable_backed = models.BooleanField(default=False, help_text="Backed by Renewable Energy Certificates (REC/PPA)")

    # Data Quality & Integrity
    data_quality_score = models.CharField(
        max_length=32,
        choices=[("METER_READING", "Direct Meter / Sensor (High)"), ("UTILITY_INVOICE", "Utility Invoice (Medium-High)"), ("ESTIMATED", "Estimated / Accrual (Medium)")],
        default="UTILITY_INVOICE"
    )
    external_sync_id = models.CharField(max_length=128, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Facility Utility Record"
        verbose_name_plural = "Facility Utility Records"
        ordering = ["-start_date", "facility"]
        indexes = [
            models.Index(fields=["facility", "utility_type", "start_date"]),
            models.Index(fields=["sap_document_number"]),
        ]

    def __str__(self):
        return f"{self.facility.code} | {self.utility_type}: {self.consumption_value} {self.consumption_unit} ({self.start_date})"


class WorkforceMetricRecord(models.Model):
    """
    Normalized social / HR ESG metrics ingested from Workday / SuccessFactors.
    Used for Social KPIs (Gender diversity %, LTIFR, Safety incident rate, Energy intensity per FTE).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="workforce_records")
    
    period_start = models.DateField()
    period_end = models.DateField()

    total_headcount = models.PositiveIntegerField(help_text="Active Full-Time Equivalents (FTE)")
    female_headcount = models.PositiveIntegerField(default=0)
    male_headcount = models.PositiveIntegerField(default=0)
    non_binary_headcount = models.PositiveIntegerField(default=0)

    # Safety Metrics (for LTIFR calculation)
    lost_time_injuries = models.PositiveIntegerField(default=0, help_text="Number of lost-time injuries (LTI)")
    recordable_incidents = models.PositiveIntegerField(default=0, help_text="OSHA / statutory recordable incidents")
    total_hours_worked = models.DecimalField(max_digits=14, decimal_places=2, default=160000.0, help_text="Total operational employee exposure hours")
    
    training_hours_total = models.DecimalField(max_digits=12, decimal_places=2, default=1200.0, help_text="Total ESG and compliance training hours delivered")
    employee_turnover_count = models.PositiveIntegerField(default=15)

    source_hr_system = models.CharField(max_length=64, default="WORKDAY_HCM")
    external_sync_id = models.CharField(max_length=128, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Workforce Metric Record"
        verbose_name_plural = "Workforce Metric Records"
        ordering = ["-period_start", "facility"]

    def __str__(self):
        return f"{self.facility.code} HR ({self.period_start} to {self.period_end}) - Headcount: {self.total_headcount}"
