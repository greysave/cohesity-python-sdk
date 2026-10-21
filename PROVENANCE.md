# Provenance

* **Source:** six modules authored by Greg (cohesity_auth, cohesity_stats, cohesity_tenant,
  cohesity_cluster, cohesity_vaults, csv_export), originally written as part of a customer
  deliverable during Greg's employment at Cohesity.
* **Derivation:** sanitized rewrite. Customer name, the chargeback reporting workflow, real
  cluster/tenant identifiers and data, generated reports, virtualenv, Dockerfile, and insecure
  defaults (disabled TLS verification, suppressed warnings, credential-bearing payload strings)
  were removed. API endpoints and metric names used are those of Cohesity's documented public
  REST API v1. A previously considered `pyhesity.py` is third-party and is **not** used.
* **Publication rights:** Greg (the author) explicitly confirmed on 2026-10-21 that he has the
  right and permission to publish this sanitized derivative publicly. This is the author's
  confirmation only; it does not imply any endorsement, review, or approval by Cohesity or any customer.
* **License:** Apache-2.0 (see [LICENSE](LICENSE)), consistent with the author's other public repositories.

See [docs/SOURCE_MAPPING.md](docs/SOURCE_MAPPING.md) for module-level mapping.
