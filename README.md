# cohesity-rest-helper

Small Python helpers for authenticating to a Cohesity cluster and pulling
protection / storage statistics over its REST API.

> Released under the Apache License 2.0 (see [LICENSE](LICENSE)). See [PROVENANCE.md](PROVENANCE.md)
> for how this sanitized library was derived. Unofficial; not endorsed by or affiliated with Cohesity.

## Modules

| Module | Purpose |
|---|---|
| `cohesity_auth` | `CohesityUserAuthentication.get_bearer_token()` and `CohesityAPIError` |
| `cohesity_stats` | `CohesityProtectionStatsObject`: protection-run, replication, view and vault consumption stats as pandas frames |
| `cohesity_tenant` | `CohesityTenants.get_tenants()` |
| `cohesity_cluster` | `CohesityClusterObject.get_cluster_info()` |
| `cohesity_vaults` | `CohesityProtectionVaultObject.get_vaults()` |
| `csv_export` | `CSVData.save_as_excel()` writes one workbook; `save_as_csv_files()` writes eight safe CSV files |

## Usage

```python
import os
from cohesity_rest_helper import CohesityUserAuthentication, CohesityTenants

host = os.environ["COHESITY_HOST"]
auth = CohesityUserAuthentication(host, verify=os.environ.get("COHESITY_CA_BUNDLE", True))
token = auth.get_bearer_token(os.environ["COHESITY_USER"],
                              os.environ["COHESITY_PASSWORD"],
                              os.environ.get("COHESITY_DOMAIN", "LOCAL"))

tenants = CohesityTenants(token, host, verify=auth.verify)
ids = tenants.get_tenants()
```

For consumption stats, set `api_payload["tenantIds"]`, `start_time` and `end_time`
(epoch ms), then call `get_protection_jobs()`, `get_storage_consumed()`, etc.

## Synthetic end-to-end report

A runnable offline example demonstrates the complete tenant storage-reporting flow with
fully invented data. It discovers synthetic tenants, protection jobs, replicas, views,
and cluster-level vaults, then creates an Excel workbook and eight CSV files.

```console
python examples/tenant_storage_report.py --output /tmp/synthetic-report
```

Representative results:

| Tenant | Physical | Written | Logical |
|---|---:|---:|---:|
| tenant-aurora | 900 GiB | 1,250 GiB | 2,500 GiB |
| tenant-beacon | 500 GiB | 700 GiB | 1,400 GiB |

The example makes no network requests and uses no real identifiers, credentials, or
measurements. See [the walkthrough and full output](docs/EXAMPLE.md).

## Step-by-step examples

Six short scripts in [`examples/`](examples/) cover the common tasks. They use the live
API paths, but this sanitized release has only been tested with mocked responses so far.
Run them first with a read-only account on a permitted nonproduction cluster.

**Install** (Python 3.9+; run from the repository root):

```console
pip install -e ".[excel]"        # library + pandas + requests, plus openpyxl for .xlsx output
```

**Connection settings come from environment variables.** The examples do not print or write
the password or bearer token:

```console
export COHESITY_HOST=cluster.example.com
export COHESITY_USER=<your user>
export COHESITY_PASSWORD=<your password>
export COHESITY_DOMAIN=LOCAL                  # optional, default LOCAL
export COHESITY_CA_BUNDLE=/path/to/ca.pem     # optional, for a private certificate authority
```

TLS verification is always on in the examples. Each script imports the package as
`from cohesity_rest_helper import ...`, so install it first; run the scripts from the
repository root, e.g. `python examples/warm_storage.py --days 30`.

| Script | What it shows |
|---|---|
| `auth_cluster_info.py` | Log in and read cluster name, ID and software version |
| `tenants_and_vaults.py` | List tenant IDs and vaults (external targets) |
| `warm_storage.py` | Warm tier: physical, written and logical bytes per tenant |
| `replica_and_view_tiers.py` | Replica and view (cold) tiers per tenant |
| `vault_consumption.py` | Consumption per vault (cluster-wide) |
| `full_tier_workbook.py` | All tiers into one eight-sheet Excel workbook (`--output`, `--force`) |

`example_support.py` holds the shared environment/login/time-window helpers. Exported
workbooks describe your cluster, so keep them out of version control (`.gitignore` already
excludes `*.xlsx` and `*.csv`).

## Security defaults

* TLS certificate verification is **on** by default. For a private CA pass
  `verify="/path/to/ca.pem"`. `verify=False` must be requested explicitly.
* The authentication object does not retain the username or password. API client objects keep
  the bearer token in memory for request headers; examples do not print it or include it in errors.
* Every request has a timeout (default 60 s).
* Errors raise `CohesityAPIError` (a `ValueError`) carrying only the HTTP status.

## Development

```
pip install -e ".[dev]"
pytest
ruff check .
```
Tests mock `requests` and use only synthetic data; no cluster is contacted. They also run every script in `examples/` against a fake cluster (`tests/example_fakes.py`).
