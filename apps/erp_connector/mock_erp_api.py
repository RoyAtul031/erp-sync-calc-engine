"""
High-fidelity simulated enterprise ERP & HR API endpoints.
Emulates SAP S/4HANA (Plant Maintenance & Utility Invoicing) and Workday HCM (EHS & Workforce Demographics).
"""

import datetime
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


MOCK_SAP_DATA = [
    {
        "external_record_id": "SAP-MATDOC-2024-00101",
        "plant_code": "PLANT-US-01",
        "plant_name": "Austin Gigafactory & Clean Tech Campus",
        "country": "USA",
        "region_state": "Texas",
        "grid_subregion": "US_ERCOT",
        "utility_type": "ELECTRICITY_PURCHASED",
        "scope_category": "SCOPE_2_LOCATION",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "consumption_value": 485000.0,
        "consumption_unit": "KWH",
        "meter_identifier": "SMTR-ERCOT-901-A",
        "sap_document_number": "MATDOC-49001",
        "is_renewable_backed": False,
        "data_quality_score": "METER_READING",
        "delta_timestamp": "2024-02-01T08:30:00Z"
    },
    {
        "external_record_id": "SAP-MATDOC-2024-00102",
        "plant_code": "PLANT-US-01",
        "plant_name": "Austin Gigafactory & Clean Tech Campus",
        "country": "USA",
        "region_state": "Texas",
        "grid_subregion": "US_ERCOT",
        "utility_type": "DIESEL_GENERATOR",
        "scope_category": "SCOPE_1",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "consumption_value": 12400.0,
        "consumption_unit": "LITERS",
        "meter_identifier": "GEN-DIESEL-TANK-01",
        "sap_document_number": "MATDOC-49002",
        "is_renewable_backed": False,
        "data_quality_score": "UTILITY_INVOICE",
        "delta_timestamp": "2024-02-01T09:00:00Z"
    },
    {
        "external_record_id": "SAP-MATDOC-2024-00103",
        "plant_code": "PLANT-US-01",
        "plant_name": "Austin Gigafactory & Clean Tech Campus",
        "country": "USA",
        "region_state": "Texas",
        "grid_subregion": "US_ERCOT",
        "utility_type": "NATURAL_GAS",
        "scope_category": "SCOPE_1",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "consumption_value": 31500.0,
        "consumption_unit": "M3",
        "meter_identifier": "GAS-MAIN-PIPE-04",
        "sap_document_number": "MATDOC-49003",
        "is_renewable_backed": False,
        "data_quality_score": "METER_READING",
        "delta_timestamp": "2024-02-01T09:15:00Z"
    },
    {
        "external_record_id": "SAP-MATDOC-2024-00201",
        "plant_code": "PLANT-DE-02",
        "plant_name": "Munich Advanced Technology Center",
        "country": "Germany",
        "region_state": "Bavaria",
        "grid_subregion": "DE_GRID",
        "utility_type": "ELECTRICITY_PURCHASED",
        "scope_category": "SCOPE_2_MARKET",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "consumption_value": 290000.0,
        "consumption_unit": "KWH",
        "meter_identifier": "SMTR-STADTWERKE-MUC",
        "sap_document_number": "MATDOC-DE-8812",
        "is_renewable_backed": True,  # 100% green hydro/wind tariff
        "data_quality_score": "METER_READING",
        "delta_timestamp": "2024-02-02T10:00:00Z"
    },
    {
        "external_record_id": "SAP-MATDOC-2024-00202",
        "plant_code": "PLANT-DE-02",
        "plant_name": "Munich Advanced Technology Center",
        "country": "Germany",
        "region_state": "Bavaria",
        "grid_subregion": "DE_GRID",
        "utility_type": "NATURAL_GAS",
        "scope_category": "SCOPE_1",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "consumption_value": 18200.0,
        "consumption_unit": "M3",
        "meter_identifier": "GAS-HEATING-CENTRAL",
        "sap_document_number": "MATDOC-DE-8813",
        "is_renewable_backed": False,
        "data_quality_score": "UTILITY_INVOICE",
        "delta_timestamp": "2024-02-02T10:30:00Z"
    },
    {
        "external_record_id": "SAP-MATDOC-2024-00301",
        "plant_code": "PLANT-IN-03",
        "plant_name": "Bangalore Engineering & Global Capability Center",
        "country": "India",
        "region_state": "Karnataka",
        "grid_subregion": "IN_SOUTHERN",
        "utility_type": "ELECTRICITY_PURCHASED",
        "scope_category": "SCOPE_2_LOCATION",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "consumption_value": 340000.0,
        "consumption_unit": "KWH",
        "meter_identifier": "BESCOM-FEEDER-11",
        "sap_document_number": "MATDOC-IN-5501",
        "is_renewable_backed": False,
        "data_quality_score": "METER_READING",
        "delta_timestamp": "2024-02-03T11:00:00Z"
    },
    {
        "external_record_id": "SAP-MATDOC-2024-00302",
        "plant_code": "PLANT-IN-03",
        "plant_name": "Bangalore Engineering & Global Capability Center",
        "country": "India",
        "region_state": "Karnataka",
        "grid_subregion": "IN_SOUTHERN",
        "utility_type": "DIESEL_GENERATOR",
        "scope_category": "SCOPE_1",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "consumption_value": 8500.0,
        "consumption_unit": "LITERS",
        "meter_identifier": "DG-BACKUP-SET-2",
        "sap_document_number": "MATDOC-IN-5502",
        "is_renewable_backed": False,
        "data_quality_score": "UTILITY_INVOICE",
        "delta_timestamp": "2024-02-03T11:45:00Z"
    },
    {
        "external_record_id": "SAP-MATDOC-2024-00401",
        "plant_code": "PLANT-UK-04",
        "plant_name": "London Supply Chain & Logistics Hub",
        "country": "UK",
        "region_state": "Greater London",
        "grid_subregion": "UK_GRID",
        "utility_type": "ELECTRICITY_PURCHASED",
        "scope_category": "SCOPE_2_LOCATION",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "consumption_value": 210000.0,
        "consumption_unit": "KWH",
        "meter_identifier": "UK-POWER-NETWORKS-09",
        "sap_document_number": "MATDOC-UK-1209",
        "is_renewable_backed": False,
        "data_quality_score": "METER_READING",
        "delta_timestamp": "2024-02-04T09:00:00Z"
    },
    {
        "external_record_id": "SAP-MATDOC-2024-00402",
        "plant_code": "PLANT-UK-04",
        "plant_name": "London Supply Chain & Logistics Hub",
        "country": "UK",
        "region_state": "Greater London",
        "grid_subregion": "UK_GRID",
        "utility_type": "DIESEL_FLEET",
        "scope_category": "SCOPE_1",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "consumption_value": 15800.0,
        "consumption_unit": "LITERS",
        "meter_identifier": "FLEET-FUEL-PUMP-01",
        "sap_document_number": "MATDOC-UK-1210",
        "is_renewable_backed": False,
        "data_quality_score": "UTILITY_INVOICE",
        "delta_timestamp": "2024-02-04T09:30:00Z"
    }
]

