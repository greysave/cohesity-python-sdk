from pathlib import Path

import pandas as pd

from cohesity_rest_helper import CSVData
from examples.tenant_storage_report import GIB, build_report


def test_synthetic_example_builds_expected_reports(tmp_path: Path):
    client, cluster, tenants, vaults = build_report(tmp_path)

    assert cluster["name"] == "lab-fleet-01"
    assert tenants == ["tenant-aurora", "tenant-beacon"]
    assert [vault["name"] for vault in vaults] == ["archive-east", "archive-west"]
    assert (tmp_path / "synthetic-storage-report.xlsx").exists()

    warm = client.df_sum.set_index("Tenant Name")
    assert warm.loc["tenant-aurora", "Warm Storage Consumed"] == 900 * GIB
    assert warm.loc["tenant-aurora", "Warm Data Written"] == 1250 * GIB
    assert warm.loc["tenant-beacon", "Warm Logical Usage"] == 1400 * GIB

    expected_csv = {
        "warm_granular.csv", "warm_summary.csv", "replica_granular.csv",
        "replica_summary.csv", "cold_granular.csv", "cold_summary.csv",
        "vault_granular.csv", "vault_summary.csv",
    }
    assert {path.name for path in (tmp_path / "csv").iterdir()} == expected_csv
    assert "Time (UTC)" in pd.read_csv(tmp_path / "csv" / "warm_granular.csv").columns


def test_csv_export_neutralizes_spreadsheet_formulas(tmp_path: Path):
    frame = pd.DataFrame({"Job Name": ["=unsafe()"], "Time": [1000]})
    data = CSVData(*([frame] * 8))
    data.save_as_csv_files(str(tmp_path))
    exported = pd.read_csv(tmp_path / "warm_granular.csv")
    assert exported.loc[0, "Job Name"] == "'=unsafe()"
    assert exported.loc[0, "Time (UTC)"] == "1970-01-01T00:00:01Z"
