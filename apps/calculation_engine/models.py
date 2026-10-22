import uuid
from django.db import models
from apps.data_warehouse.models import Facility, FacilityUtilityRecord, WorkforceMetricRecord


class ComplianceFramework(models.Model):
    """
    Standard ESG reporting framework (e.g. GHG Protocol, US EPA, UK DEFRA, India BRSR, EU CSRD).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=64, unique=True, help_text="e.g. GHG_PROTOCOL, US_EPA, UK_DEFRA, INDIA_BRSR, EU_CSRD")
    name = models.CharField(max_length=255)
    jurisdiction = models.CharField(max_length=128, default="Global")
    version_tag = models.CharField(max_length=32, default="2024")
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Compliance Framework"
        verbose_name_plural = "Compliance Frameworks"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.version_tag})"


class EmissionFactor(models.Model):
    """
    Certified conversion coefficient and emission factors for fuels, grid regions, and materials.
    """
    CATEGORIES = [
        ("SCOPE_1_COMBUSTION", "Scope 1 - Stationary & Mobile Fuel Combustion"),
        ("SCOPE_2_LOCATION_GRID", "Scope 2 - Location-Based Electricity Grid Factor"),
        ("SCOPE_2_MARKET_GRID", "Scope 2 - Market-Based Residual Factor"),
        ("REFRIGERANT_GWP", "Refrigerant Global Warming Potential (GWP)"),
        ("CONVERSION_COEFFICIENT", "Unit Energy Density / Conversion Factor"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    framework = models.ForeignKey(ComplianceFramework, on_delete=models.CASCADE, related_name="emission_factors")
    category = models.CharField(max_length=64, choices=CATEGORIES)
    activity_key = models.CharField(max_length=128, db_index=True, help_text="e.g. DIESEL_LITER, NATURAL_GAS_M3, GRID_US_ERCOT, GRID_DE_NATIONAL")
    display_name = models.CharField(max_length=255)
    
    factor_value = models.DecimalField(max_digits=14, decimal_places=6, help_text="e.g. 2.687000 for kg CO2e / liter diesel")
    factor_unit = models.CharField(max_length=64, help_text="e.g. 'kgCO2e / L', 'kgCO2e / kWh', 'kgCO2e / m3', 'GWP'")
    
    # Gas Speciation (Optional detail for advanced GHG reporting)
    co2_ratio = models.DecimalField(max_digits=10, decimal_places=6, default=0.99)
    ch4_ratio = models.DecimalField(max_digits=10, decimal_places=6, default=0.005)
    n2o_ratio = models.DecimalField(max_digits=10, decimal_places=6, default=0.005)

    source_citation = models.CharField(max_length=512, help_text="Official source reference, e.g. 'EPA eGRID 2024' or 'DEFRA 2024'")
    effective_year = models.PositiveIntegerField(default=2024)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Emission Factor"
        verbose_name_plural = "Emission Factors"
        unique_together = ("framework", "activity_key", "effective_year")
        ordering = ["category", "activity_key"]

    def __str__(self):
        return f"[{self.framework.code}] {self.display_name}: {self.factor_value} {self.factor_unit}"


class CalculationMethodology(models.Model):
    """
    A named calculation methodology version tying together rules, factors, and compliance math.
    Allows compliance officers to adjust math models without changing system code.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    framework = models.ForeignKey(ComplianceFramework, on_delete=models.CASCADE, related_name="methodologies")
    name = models.CharField(max_length=255, default="Corporate Standard GHG & Social ESG v1.0")
    version_label = models.CharField(max_length=32, default="v1.0")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Calculation Methodology"
        verbose_name_plural = "Calculation Methodologies"
        ordering = ["-is_active", "name"]

    def __str__(self):
        return f"{self.name} ({self.version_label}) [{self.framework.code}]"