MOCK_WORKDAY_DATA = [
    {
        "external_record_id": "WD-HR-2024-US01-Q1",
        "plant_code": "PLANT-US-01",
        "plant_name": "Austin Gigafactory & Clean Tech Campus",
        "country": "USA",
        "region_state": "Texas",
        "grid_subregion": "US_ERCOT",
        "period_start": "2024-01-01",
        "period_end": "2024-01-31",
        "total_headcount": 1450,
        "female_headcount": 610,
        "male_headcount": 810,
        "non_binary_headcount": 30,
        "lost_time_injuries": 1,
        "recordable_incidents": 2,
        "total_hours_worked": 248000.0,
        "training_hours_total": 3600.0,
        "employee_turnover_count": 18,
        "source_system": "WORKDAY_GLOBAL_HCM",
        "delta_timestamp": "2024-02-05T08:00:00Z"
    },
    {
        "external_record_id": "WD-HR-2024-DE02-Q1",
        "plant_code": "PLANT-DE-02",
        "plant_name": "Munich Advanced Technology Center",
        "country": "Germany",
        "region_state": "Bavaria",
        "grid_subregion": "DE_GRID",
        "period_start": "2024-01-01",
        "period_end": "2024-01-31",
        "total_headcount": 820,
        "female_headcount": 365,
        "male_headcount": 440,
        "non_binary_headcount": 15,
        "lost_time_injuries": 0,
        "recordable_incidents": 1,
        "total_hours_worked": 138000.0,
        "training_hours_total": 2400.0,
        "employee_turnover_count": 6,
        "source_system": "WORKDAY_GLOBAL_HCM",
        "delta_timestamp": "2024-02-05T08:30:00Z"
    },
    {
        "external_record_id": "WD-HR-2024-IN03-Q1",
        "plant_code": "PLANT-IN-03",
        "plant_name": "Bangalore Engineering & Global Capability Center",
        "country": "India",
        "region_state": "Karnataka",
        "grid_subregion": "IN_SOUTHERN",
        "period_start": "2024-01-01",
        "period_end": "2024-01-31",
        "total_headcount": 2100,
        "female_headcount": 940,
        "male_headcount": 1130,
        "non_binary_headcount": 30,
        "lost_time_injuries": 0,
        "recordable_incidents": 0,
        "total_hours_worked": 352000.0,
        "training_hours_total": 6800.0,
        "employee_turnover_count": 25,
        "source_system": "WORKDAY_GLOBAL_HCM",
        "delta_timestamp": "2024-02-05T09:00:00Z"
    },
    {
        "external_record_id": "WD-HR-2024-UK04-Q1",
        "plant_code": "PLANT-UK-04",
        "plant_name": "London Supply Chain & Logistics Hub",
        "country": "UK",
        "region_state": "Greater London",
        "grid_subregion": "UK_GRID",
        "period_start": "2024-01-01",
        "period_end": "2024-01-31",
        "total_headcount": 480,
        "female_headcount": 195,
        "male_headcount": 275,
        "non_binary_headcount": 10,
        "lost_time_injuries": 1,
        "recordable_incidents": 2,
        "total_hours_worked": 82000.0,
        "training_hours_total": 1100.0,
        "employee_turnover_count": 8,
        "source_system": "WORKDAY_GLOBAL_HCM",
        "delta_timestamp": "2024-02-05T09:30:00Z"
    }
]


