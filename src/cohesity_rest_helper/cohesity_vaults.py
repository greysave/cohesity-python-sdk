"""Vault (external target) module."""
from cohesity_rest_helper.cohesity_stats import API_ROOT, CohesityProtectionStatsObject


class CohesityProtectionVaultObject(CohesityProtectionStatsObject):
    """Get vault objects."""

    def get_vaults(self) -> list:
        """Return vault objects.

        Raises:
            CohesityAPIError: If the status code is not 200.
        """
        return self._get_json(API_ROOT + "/vaults")
