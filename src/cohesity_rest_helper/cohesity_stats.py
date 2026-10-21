"""Cohesity time series stats: protection runs, replication, views and vaults."""
import datetime
from typing import Dict, List, Union

import pandas as pd
import requests
from requests.structures import CaseInsensitiveDict

from cohesity_rest_helper.cohesity_auth import (
    DEFAULT_TIMEOUT,
    CohesityAPIError,
    normalize_cluster_url,
)

API_ROOT = "/irisservices/api/v1/public"
CONSUMERS_ENDPOINT = API_ROOT + "/stats/consumers"
TIMESERIES_ENDPOINT = API_ROOT + "/statistics/timeSeriesStats"
WEEK_MSECS = 604800000
SORT_KEYS = ["Tenant Name", "Tenant ID", "Time", "Job Name"]


class CohesityProtectionStatsObject:
    """Cohesity protection stats object.

    Callers populate ``api_payload['tenantIds']`` (see ``CohesityTenants.get_tenants``)
    and ``start_time`` / ``end_time`` (epoch milliseconds) before querying.
    """

    def __init__(self, bearer_token: str, cluster_url: str,
                 verify: Union[bool, str] = True, timeout: int = DEFAULT_TIMEOUT):
        json_type = "application/json"
        self.cluster_url = normalize_cluster_url(cluster_url)
        self.bearer_token = bearer_token
        self.verify = verify
        self.timeout = timeout
        self.protocol = "https://"
        self.headers = CaseInsensitiveDict()
        self.headers["Accept"] = json_type
        self.headers["Content-type"] = json_type
        self.headers["Authorization"] = "bearer " + self.bearer_token
        self.api_payload: Dict = {}
        self.start_time = None
        self.end_time = None
        self.df_warm = None
        self.df_sum = None
        self.df_replica = None
        self.df_replica_sum = None
        self.df_view = None
        self.df_view_sum = None
        self.df_vault = None
        self.df_vault_sum = None

    # ---- shared plumbing -------------------------------------------------
    def _get_json(self, endpoint: str, params: dict = None):
        """GET an endpoint and return decoded JSON; raise CohesityAPIError if not 200."""
        url = self.protocol + self.cluster_url + endpoint
        response = requests.get(url=url, params=params, headers=self.headers,
                                verify=self.verify, timeout=self.timeout)
        if response.status_code != 200:
            raise CohesityAPIError(
                f"GET {endpoint} failed with HTTP {response.status_code}", response.status_code)
        return response.json()

    def _require_window(self) -> None:
        if self.start_time is None or self.end_time is None:
            raise ValueError("start_time and end_time (epoch msecs) must be set first")

    def convert_epoch_usecs(self, epoch: float) -> datetime.datetime:
        """Convert epoch microseconds to a datetime."""
        return datetime.datetime.fromtimestamp(epoch / 10**6)

    def convert_epoch_msecs(self, epoch: float) -> datetime.datetime:
        """Convert epoch milliseconds to a datetime."""
        return datetime.datetime.fromtimestamp(epoch / 10**3)

    def _consumers(self, tenant: str, consumer_type: str, fetch_policy: bool = False) -> list:
        params = {
            "organizationsIdList": tenant,
            "msecsBeforeCurrentTimeToCompare": WEEK_MSECS,
            "maxCount": 1000,
            "fetchViewBoxName": "true",
            "fetchTenantName": "true",
            "fetchProtectionEnvironment": "true",
            "consumerType": consumer_type,
        }
        if fetch_policy:
            params["fetchProtectionPolicy"] = "true"
        return self._get_json(CONSUMERS_ENDPOINT, params)["statsList"]

    def _timeseries(self, entity_id, metric: str) -> list:
        params = {
            "startTimeMsecs": self.start_time,
            "endTimeMsecs": self.end_time,
            "schemaName": "BookKeeperStats",
            "metricName": metric,
            "rollupIntervalSecs": 86400,
            "rollupFunction": "latest",
            "entityIdList": entity_id,
        }
        return self._get_json(TIMESERIES_ENDPOINT, params)["dataPointVec"]

    def _metric_frame(self, stats_key: str, metric: str, column: str) -> pd.DataFrame:
        """One row per (job entity, data point) for a metric, sorted by SORT_KEYS."""
        self._require_window()
        rows: List[dict] = []
        for tenant in self.api_payload["tenants"].values():
            for stat in tenant[stats_key]:
                for entity in stat["groupList"]:
                    for point in self._timeseries(entity["entityId"], metric):
                        rows.append({
                            "Tenant Name": entity["tenantName"],
                            "Tenant ID": entity["tenantId"],
                            "Job Name": stat["name"],
                            "Time": point["timestampMsecs"],
                            column: point["data"]["int64Value"],
                        })
        columns = ["Tenant Name", "Tenant ID", "Job Name", "Time", column]
        frame = pd.DataFrame(rows, columns=columns)
        return frame.sort_values(SORT_KEYS).reset_index(drop=True)

    @staticmethod
    def _latest_sum(frame: pd.DataFrame, column: str) -> pd.DataFrame:
        """Latest data point per job, summed per tenant."""
        latest = frame.drop_duplicates(subset="Job Name", keep="last")
        return latest.groupby(["Tenant Name"])[column].sum().reset_index()

    def _first_metric(self, stats_key, metric, column):
        frame = self._metric_frame(stats_key, metric, column)
        return frame, self._latest_sum(frame, column)

    def _add_metric(self, frame, summary, stats_key, metric, column):
        extra = self._metric_frame(stats_key, metric, column)
        frame = frame.merge(extra, on=SORT_KEYS, how="left")
        summary = summary.merge(self._latest_sum(extra, column), on="Tenant Name", how="left")
        return frame, summary

    # ---- protection runs -------------------------------------------------
    def get_protection_jobs(self) -> None:
        """Get warm protection jobs for each tenant in ``api_payload['tenantIds']``."""
        self.api_payload["tenants"] = {}
        for tenant in self.api_payload["tenantIds"]:
            self.api_payload["tenants"][tenant] = {
                "stats_list": self._consumers(tenant, "kProtectionRuns")}

    def get_replica_protection_jobs(self) -> None:
        """Get replica protection objects."""
        for tenant in self.api_payload["tenantIds"]:
            self.api_payload["tenants"][tenant]["replica_stats_list"] = self._consumers(
                tenant, "kReplicationRuns")

    def view_storage_info(self) -> None:
        """Get cold (view) storage info."""
        for tenant in self.api_payload["tenantIds"]:
            self.api_payload["tenants"][tenant]["view_stats_list"] = self._consumers(
                tenant, "kViews", fetch_policy=True)

    # ---- warm ------------------------------------------------------------
    def get_storage_consumed(self) -> None:
        """Warm storage consumed (ChunkBytesPhysical)."""
        self.df_warm, self.df_sum = self._first_metric(
            "stats_list", "ChunkBytesPhysical", "Warm Storage Consumed")

    def get_data_written(self) -> None:
        """Warm data written (ChunkBytesMorphed)."""
        self.df_warm, self.df_sum = self._add_metric(
            self.df_warm, self.df_sum, "stats_list", "ChunkBytesMorphed", "Warm Data Written")

    def get_logical_usage(self) -> None:
        """Warm logical usage (LogicalUsage)."""
        self.df_warm, self.df_sum = self._add_metric(
            self.df_warm, self.df_sum, "stats_list", "LogicalUsage", "Warm Logical Usage")

    # ---- replica ---------------------------------------------------------
    def get_replica_storage_consumed(self) -> None:
        """Replica storage consumed (ChunkBytesMorphed)."""
        self.df_replica, self.df_replica_sum = self._first_metric(
            "replica_stats_list", "ChunkBytesMorphed", "Replica Storage Consumed")

    def get_replica_data_written(self) -> None:
        """Replica data written (ChunkBytesMorphed)."""
        self.df_replica, self.df_replica_sum = self._add_metric(
            self.df_replica, self.df_replica_sum, "replica_stats_list",
            "ChunkBytesMorphed", "Replica Data Written")

    # ---- cold / views ----------------------------------------------------
    def get_view_storage_consumed(self) -> None:
        """Cold storage consumed (ChunkBytesPhysical)."""
        self.df_view, self.df_view_sum = self._first_metric(
            "view_stats_list", "ChunkBytesPhysical", "Cold Storage Consumed")

    def get_view_data_written(self) -> None:
        """Cold data written (ChunkBytesMorphed)."""
        self.df_view, self.df_view_sum = self._add_metric(
            self.df_view, self.df_view_sum, "view_stats_list",
            "ChunkBytesMorphed", "Cold Data Written")

    # ---- frozen / vaults -------------------------------------------------
    def get_vault_consumed(self) -> None:
        """Frozen (external target / vault) consumed bytes.

        Requires ``api_payload['vaults']`` (see ``CohesityProtectionVaultObject.get_vaults``).
        """
        self._require_window()
        rows = []
        for vault in self.api_payload["vaults"]:
            params = {
                "endTimeMsecs": self.end_time,
                "entityId": vault["id"],
                "metricName": "kMorphedUsageBytes",
                "metricUnitType": 0,
                "range": "month",
                "rollupFunction": "latest",
                "rollupIntervalSecs": 86400,
                "schemaName": "kIceboxVaultStats",
                "startTimeMsecs": self.start_time,
            }
            for point in self._get_json(TIMESERIES_ENDPOINT, params)["dataPointVec"]:
                rows.append({
                    "Archive Name": vault["name"],
                    "Archive Provider": vault["externalTargetType"],
                    "Time": point["timestampMsecs"],
                    "Vault Consumed": point["data"]["int64Value"],
                })
        columns = ["Archive Name", "Archive Provider", "Time", "Vault Consumed"]
        self.df_vault = pd.DataFrame(rows, columns=columns).sort_values(
            ["Archive Name", "Time"]).reset_index(drop=True)
        latest = self.df_vault.drop_duplicates(subset="Archive Name", keep="last")
        self.df_vault_sum = latest.groupby(["Archive Name"])["Vault Consumed"].sum().reset_index()
