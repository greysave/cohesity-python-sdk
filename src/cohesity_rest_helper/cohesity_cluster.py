"""Cluster info module."""
from cohesity_rest_helper.cohesity_stats import API_ROOT, CohesityProtectionStatsObject


class CohesityClusterObject(CohesityProtectionStatsObject):
    """Represents the Cohesity cluster object."""

    def get_cluster_info(self) -> dict:
        """Fetch cluster info, store it in ``api_payload['cluster']`` and return it.

        Raises:
            CohesityAPIError: If the status code is not 200.
        """
        self.api_payload["cluster"] = self._get_json(API_ROOT + "/cluster")
        return self.api_payload["cluster"]
