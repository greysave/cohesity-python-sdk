"""Example 1: log in and read basic cluster information.

Prerequisites
    pip install -e .                      # from the repository root
    export COHESITY_HOST=cluster.example.com
    export COHESITY_USER=<your user>
    export COHESITY_PASSWORD=<your password>
    # optional: COHESITY_DOMAIN (default LOCAL), COHESITY_CA_BUNDLE=/path/to/ca.pem

Run
    python examples/auth_cluster_info.py

What it does: requests a bearer token, then asks the cluster for its description.
"""
from __future__ import annotations

import argparse

from example_support import fail, login, make_client, read_settings

from cohesity_rest_helper import CohesityAPIError, CohesityClusterObject

SHOWN_FIELDS = ("name", "id", "clusterSoftwareVersion")


def main(argv=None) -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    settings = read_settings()
    try:
        token = login(settings)
        cluster = make_client(CohesityClusterObject, token, settings).get_cluster_info()
    except CohesityAPIError as err:
        return fail(str(err))
    print("Authentication succeeded.")
    for field in SHOWN_FIELDS:
        print(f"  {field}: {cluster.get(field, 'n/a')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
