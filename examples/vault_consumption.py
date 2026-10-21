"""Example 5: consumption of each vault (external target).

Prerequisites: same as auth_cluster_info.py. Needs pandas (installed with the package).

Run
    python examples/vault_consumption.py --days 30

What it does: lists the vaults, reads each vault's daily consumed bytes for the last N days,
and prints the latest value per vault. Vault usage is cluster-wide, not per tenant.
"""
from __future__ import annotations

import argparse

from example_support import fail, gib, login, make_client, read_settings, time_window

from cohesity_rest_helper import (
    CohesityAPIError,
    CohesityProtectionStatsObject,
    CohesityProtectionVaultObject,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=30, help="look-back window (default 30)")
    args = parser.parse_args(argv)
    settings = read_settings()
    try:
        token = login(settings)
        vaults = make_client(CohesityProtectionVaultObject, token, settings).get_vaults()
        stats = make_client(CohesityProtectionStatsObject, token, settings)
        stats.api_payload["vaults"] = vaults
        stats.start_time, stats.end_time = time_window(args.days)
        stats.get_vault_consumed()
    except CohesityAPIError as err:
        return fail(str(err))
    providers = stats.df_vault.drop_duplicates("Archive Name").set_index("Archive Name")
    print(f"Vault consumption, last {args.days} day(s), latest value per vault:")
    for row in stats.df_vault_sum.to_dict("records"):
        provider = providers.loc[row["Archive Name"], "Archive Provider"]
        print(f"  {row['Archive Name']} ({provider}): {gib(row['Vault Consumed'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