from drf_spectacular.utils import extend_schema


class MockSAPUtilityAPIView(APIView):
    """
    Simulated SAP S/4HANA OData / REST Endpoint for Plant Utility Consumption.
    Provides pagination and delta query parameter `?since=...`.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Simulated SAP S/4HANA Utility Feed",
        description="Emulates SAP S/4HANA Plant Maintenance / Utility Accounting OData API."
    )
    def get(self, request):
        since = request.query_params.get("since")
        items = MOCK_SAP_DATA

        if since:
            # Filter delta
            items = [item for item in items if item["delta_timestamp"] > since]

        return Response({
            "status": "success",
            "erp_system": "SAP S/4HANA (Cloud Private Edition 2024)",
            "api_version": "v2.0-OData",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "count": len(items),
            "results": items
        })


class MockWorkdayWorkforceAPIView(APIView):
    """
    Simulated Workday HCM REST Endpoint for Workforce & EHS Social ESG Reporting.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Simulated Workday HCM Workforce Feed",
        description="Emulates Workday HCM Worker & EHS Incident REST API."
    )
    def get(self, request):
        since = request.query_params.get("since")
        items = MOCK_WORKDAY_DATA

        if since:
            items = [item for item in items if item["delta_timestamp"] > since]

        return Response({
            "status": "success",
            "erp_system": "Workday HCM (Enterprise EHS Connector)",
            "api_version": "v41.0",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "count": len(items),
            "results": items
        })
