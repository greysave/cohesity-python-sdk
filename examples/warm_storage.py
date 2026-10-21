"""Example 3: warm (primary protection) storage per tenant.

Prerequisites: same as auth_cluster_info.py. Needs pandas (installed with the package).

Run
    python examples/warm_storage.py --days 30

What it does: finds each tenant's protection jobs, reads the daily physical, written and
logical byte counts for the last N days, and prints the latest value per tenant.
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
        stats.get_protection_jobs()
        stats.get_storage_consumed()
        stats.get_data_written()
        stats.get_logical_usage()
    except CohesityAPIError as err:
        return fail(str(err))
    print(f"Warm storage, last {args.days} day(s), latest value per tenant:")
    for row in stats.df_sum.to_dict("records"):
        print(
            f"  {row['Tenant Name']}: physical {gib(row['Warm Storage Consumed'])}, "
            f"written {gib(row['Warm Data Written'])}, logical {gib(row['Warm Logical Usage'])}"
        )
    print(f"({len(stats.df_warm)} daily data points across all jobs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
