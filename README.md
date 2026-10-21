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
| `csv_export` | `CSVData.save_as_excel()` writes the frames to one workbook |

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

## Security defaults

* TLS certificate verification is **on** by default. For a private CA pass
  `verify="/path/to/ca.pem"`. `verify=False` must be requested explicitly.
* Credentials are passed as arguments, never stored on objects, logged, or put in errors.
* Every request has a timeout (default 60 s).
* Errors raise `CohesityAPIError` (a `ValueError`) carrying only the HTTP status.

## Development

```
pip install -e ".[dev]"
pytest
ruff check .
```
Tests mock `requests` and use only synthetic data; no cluster is contacted.
