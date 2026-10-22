"""
Seed data script for standard compliance frameworks, certified emission factors,
and default calculation methodologies for Global Enterprise ESG Operations.
Supports EU CSRD, US EPA, UK DEFRA, India BRSR, and GHG Protocol.
"""

from decimal import Decimal
from apps.calculation_engine.models import (
    ComplianceFramework,
    EmissionFactor,
    CalculationMethodology,
    FormulaRule,
)
from apps.erp_connector.models import ERPConnection


def seed_all_reference_data():
    """
    Idempotently seeds global compliance frameworks, emission factors, formulas, and ERP connections.
    """
    # 1. Global Multi-Jurisdiction Compliance Frameworks
    frameworks_data = [
        {
            "code": "GHG_PROTOCOL",
            "name": "GHG Protocol Corporate Standard (WRI/WBCSD)",
            "jurisdiction": "Global (ISO 14064 Aligned)",
            "version_tag": "2024.1",
            "is_default": True,
            "description": "Global benchmark accounting standard for corporate Scope 1, 2, and 3 GHG disclosures.",
        },
        {
            "code": "EU_CSRD",
            "name": "EU CSRD / ESRS E1 (Climate Change & Scope 1-3)",
            "jurisdiction": "European Union (EFRAG)",
            "version_tag": "2024",
            "is_default": False,
            "description": "Mandatory European Corporate Sustainability Reporting Directive under ESRS E1 standard.",
        },
        {
            "code": "US_EPA",
            "name": "US EPA Mandatory Reporting (GHGRP & eGRID 2024)",
            "jurisdiction": "United States (EPA)",
            "version_tag": "2024",
            "is_default": False,
            "description": "US Environmental Protection Agency standards including regional eGRID electricity factors.",
        },
        {
            "code": "UK_DEFRA",
            "name": "UK DEFRA / DESNZ GHG Conversion Factors",
            "jurisdiction": "United Kingdom",
            "version_tag": "2024",
            "is_default": False,
            "description": "UK Department for Energy Security and Net Zero government GHG reporting factors.",
        },
        {
            "code": "INDIA_BRSR",
            "name": "India SEBI BRSR (Business Responsibility & Sustainability)",
            "jurisdiction": "India (SEBI)",
            "version_tag": "2024",
            "is_default": False,
            "description": "Securities and Exchange Board of India (SEBI) Core BRSR ESG disclosure framework.",
        },
    ]

    framework_objects = {}
    for fw in frameworks_data:
        obj, _ = ComplianceFramework.objects.get_or_create(
            code=fw["code"],
            defaults={
                "name": fw["name"],
                "jurisdiction": fw["jurisdiction"],
                "version_tag": fw["version_tag"],
                "is_default": fw["is_default"],
                "description": fw["description"],
            }
        )
        framework_objects[fw["code"]] = obj

    ghg_fw = framework_objects["GHG_PROTOCOL"]
    csrd_fw = framework_objects["EU_CSRD"]
    epa_fw = framework_objects["US_EPA"]
    defra_fw = framework_objects["UK_DEFRA"]
    brsr_fw = framework_objects["INDIA_BRSR"]

    # 2. Certified Emission Factors
    factors_data = [
        # Scope 1 - Fuels
        {
            "framework": ghg_fw,
            "category": "SCOPE_1_COMBUSTION",
            "activity_key": "DIESEL_LITER",
            "display_name": "Diesel Fuel Combustion (Stationary & Mobile Fleet)",
            "factor_value": Decimal("2.687000"),
            "factor_unit": "kgCO2e / L",
            "source_citation": "GHG Protocol Emission Factor Hub 2024",
            "effective_year": 2024,
        },
        {
            "framework": ghg_fw,
            "category": "SCOPE_1_COMBUSTION",
            "activity_key": "NATURAL_GAS_M3",
            "display_name": "Natural Gas Combustion (Stationary Heating & Boilers)",
            "factor_value": Decimal("2.023000"),
            "factor_unit": "kgCO2e / m3",
            "source_citation": "GHG Protocol Stationary Combustion Tool v4.1",
            "effective_year": 2024,
        },
        # Scope 2 - Electricity Grids
        {
            "framework": ghg_fw,
            "category": "SCOPE_2_LOCATION_GRID",
            "activity_key": "GRID_US_ERCOT",
            "display_name": "US ERCOT Grid (Texas Interconnection)",
            "factor_value": Decimal("0.389000"),
            "factor_unit": "kgCO2e / kWh",
            "source_citation": "EPA eGRID2024 Subregion ERCT",
            "effective_year": 2024,
        },
        {
            "framework": ghg_fw,
            "category": "SCOPE_2_LOCATION_GRID",
            "activity_key": "GRID_US_CAMX",
            "display_name": "US CAMX Grid (California Interconnection)",
            "factor_value": Decimal("0.215000"),
            "factor_unit": "kgCO2e / kWh",
            "source_citation": "EPA eGRID2024 Subregion CAMX",
            "effective_year": 2024,
        },
        {
            "framework": ghg_fw,
            "category": "SCOPE_2_LOCATION_GRID",
            "activity_key": "GRID_DE_GRID",
            "display_name": "Germany National Grid Factor (UBA Federal Environment Agency)",
            "factor_value": Decimal("0.366000"),
            "factor_unit": "kgCO2e / kWh",
            "source_citation": "Umweltbundesamt (UBA) Germany 2024",
            "effective_year": 2024,
        },
        {
            "framework": ghg_fw,
            "category": "SCOPE_2_LOCATION_GRID",
            "activity_key": "GRID_IN_SOUTHERN",
            "display_name": "India National / Regional Grid (CEA CO2 Baseline)",
            "factor_value": Decimal("0.710000"),
            "factor_unit": "kgCO2e / kWh",
            "source_citation": "Central Electricity Authority (CEA) India User Guide v19",
            "effective_year": 2024,
        },
        {
            "framework": ghg_fw,
            "category": "SCOPE_2_LOCATION_GRID",
            "activity_key": "GRID_UK_GRID",
            "display_name": "UK National Grid Electricity (DESNZ)",
            "factor_value": Decimal("0.207000"),
            "factor_unit": "kgCO2e / kWh",
            "source_citation": "UK DESNZ / DEFRA 2024 Conversion Factors",
            "effective_year": 2024,
        },
        # Refrigerants & GWP
        {
            "framework": ghg_fw,
            "category": "REFRIGERANT_GWP",
            "activity_key": "REFRIGERANT_R410A",
            "display_name": "Refrigerant R-410A Fugitive GWP (IPCC AR5)",
            "factor_value": Decimal("2088.000000"),
            "factor_unit": "GWP (IPCC AR5)",
            "source_citation": "IPCC Fifth Assessment Report (AR5)",
            "effective_year": 2024,
        },
    ]

    for f_data in factors_data:
        EmissionFactor.objects.get_or_create(
            framework=f_data["framework"],
            activity_key=f_data["activity_key"],
            effective_year=f_data["effective_year"],
            defaults=f_data
        )

    # 3. Calculation Methodology & Formula Rules
    methodology, _ = CalculationMethodology.objects.get_or_create(
        name="Global Corporate Standard GHG & Social ESG v1.0",
        framework=ghg_fw,
        version_label="v1.0",
        defaults={
            "description": "Enterprise deterministic model computing Scope 1 direct combustion, Scope 2 location/market grid electricity, and Workforce social metrics.",
            "is_active": True,
        }
    )

    formula_rules_data = [
        {
            "rule_code": "SCOPE_1_DIESEL",
            "name": "Scope 1 Stationary Diesel Generators",
            "kpi_category": "SCOPE_1",
            "expression": "(consumption * emission_factor) / 1000.0",
            "output_unit": "tCO2e",
            "description": "Converts liters of diesel to metric tonnes CO2 equivalent: (liters * 2.687 kgCO2e/L) / 1000.",
        },
        {
            "rule_code": "SCOPE_1_DIESEL_FLEET",
            "name": "Scope 1 Mobile Logistics Fleet",
            "kpi_category": "SCOPE_1",
            "expression": "(consumption * emission_factor) / 1000.0",
            "output_unit": "tCO2e",
            "description": "Converts fleet liters of diesel to metric tonnes CO2e.",
        },
        {
            "rule_code": "SCOPE_1_NAT_GAS",
            "name": "Scope 1 Natural Gas Heating & Boilers",
            "kpi_category": "SCOPE_1",
            "expression": "(consumption * emission_factor) / 1000.0",
            "output_unit": "tCO2e",
            "description": "Converts cubic meters of natural gas to metric tonnes CO2e: (m3 * 2.023 kgCO2e/m3) / 1000.",
        },
        {
            "rule_code": "SCOPE_2_LOCATION",
            "name": "Scope 2 Location-Based Grid Electricity",
            "kpi_category": "SCOPE_2_LOCATION",
            "expression": "(consumption * emission_factor) / 1000.0",
            "output_unit": "tCO2e",
            "description": "Multiplies grid electricity (kWh) by regional grid factor (kgCO2e/kWh), divided by 1000 for tCO2e.",
        },
        {
            "rule_code": "SCOPE_2_MARKET",
            "name": "Scope 2 Market-Based Contractual Instruments",
            "kpi_category": "SCOPE_2_MARKET",
            "expression": "(consumption * emission_factor) / 1000.0",
            "output_unit": "tCO2e",
            "description": "Market-based method: PPA / Renewable Energy Certificates (REC) yield zero emission factors.",
        },
        {
            "rule_code": "GENDER_DIVERSITY_PCT",
            "name": "Social - Gender Diversity Ratio",
            "kpi_category": "SOCIAL_DIVERSITY",
            "expression": "(female_headcount / total_headcount) * 100.0",
            "output_unit": "%",
            "description": "Percentage of operational workforce identifying as female.",
        },
        {
            "rule_code": "LTIFR_SAFETY",
            "name": "Social - Lost Time Injury Frequency Rate (LTIFR)",
            "kpi_category": "SOCIAL_SAFETY",
            "expression": "(lost_time_injuries * 1000000.0) / total_hours_worked",
            "output_unit": "injuries_per_million_hours",
            "description": "International ILO / OSHA standard safety frequency rate normalized per 1,000,000 exposure hours.",
        },
    ]

    for r_data in formula_rules_data:
        FormulaRule.objects.get_or_create(
            methodology=methodology,
            rule_code=r_data["rule_code"],
            defaults=r_data
        )

    # 4. Global Enterprise ERP Connections
    ERPConnection.objects.get_or_create(
        name="SAP S/4HANA - Global Utility Invoicing & PM",
        defaults={
            "connector_type": "SAP_S4HANA",
            "base_url": "http://127.0.0.1:8080/api/erp/mock-erp/sap/utility-metering/",
            "auth_mode": "MOCK_INTERNAL",
            "sync_interval_minutes": 60,
            "is_active": True,
            "last_sync_status": "HEALTHY",
        }
    )

    ERPConnection.objects.get_or_create(
        name="Workday HCM - Global Workforce & EHS Safety",
        defaults={
            "connector_type": "WORKDAY_HCM",
            "base_url": "http://127.0.0.1:8080/api/erp/mock-erp/workday/workforce-metrics/",
            "auth_mode": "MOCK_INTERNAL",
            "sync_interval_minutes": 120,
            "is_active": True,
            "last_sync_status": "HEALTHY",
        }
    )
