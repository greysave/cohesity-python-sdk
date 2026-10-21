"""Example 4: replica and view (cold) storage tiers per tenant.

Prerequisites: same as auth_cluster_info.py. Needs pandas (installed with the package).

Run
    python examples/replica_and_view_tiers.py --days 30

What it does: finds each tenant's replication runs and views, reads the daily byte counts for
the last N days, and prints the latest value per tenant for each tier.
"""
from __future__ import annotations

import argparse

from example_support import fail, gib, login, make_client, read_settings, time_window

from cohesity_rest_helper import (
    CohesityAPIError,
    CohesityProtectionStatsObject,
    CohesityTenants,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=30, help="look-back window (default 30)")
    args = parser.parse_args(argv)
    settings = read_settings()
    try:
        token = login(settings)
        tenant_ids = make_client(CohesityTenants, token, settings).get_tenants()
        stats = make_client(CohesityProtectionStatsObject, token, settings)
        stats.api_payload["tenantIds"] = tenant_ids
        stats.start_time, stats.end_time = time_window(args.days)
        # get_protection_jobs() creates the per-tenant structure the other lookups extend.
        stats.get_protection_jobs()
        stats.get_replica_protection_jobs()
        stats.view_storage_info()
        stats.get_replica_storage_consumed()
        stats.get_replica_data_written()
        stats.get_view_storage_consumed()
        stats.get_view_data_written()
    except CohesityAPIError as err:
        return fail(str(err))
    print(f"Replica tier, last {args.days} day(s), latest value per tenant:")
    for row in stats.df_replica_sum.to_dict("records"):
        print(
            f"  {row['Tenant Name']}: consumed {gib(row['Replica Storage Consumed'])}, "
            f"written {gib(row['Replica Data Written'])}"
        )
    print("View (cold) tier:")
    for row in stats.df_view_sum.to_dict("records"):
        print(
            f"  {row['Tenant Name']}: consumed {gib(row['Cold Storage Consumed'])}, "
            f"written {gib(row['Cold Data Written'])}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
