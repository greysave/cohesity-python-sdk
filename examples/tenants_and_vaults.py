"""Example 2: list tenants and vaults (external targets).

Prerequisites: same as auth_cluster_info.py (install the package, set the COHESITY_* variables).

Run
    python examples/tenants_and_vaults.py

What it does: logs in, then lists every tenant ID and every vault with its provider type.
"""
from __future__ import annotations

import argparse

from example_support import fail, login, make_client, read_settings

from cohesity_rest_helper import CohesityAPIError, CohesityProtectionVaultObject, CohesityTenants


def main(argv=None) -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    settings = read_settings()
    try:
        token = login(settings)
        tenants = make_client(CohesityTenants, token, settings).get_tenants()
        vaults = make_client(CohesityProtectionVaultObject, token, settings).get_vaults()
    except CohesityAPIError as err:
        return fail(str(err))
    print(f"{len(tenants)} tenant(s):")
    for tenant_id in tenants:
        print(f"  {tenant_id}")
    print(f"{len(vaults)} vault(s):")
    for vault in vaults:
        print(f"  {vault['name']} (id {vault['id']}, provider {vault['externalTargetType']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
