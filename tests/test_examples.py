"""Run each example end to end against the offline fake cluster in example_fakes.py."""
import importlib

import pandas as pd
import pytest

from tests.example_fakes import (
    FAKE_PASSWORD,
    FAKE_TOKEN,
    FAKE_USER,
    GIB,
    HOST,
    patch_cluster,
)

EXAMPLES = ["auth_cluster_info", "tenants_and_vaults", "warm_storage",
            "replica_and_view_tiers", "vault_consumption", "full_tier_workbook"]


@pytest.fixture(autouse=True)
def cluster_env(monkeypatch):
    monkeypatch.setenv("COHESITY_HOST", HOST)
    monkeypatch.setenv("COHESITY_USER", FAKE_USER)
    monkeypatch.setenv("COHESITY_PASSWORD", FAKE_PASSWORD)
    monkeypatch.delenv("COHESITY_DOMAIN", raising=False)
    monkeypatch.delenv("COHESITY_CA_BUNDLE", raising=False)


def run(name, argv=()):
    module = importlib.import_module(name)
    with patch_cluster() as (post, get):
        code = module.main(list(argv))
    return code, post, get


def assert_safe_requests(post, get):
    """TLS stays on, every call has a timeout, and the token is sent only as a header."""
    for call in [*post.call_args_list, *get.call_args_list]:
        assert call.kwargs["verify"] is True
        assert call.kwargs["timeout"] == 60
    assert post.call_args.kwargs["url"].startswith(f"https://{HOST}/")
    assert post.call_args.kwargs["json"]["password"] == FAKE_PASSWORD


def test_every_example_has_a_test():
    import pathlib
    here = pathlib.Path(__file__).resolve().parents[1] / "examples"
    scripts = {p.stem for p in here.glob("*.py")} - {"__init__", "example_support",
                                                      "tenant_storage_report"}
    assert scripts == set(EXAMPLES)


def test_auth_cluster_info(capsys):
    code, post, get = run("auth_cluster_info")
    out = capsys.readouterr().out
    assert code == 0
    assert "demo-cluster" in out and "4242" in out and "0.0.0-synthetic" in out
    assert FAKE_USER not in out and FAKE_PASSWORD not in out and FAKE_TOKEN not in out
    assert_safe_requests(post, get)


def test_tenants_and_vaults(capsys):
    code, post, get = run("tenants_and_vaults")
    out = capsys.readouterr().out
    assert code == 0
    assert "2 tenant(s)" in out and "tenant-delta/" in out and "tenant-ember/" in out
    assert "vault-demo-a (id 71, provider kS3)" in out
    assert "vault-demo-b (id 72, provider kAzure)" in out
    assert_safe_requests(post, get)


def test_warm_storage(capsys):
    code, post, get = run("warm_storage", ["--days", "7"])
    out = capsys.readouterr().out
    assert code == 0
    assert "last 7 day(s)" in out
    # delta = jobs 11 + 12; ember = job 21 (latest data point per job)
    assert "tenant-delta/: physical 150.0 GiB, written 220.0 GiB, logical 440.0 GiB" in out
    assert "tenant-ember/: physical 80.0 GiB, written 90.0 GiB, logical 200.0 GiB" in out
    assert "6 daily data points" in out
    assert_safe_requests(post, get)
    windows = {(c.kwargs["params"]["endTimeMsecs"] - c.kwargs["params"]["startTimeMsecs"])
               for c in get.call_args_list if "startTimeMsecs" in (c.kwargs["params"] or {})}
    assert windows == {7 * 86_400_000}


def test_replica_and_view_tiers(capsys):
    code, post, get = run("replica_and_view_tiers")
    out = capsys.readouterr().out
    assert code == 0
    assert "tenant-delta/: consumed 65.0 GiB, written 65.0 GiB" in out
    assert "tenant-ember/: consumed 30.0 GiB, written 30.0 GiB" in out
    assert "tenant-delta/: consumed 12.0 GiB, written 15.0 GiB" in out
    assert "tenant-ember/: consumed 7.0 GiB, written 9.0 GiB" in out
    assert_safe_requests(post, get)


def test_vault_consumption(capsys):
    code, post, get = run("vault_consumption", ["--days", "14"])
    out = capsys.readouterr().out
    assert code == 0
    assert "vault-demo-a (kS3): 500.0 GiB" in out
    assert "vault-demo-b (kAzure): 320.0 GiB" in out
    assert_safe_requests(post, get)