class FormulaRule(models.Model):
    """
    Configurable mathematical rule evaluated safely by the deterministic calculation engine.
    Example expression: '(consumption * emission_factor) / 1000.0'
    """
    KPI_CATEGORIES = [
        ("SCOPE_1", "Scope 1 Direct GHG"),
        ("SCOPE_2_LOCATION", "Scope 2 Location-Based Indirect GHG"),
        ("SCOPE_2_MARKET", "Scope 2 Market-Based Indirect GHG"),
        ("SOCIAL_DIVERSITY", "Social - Gender Diversity Ratio"),
        ("SOCIAL_SAFETY", "Social - Safety Incident & LTIFR"),
        ("INTENSITY", "ESG Intensity - Energy / Emissions per FTE"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    methodology = models.ForeignKey(CalculationMethodology, on_delete=models.CASCADE, related_name="formula_rules")
    rule_code = models.CharField(max_length=64, help_text="e.g. SCOPE_1_DIESEL, SCOPE_2_GRID, LTIFR_SAFETY, GENDER_DIVERSITY")
    name = models.CharField(max_length=255)
    kpi_category = models.CharField(max_length=32, choices=KPI_CATEGORIES, default="SCOPE_1")

    # Safe mathematical expression evaluated via Python AST parser
    expression = models.CharField(
        max_length=512,
        default="(consumption * emission_factor) / 1000.0",
        help_text="Deterministic formula, e.g. '(consumption * emission_factor) / 1000.0' (converts kg to metric tonnes tCO2e)"
    )
    output_unit = models.CharField(max_length=32, default="tCO2e", help_text="e.g. tCO2e, %, per_million_hours, MWh_per_FTE")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Formula Rule"
        verbose_name_plural = "Formula Rules"
        unique_together = ("methodology", "rule_code")
        ordering = ["kpi_category", "rule_code"]

    def __str__(self):
        return f"{self.rule_code} | {self.expression} -> {self.output_unit}"


class CalculationRun(models.Model):
    """
    Audit execution record of a calculation job over raw warehouse records.
    Provides verifiable enterprise audit trails for ESG disclosures.
    """
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    methodology = models.ForeignKey(CalculationMethodology, on_delete=models.CASCADE, related_name="runs")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="PENDING")
    initiated_by = models.CharField(max_length=128, default="SYSTEM_SCHEDULER")

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(default=0)

    # Aggregated KPI Summary
    total_scope_1_tco2e = models.DecimalField(max_digits=14, decimal_places=4, default=0.0)
    total_scope_2_location_tco2e = models.DecimalField(max_digits=14, decimal_places=4, default=0.0)
    total_scope_2_market_tco2e = models.DecimalField(max_digits=14, decimal_places=4, default=0.0)
    total_ghg_emissions_tco2e = models.DecimalField(max_digits=14, decimal_places=4, default=0.0)
    
    avg_gender_diversity_pct = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    avg_ltifr = models.DecimalField(max_digits=8, decimal_places=3, default=0.0, help_text="Lost Time Injury Frequency Rate")

    records_processed = models.PositiveIntegerField(default=0)
    records_computed = models.PositiveIntegerField(default=0)
    error_log = models.TextField(blank=True)

    class Meta:
        verbose_name = "Calculation Run"
        verbose_name_plural = "Calculation Runs"
        ordering = ["-started_at"]

    def __str__(self):
        return f"Run {self.id} | {self.methodology.name} | Total: {self.total_ghg_emissions_tco2e} tCO2e ({self.status})"


class CalculatedRecord(models.Model):
    """
    Granular, auditable calculated record tied back to raw ERP source and formula.
    Every single number in an ESG report can be inspected here down to the exact math proof.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(CalculationRun, on_delete=models.CASCADE, related_name="calculated_records")
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="calculated_records")
    
    utility_record = models.ForeignKey(FacilityUtilityRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name="calculations")
    workforce_record = models.ForeignKey(WorkforceMetricRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name="calculations")
    
    formula_rule = models.ForeignKey(FormulaRule, on_delete=models.SET_NULL, null=True, related_name="records")
    rule_code = models.CharField(max_length=64, db_index=True)
    kpi_category = models.CharField(max_length=32)

    # Deterministic Lineage & Audit Snapshot
    inputs_snapshot = models.JSONField(help_text="Frozen inputs at execution time (consumption, factor, headcount, etc.)")
    formula_evaluated = models.CharField(max_length=512, help_text="Resolved expression, e.g. '(15200.0 * 2.687) / 1000.0'")
    result_value = models.DecimalField(max_digits=16, decimal_places=4)
    result_unit = models.CharField(max_length=32)

    calculation_trace = models.JSONField(
        default=dict,
        help_text="Step-by-step mathematical proof, conversion factors, source citations, and timestamps"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Calculated Record"
        verbose_name_plural = "Calculated Records"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["rule_code", "created_at"]),
            models.Index(fields=["facility", "kpi_category"]),
        ]

    def __str__(self):
        return f"{self.facility.code} | {self.rule_code}: {self.result_value} {self.result_unit}"
