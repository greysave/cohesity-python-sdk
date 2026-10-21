"""Tenant API module."""
from typing import List

from cohesity_rest_helper.cohesity_stats import API_ROOT, CohesityProtectionStatsObject


class CohesityTenants(CohesityProtectionStatsObject):
    """Cohesity tenant class."""

    def get_tenants(self) -> List[str]:
        """Return the list of tenant IDs.

        Raises:
            CohesityAPIError: If the status code is not 200.
        """
        return [tenant["tenantId"] for tenant in self._get_json(API_ROOT + "/tenants")]