def test_full_tier_workbook(tmp_path, capsys):
    target = tmp_path / "tiers.xlsx"
    code, post, get = run("full_tier_workbook", ["--output", str(target)])
    assert code == 0
    assert "Wrote" in capsys.readouterr().out
    sheets = pd.read_excel(target, sheet_name=None)
    assert set(sheets) == {"Warm Granular", "Warm Sum", "Replica Granular", "Replica Sum",
                           "Cold Granular", "Cold Sum", "Frozen Granular", "Frozen Sum"}
    warm = sheets["Warm Sum"].set_index("Tenant Name")
    assert warm.loc["tenant-delta/", "Warm Storage Consumed"] == 150 * GIB
    assert sheets["Frozen Sum"]["Vault Consumed"].sum() == 820 * GIB
    assert len(sheets["Cold Granular"]) == 4
    assert_safe_requests(post, get)


def test_workbook_refuses_to_overwrite(tmp_path, capsys):
    target = tmp_path / "tiers.xlsx"
    target.write_text("keep me")
    code, post, _ = run("full_tier_workbook", ["--output", str(target)])
    assert code == 1
    assert "--force" in capsys.readouterr().err
    assert target.read_text() == "keep me"
    post.assert_not_called()


@pytest.mark.parametrize("name", EXAMPLES)
def test_missing_credentials_exit_cleanly(name, monkeypatch, capsys):
    monkeypatch.delenv("COHESITY_PASSWORD")
    module = importlib.import_module(name)
    with patch_cluster() as (post, get), pytest.raises(SystemExit) as stop:
        module.main([])
    assert "COHESITY_PASSWORD" in str(stop.value)
    post.assert_not_called()
    get.assert_not_called()


def test_login_failure_is_reported_without_credentials(monkeypatch, capsys):
    monkeypatch.setenv("COHESITY_PASSWORD", "wrong-synthetic-value")
    code, _, _ = run("auth_cluster_info")
    captured = capsys.readouterr()
    assert code == 1
    assert "HTTP 401" in captured.err
    assert "wrong-synthetic-value" not in captured.out + captured.err


def test_ca_bundle_is_passed_through(monkeypatch):
    monkeypatch.setenv("COHESITY_CA_BUNDLE", "/etc/ssl/example-ca.pem")
    _, post, get = run("auth_cluster_info")
    assert post.call_args.kwargs["verify"] == "/etc/ssl/example-ca.pem"
    assert get.call_args.kwargs["verify"] == "/etc/ssl/example-ca.pem"


def test_same_job_name_in_two_tenants_is_kept_separate():
    from cohesity_rest_helper import CohesityProtectionStatsObject

    frame = pd.DataFrame({
        "Tenant Name": ["a/", "b/"], "Tenant ID": ["a/", "b/"], "Job Name": ["nightly"] * 2,
        "Time": [1, 1], "Cold Storage Consumed": [10, 20]})
    summary = CohesityProtectionStatsObject._latest_sum(frame, "Cold Storage Consumed")
    assert len(summary) == 2


def test_same_job_name_keeps_latest_point_per_tenant():
    from cohesity_rest_helper import CohesityProtectionStatsObject

    frame = pd.DataFrame({
        "Tenant Name": ["a", "a", "b", "b"], "Tenant ID": ["a/", "a/", "b/", "b/"],
        "Job Name": ["nightly"] * 4, "Time": [1, 2, 1, 2],
        "Cold Storage Consumed": [10, 11, 20, 21]})
    summary = CohesityProtectionStatsObject._latest_sum(frame, "Cold Storage Consumed")
    assert dict(zip(summary["Tenant Name"], summary["Cold Storage Consumed"])) == {"a": 11, "b": 21}


def test_distinct_jobs_in_one_tenant_still_sum():
    from cohesity_rest_helper import CohesityProtectionStatsObject

    frame = pd.DataFrame({
        "Tenant Name": ["a", "a"], "Tenant ID": ["a/", "a/"], "Job Name": ["j1", "j2"],
        "Time": [1, 1], "Cold Storage Consumed": [10, 5]})
    summary = CohesityProtectionStatsObject._latest_sum(frame, "Cold Storage Consumed")
    assert summary["Cold Storage Consumed"].tolist() == [15]
