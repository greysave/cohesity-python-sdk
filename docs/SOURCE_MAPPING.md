# Source-to-release mapping

Source dir: `cohesity_api_helper/` (private, quarantined). Release package: `src/cohesity_rest_helper/`.

| Source module | Release module | Changes |
|---|---|---|
| `cohesity_auth.py` | `cohesity_auth.py` | `verify` defaults to True (was hard-coded False); `disable_warnings` removed; `timeout` configurable; JSON via `json=`; `CohesityAPIError(ValueError)` with status code replaces bare `ValueError`; host normalization; parameter `security` renamed `password`; stray `@dataclass` removed |
| `cohesity_stats.py` | `cohesity_stats.py` | Same class, attributes, and public methods. Eleven copy-pasted request/parse blocks collapsed into `_get_json`, `_consumers`, `_timeseries`, `_metric_frame`; query strings built via `params=`; TLS verify/timeout configurable; same metrics and column names. Fixes: granular frames are now merged on keys instead of positional `join` (original joined an unsorted frame to a sorted one); `get_vault_consumed` emits one row per data point (original looped over every vault config key, duplicating rows); unused variables dropped; `start_time`/`end_time` validated |
| `cohesity_tenant.py` | `cohesity_tenant.py` | Uses shared `_get_json`; annotated as returning a list of tenant IDs |
| `cohesity_cluster.py` | `cohesity_cluster.py` | Class renamed `CohesityClusterObject` (typo fix); now also returns the payload |
| `cohesity_vaults.py` | `cohesity_vaults.py` | Uses shared `_get_json` |
| `csv_export.py` | `csv_export.py` | Proper dataclass fields; `save_as_excel` added, `save_as_csv` kept as alias (it always wrote .xlsx); public release later added safe multi-file CSV export with UTC timestamps and formula neutralization |
| `__init__.py` (empty) | `__init__.py` | Public exports |

Removed entirely: customer/chargeback workflow code, reports, venv, Dockerfile, real identifiers.

`examples/tenant_storage_report.py`, `docs/EXAMPLE.md`, and `examples/sample_output/` are new public-release material built from invented fixtures. They demonstrate the generic inventory-and-capacity sequence without copying a customer report or its data.
