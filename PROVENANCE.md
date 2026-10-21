# Provenance

* **Source:** six modules authored by Greg (cohesity_auth, cohesity_stats, cohesity_tenant,
  cohesity_cluster, cohesity_vaults, csv_export), originally written as part of a customer
  deliverable during Greg's employment at Cohesity.
* **Derivation:** sanitized rewrite. Customer name, the chargeback reporting workflow, real
  cluster/tenant identifiers and data, generated reports, virtualenv, Dockerfile, and insecure
  defaults (disabled TLS verification, suppressed warnings, credential-bearing payload strings)
  were removed. The API paths and metric names were retained from Greg-authored modules used in
  the original workflow. A previously considered `pyhesity.py` is third-party and is **not** used.
* **Publication rights:** Greg (the author) explicitly confirmed on 2026-10-21 that he has the
  right and permission to publish this sanitized derivative publicly. This is the author's
  confirmation only; it does not imply any endorsement, review, or approval by Cohesity or any customer.
* **License:** Apache-2.0 (see [LICENSE](LICENSE)), consistent with the author's other public repositories.

* **Additional examples:** `examples/auth_cluster_info.py`, `tenants_and_vaults.py`,
  `warm_storage.py`, `replica_and_view_tiers.py`, `vault_consumption.py`, `full_tier_workbook.py`
  and `examples/example_support.py` are new material written for this release. They call only the
  public API of this package. The original chargeback workflow was used to identify useful task
  sequences. The examples were newly written and contain no customer identifiers, reports, data,
  or customer-specific control flow.
  All hosts, tenants, vaults, IDs and measurements in the examples and tests are invented
  (RFC 5737 / example domains); no real output is included. Credentials are read from
  environment variables only, and TLS verification is never disabled.

See [docs/SOURCE_MAPPING.md](docs/SOURCE_MAPPING.md) for module-level mapping.
