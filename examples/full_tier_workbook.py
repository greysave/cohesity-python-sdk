"""Example 6: every storage tier in one Excel workbook.

Prerequisites
    pip install -e ".[excel]"             # adds openpyxl, needed to write .xlsx files
    plus the COHESITY_* variables described in auth_cluster_info.py

Run
    python examples/full_tier_workbook.py --days 30 --output storage-tiers.xlsx

What it does: gathers warm, replica, view (cold) and vault (frozen) statistics and writes
eight sheets (a granular and a summary sheet per tier). Existing files are not overwritten
unless --force is given. Treat the workbook as sensitive: it describes your cluster.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from example_support import fail, login, make_client, read_settings, time_window

from cohesity_rest_helper import (
    CohesityAPIError,
    CohesityProtectionStatsObject,
    CohesityProtectionVaultObject,
    CohesityTenants,
    CSVData,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=30, help="look-back window (default 30)")
    parser.add_argument("--output", type=Path, default=Path("storage-tiers.xlsx"))
    parser.add_argument("--force", action="store_true", help="overwrite an existing file")
    args = parser.parse_args(argv)
    try:
        import openpyxl  # noqa: F401  (pandas needs it to write .xlsx)
    except ImportError:
        return fail('openpyxl is missing; run: pip install -e ".[excel]"')
    if args.output.exists() and not args.force:
        return fail(f"{args.output} already exists; pass --force to overwrite it")
    settings = read_settings()
    try:
        token = login(settings)
        tenant_ids = make_client(CohesityTenants, token, settings).get_tenants()
        vaults = make_client(CohesityProtectionVaultObject, token, settings).get_vaults()
        stats = make_client(CohesityProtectionStatsObject, token, settings)
        stats.api_payload["tenantIds"] = tenant_ids
        stats.api_payload["vaults"] = vaults
        stats.start_time, stats.end_time = time_window(args.days)
        stats.get_protection_jobs()
        stats.get_replica_protection_jobs()
        stats.view_storage_info()
        stats.get_storage_consumed()
        stats.get_data_written()
        stats.get_logical_usage()
        stats.get_replica_storage_consumed()
        stats.get_replica_data_written()
        stats.get_view_storage_consumed()
        stats.get_view_data_written()
        stats.get_vault_consumed()
    except CohesityAPIError as err:
        return fail(str(err))
    CSVData(
        stats.df_warm, stats.df_sum, stats.df_replica, stats.df_replica_sum,
        stats.df_view, stats.df_view_sum, stats.df_vault, stats.df_vault_sum,
    ).save_as_excel(str(args.output))
    print(f"Wrote {args.output} (8 sheets: warm, replica, cold and frozen tiers).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
