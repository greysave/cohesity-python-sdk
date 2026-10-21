"""Generate a realistic, fully synthetic storage-consumption report.

No network requests are made. Every identifier and measurement is invented.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from cohesity_rest_helper import (
    CohesityClusterObject,
    CohesityProtectionStatsObject,
    CohesityProtectionVaultObject,
    CohesityTenants,
    CSVData,
)
from cohesity_rest_helper.cohesity_stats import CONSUMERS_ENDPOINT, TIMESERIES_ENDPOINT

GIB = 1024 ** 3
DAY_1 = 1_756_684_800_000
DAY_30 = 1_759_190_400_000

CLUSTER = {"id": "cluster-0001", "name": "lab-fleet-01", "softwareVersion": "synthetic-7.2.0"}
TENANTS = [{"tenantId": "tenant-aurora"}, {"tenantId": "tenant-beacon"}]
VAULTS = [
    {"id": 901, "name": "archive-east", "externalTargetType": "kS3"},
    {"id": 902, "name": "archive-west", "externalTargetType": "kAzure"},
]


def _jobs(tenant: str, prefix: str, entity_ids: tuple[int, ...]) -> list[dict]:
    return [
        {"name": f"{prefix}-{index}", "groupList": [{
            "entityId": entity_id, "tenantName": tenant, "tenantId": tenant,
        }]}
        for index, entity_id in enumerate(entity_ids, start=1)
    ]


CONSUMERS = {
    ("tenant-aurora", "kProtectionRuns"): _jobs("tenant-aurora", "prod-db", (101, 102)),
    ("tenant-beacon", "kProtectionRuns"): _jobs("tenant-beacon", "files", (201,)),
    ("tenant-aurora", "kReplicationRuns"): _jobs("tenant-aurora", "replica", (301,)),
    ("tenant-beacon", "kReplicationRuns"): _jobs("tenant-beacon", "replica", (302,)),
    ("tenant-aurora", "kViews"): _jobs("tenant-aurora", "analytics-view", (401,)),
    ("tenant-beacon", "kViews"): _jobs("tenant-beacon", "engineering-view", (402,)),
}

LATEST_GIB = {
    (101, "ChunkBytesPhysical"): 600, (101, "ChunkBytesMorphed"): 800,
    (101, "LogicalUsage"): 1600, (102, "ChunkBytesPhysical"): 300,
    (102, "ChunkBytesMorphed"): 450, (102, "LogicalUsage"): 900,
    (201, "ChunkBytesPhysical"): 500, (201, "ChunkBytesMorphed"): 700,
    (201, "LogicalUsage"): 1400, (301, "ChunkBytesMorphed"): 350,
    (302, "ChunkBytesMorphed"): 280, (401, "ChunkBytesPhysical"): 120,
    (401, "ChunkBytesMorphed"): 160, (402, "ChunkBytesPhysical"): 90,
    (402, "ChunkBytesMorphed"): 125, (901, "kMorphedUsageBytes"): 800,
    (902, "kMorphedUsageBytes"): 650,
}


def _series(entity_id: int, metric: str) -> list[dict]:
    latest = LATEST_GIB[(entity_id, metric)] * GIB
    return [
        {"timestampMsecs": DAY_1, "data": {"int64Value": int(latest * 0.92)}},
        {"timestampMsecs": DAY_30, "data": {"int64Value": latest}},
    ]


class SyntheticStatsClient(CohesityProtectionStatsObject):
    """Offline client returning deterministic invented API responses."""

    def __init__(self) -> None:
        super().__init__("synthetic-example-token", "cluster.example.invalid")
        self.start_time, self.end_time = DAY_1, DAY_30

    def _get_json(self, endpoint: str, params: dict | None = None):
        params = params or {}
        if endpoint.endswith("/cluster"):
            return CLUSTER
        if endpoint.endswith("/tenants"):
            return TENANTS
        if endpoint.endswith("/vaults"):
            return VAULTS
        if endpoint == CONSUMERS_ENDPOINT:
            key = (params["organizationsIdList"], params["consumerType"])
            return {"statsList": CONSUMERS[key]}
        if endpoint == TIMESERIES_ENDPOINT:
            entity_id = params.get("entityIdList", params.get("entityId"))
            return {"dataPointVec": _series(entity_id, params["metricName"])}
        raise KeyError(f"No synthetic response for {endpoint}")


def build_report(output_directory: Path) -> tuple[SyntheticStatsClient, dict, list[str], list[dict]]:
    """Run the inventory, statistics, and export sequence used by a capacity report."""
    client = SyntheticStatsClient()
    cluster = CohesityClusterObject.get_cluster_info(client)
    tenant_ids = CohesityTenants.get_tenants(client)
    vaults = CohesityProtectionVaultObject.get_vaults(client)

    client.api_payload["tenantIds"] = tenant_ids
    client.get_protection_jobs()
    client.get_replica_protection_jobs()
    client.view_storage_info()
    client.get_storage_consumed()
    client.get_data_written()
    client.get_logical_usage()
    client.get_replica_storage_consumed()
    client.get_replica_data_written()
    client.get_view_storage_consumed()
    client.get_view_data_written()
    client.api_payload["vaults"] = vaults
    client.get_vault_consumed()

    report = CSVData(
        client.df_warm, client.df_sum, client.df_replica, client.df_replica_sum,
        client.df_view, client.df_view_sum, client.df_vault, client.df_vault_sum,
    )
    output_directory.mkdir(parents=True, exist_ok=True)
    report.save_as_excel(str(output_directory / "synthetic-storage-report.xlsx"))
    report.save_as_csv_files(str(output_directory / "csv"))
    return client, cluster, tenant_ids, vaults


def _gib(value: int) -> str:
    return f"{value / GIB:,.0f} GiB"


def print_summary(client: SyntheticStatsClient, cluster: dict, tenants: list[str],
                  vaults: list[dict], output_directory: Path) -> None:
    print("SYNTHETIC DEMO — no cluster contacted")
    print(f"Cluster: {cluster['name']} ({cluster['softwareVersion']})")
    print(f"Tenants: {len(tenants)} | Vaults: {len(vaults)} (cluster-level)")
    print("Warm capacity by tenant:")
    for row in client.df_sum.to_dict("records"):
        print(
            f"  {row['Tenant Name']}: physical={_gib(row['Warm Storage Consumed'])}, "
            f"written={_gib(row['Warm Data Written'])}, "
            f"logical={_gib(row['Warm Logical Usage'])}"
        )
    print("Vault capacity (cluster-level):")
    for row in client.df_vault_sum.to_dict("records"):
        print(f"  {row['Archive Name']}: {_gib(row['Vault Consumed'])}")
    print(f"Reports: {output_directory}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("synthetic-report"))
    args = parser.parse_args()
    client, cluster, tenants, vaults = build_report(args.output)
    print_summary(client, cluster, tenants, vaults, args.output)


if __name__ == "__main__":
    main()
