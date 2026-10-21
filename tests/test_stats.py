import pandas as pd
import pytest

from cohesity_rest_helper import (
    CohesityAPIError,
    CohesityClusterObject,
    CohesityProtectionStatsObject,
    CohesityProtectionVaultObject,
    CohesityTenants,
    CSVData,
)
from tests.conftest import HOST, make_response


def stats(cls=CohesityProtectionStatsObject):
    obj = cls("synthetic-token", HOST)
    obj.api_payload["tenantIds"] = ["tenant-a/"]
    obj.start_time, obj.end_time = 0, 3000
    return obj


def test_headers_and_epoch_helpers():
    obj = stats()
    assert obj.headers["authorization"] == "bearer synthetic-token"
    assert obj.convert_epoch_msecs(1000) == obj.convert_epoch_usecs(1000 * 1000)


def test_tenants_cluster_vaults(mock_get):
    assert stats(CohesityTenants).get_tenants() == ["tenant-a/", "tenant-b/"]
    assert stats(CohesityClusterObject).get_cluster_info() == {"name": "example-cluster"}
    assert stats(CohesityProtectionVaultObject).get_vaults()[0]["name"] == "vault-one"
    assert all(c.kwargs["verify"] is True for c in mock_get.call_args_list)


def test_non_200_raises(mock_get):
    mock_get.side_effect = lambda *a, **k: make_response(500, {})
    with pytest.raises(CohesityAPIError) as err:
        stats(CohesityTenants).get_tenants()
    assert err.value.status_code == 500


def test_warm_pipeline(mock_get):
    obj = stats()
    obj.get_protection_jobs()
    obj.get_storage_consumed()
    obj.get_data_written()
    obj.get_logical_usage()
    assert list(obj.df_warm.columns) == [
        "Tenant Name", "Tenant ID", "Job Name", "Time",
        "Warm Storage Consumed", "Warm Data Written", "Warm Logical Usage"]
    assert len(obj.df_warm) == 4
    # latest point per job (20 + 7) summed per tenant
    assert obj.df_sum.loc[0, "Warm Storage Consumed"] == 27
    assert obj.df_sum.loc[0, "Warm Data Written"] == 27
    assert obj.df_sum.loc[0, "Warm Logical Usage"] == 27


def test_replica_and_cold(mock_get):
    obj = stats()
    obj.get_protection_jobs()
    obj.get_replica_protection_jobs()
    obj.view_storage_info()
    obj.get_replica_storage_consumed()
    obj.get_replica_data_written()
    obj.get_view_storage_consumed()
    obj.get_view_data_written()
    assert obj.df_replica_sum.loc[0, "Replica Data Written"] == 27
    assert obj.df_view_sum.loc[0, "Cold Storage Consumed"] == 27
    assert "Cold Data Written" in obj.df_view.columns
    consumer_calls = [c for c in mock_get.call_args_list if c.args == () and
                      c.kwargs["url"].endswith("/stats/consumers")]
    assert {c.kwargs["params"]["consumerType"] for c in consumer_calls} == {
        "kProtectionRuns", "kReplicationRuns", "kViews"}


def test_vault_consumed(mock_get):
    obj = stats()
    obj.api_payload["vaults"] = stats(CohesityProtectionVaultObject).get_vaults()
    obj.get_vault_consumed()
    assert obj.df_vault_sum.loc[0, "Vault Consumed"] == 60
    assert list(obj.df_vault.columns) == [
        "Archive Name", "Archive Provider", "Time", "Vault Consumed"]


def test_window_required(mock_get):
    obj = CohesityProtectionStatsObject("t", HOST)
    obj.api_payload["tenantIds"] = []
    obj.api_payload["tenants"] = {}
    with pytest.raises(ValueError):
        obj.get_storage_consumed()


def test_excel_export(tmp_path):
    frame = pd.DataFrame({"a": [1]})
    data = CSVData(*([frame] * 8))
    out = tmp_path / "out.xlsx"
    data.save_as_excel(str(out))
    assert set(pd.read_excel(out, sheet_name=None)) == {
        "Warm Granular", "Warm Sum", "Replica Granular", "Replica Sum",
        "Cold Granular", "Cold Sum", "Frozen Granular", "Frozen Sum"}


def test_excel_export_neutralizes_formula_like_names(tmp_path):
    frame = pd.DataFrame({"Tenant Name": ["=1+1", "+SUM(A1:A2)", "safe-name"]})
    data = CSVData(*([frame] * 8))
    out = tmp_path / "safe.xlsx"
    data.save_as_excel(str(out))
    values = pd.read_excel(out, sheet_name="Warm Granular")["Tenant Name"].tolist()
    assert values == ["'=1+1", "'+SUM(A1:A2)", "safe-name"]
