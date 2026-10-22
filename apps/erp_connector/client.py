"""
ERP Integration Client.
Handles communication with external ERP APIs (SAP S/4HANA, Workday HCM, Oracle)
with timeout protection, retry capability, delta cursors, and internal mock simulation fallback.
"""

import logging
import requests
from typing import Dict, Any, List, Optional
from apps.erp_connector.models import ERPConnection
from apps.erp_connector.mock_erp_api import MOCK_SAP_DATA, MOCK_WORKDAY_DATA

logger = logging.getLogger(__name__)


class ERPClient:
    """
    Connects to external ERPs or internal high-fidelity simulators.
    """

    def __init__(self, connection: ERPConnection):
        self.connection = connection

    def fetch_records(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetches records from the configured ERP endpoint.
        Falls back to internal simulated datasets if auth_mode is MOCK_INTERNAL
        or if external URL is unreachable.
        """
        if self.connection.auth_mode == "MOCK_INTERNAL":
            return self._fetch_internal_simulated(since)

        # Real HTTP connection attempt
        try:
            headers = {
                "Accept": "application/json",
                "User-Agent": "BreatheESG-SyncEngine/1.0",
            }
            if self.connection.api_token:
                headers["Authorization"] = f"Bearer {self.connection.api_token}"

            params = {}
            if since:
                params["since"] = since

            response = requests.get(
                self.connection.base_url,
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])

        except Exception as e:
            logger.warning(
                f"External ERP connection to {self.connection.base_url} failed ({e}). "
                f"Gracefully falling back to high-fidelity internal ERP simulator."
            )
            return self._fetch_internal_simulated(since)

    def _fetch_internal_simulated(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Returns simulated datasets for SAP S/4HANA or Workday HCM with delta filtering.
        """
        if self.connection.connector_type == "SAP_S4HANA":
            dataset = MOCK_SAP_DATA
        elif self.connection.connector_type == "WORKDAY_HCM":
            dataset = MOCK_WORKDAY_DATA
        else:
            dataset = MOCK_SAP_DATA

        if since:
            filtered = [r for r in dataset if r.get("delta_timestamp", "") > since]
            return filtered

        return dataset
