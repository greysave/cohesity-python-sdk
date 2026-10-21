# Synthetic tenant storage report

This example mirrors the shape of the original operational reporting workflow while
replacing every cluster, tenant, job, vault, timestamp, and measurement with deterministic
fixtures. It makes **no network requests** and contains no customer or production data.

## Run it

```console
python examples/tenant_storage_report.py --output /tmp/synthetic-report
```

It exercises the helper's inventory and reporting sequence:

1. Read cluster metadata, tenants, and external vaults.
2. Discover warm protection jobs, replication jobs, and views for each tenant.
3. Fetch physical, written, logical, replica, view, and vault measurements.
4. Aggregate the latest job values by tenant.
5. Export one eight-sheet Excel workbook and eight UTF-8 CSV files.

Vault totals are **cluster-level**, not tenant-level.

## Representative console output

```text
SYNTHETIC DEMO — no cluster contacted
Cluster: lab-fleet-01 (synthetic-7.2.0)
Tenants: 2 | Vaults: 2 (cluster-level)
Warm capacity by tenant:
  tenant-aurora: physical=900 GiB, written=1,250 GiB, logical=2,500 GiB
  tenant-beacon: physical=500 GiB, written=700 GiB, logical=1,400 GiB
Vault capacity (cluster-level):
  archive-east: 800 GiB
  archive-west: 650 GiB
Reports: /tmp/synthetic-report
```

## Selected generated results

| Tenant | Physical | Written | Logical |
|---|---:|---:|---:|
| tenant-aurora | 900 GiB | 1,250 GiB | 2,500 GiB |
| tenant-beacon | 500 GiB | 700 GiB | 1,400 GiB |

| Cluster-level vault | Provider | Consumed |
|---|---|---:|
| archive-east | kS3 | 800 GiB |
| archive-west | kAzure | 650 GiB |

Committed CSV examples are under [`examples/sample_output/`](../examples/sample_output/).
CSV exports add an ISO-8601 UTC timestamp and neutralize values that spreadsheet programs
could interpret as formulas.

This is a storage-consumption demonstration, not a billing system and not a CVE or
vulnerability report. The project is unofficial and is not endorsed by or affiliated with
Cohesity.
