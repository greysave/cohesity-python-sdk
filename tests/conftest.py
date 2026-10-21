"""Synthetic fixtures. All names, IDs and numbers are invented; hosts use RFC 2606 / 5737 space."""
from unittest import mock

import pytest

HOST = "cluster.example.invalid"


def make_response(status=200, payload=None):
    resp = mock.Mock()
    resp.status_code = status
    resp.json.return_value = payload
    return resp


STATS_LIST = [{
    "name": "job-alpha",
    "groupList": [{"entityId": 101, "tenantName": "tenant-a/", "tenantId": "tenant-a/"}],
}, {
    "name": "job-beta",
    "groupList": [{"entityId": 102, "tenantName": "tenant-a/", "tenantId": "tenant-a/"}],
}]

POINTS = {
    101: [{"timestampMsecs": 1000, "data": {"int64Value": 10}},
          {"timestampMsecs": 2000, "data": {"int64Value": 20}}],
    102: [{"timestampMsecs": 1000, "data": {"int64Value": 5}},
          {"timestampMsecs": 2000, "data": {"int64Value": 7}}],
}


def fake_get(url, params=None, **kwargs):
    """Route mocked GETs by endpoint."""
    params = params or {}
    if url.endswith("/stats/consumers"):
        return make_response(200, {"statsList": STATS_LIST})
    if url.endswith("/statistics/timeSeriesStats"):
        if "entityIdList" in params:
            return make_response(200, {"dataPointVec": POINTS[params["entityIdList"]]})
        return make_response(200, {"dataPointVec": [
            {"timestampMsecs": 1000, "data": {"int64Value": 50}},
            {"timestampMsecs": 2000, "data": {"int64Value": 60}}]})
    if url.endswith("/tenants"):
        return make_response(200, [{"tenantId": "tenant-a/"}, {"tenantId": "tenant-b/"}])
    if url.endswith("/cluster"):
        return make_response(200, {"name": "example-cluster"})
    if url.endswith("/vaults"):
        return make_response(200, [{"id": 7, "name": "vault-one", "externalTargetType": "kS3"}])
    return make_response(404, {})


@pytest.fixture
def mock_get():
    with mock.patch("requests.get", side_effect=fake_get) as patched:
        yield patched
