"""Offline stand-in for a Cohesity cluster, used by the example tests.

Every name, ID and number is invented. The host uses RFC 5737 documentation space
(192.0.2.0/24); nothing here contacts a network.
"""
from __future__ import annotations

from unittest import mock

from tests.conftest import make_response

HOST = "192.0.2.10"
GIB = 1024 ** 3
START, END = 1_700_000_000_000, 1_700_086_400_000
FAKE_TOKEN = "token-for-tests-only"
FAKE_USER = "example-svc"
FAKE_PASSWORD = "example-not-a-secret"  # nosec - synthetic test value

CLUSTER = {"name": "demo-cluster", "id": 4242, "clusterSoftwareVersion": "0.0.0-synthetic"}
TENANTS = [{"tenantId": "tenant-delta/"}, {"tenantId": "tenant-ember/"}]
VAULTS = [
    {"id": 71, "name": "vault-demo-a", "externalTargetType": "kS3"},
    {"id": 72, "name": "vault-demo-b", "externalTargetType": "kAzure"},
]


def _jobs(tenant, prefix, entity_ids):
    return [{"name": f"{prefix}-{i}",
             "groupList": [{"entityId": eid, "tenantName": tenant, "tenantId": tenant}]}
            for i, eid in enumerate(entity_ids, start=1)]


# Job names are unique here for readable example output. Separate regression tests cover
# identically named jobs in different tenants.
CONSUMERS = {
    ("tenant-delta/", "kProtectionRuns"): _jobs("tenant-delta/", "delta-db", (11, 12)),
    ("tenant-ember/", "kProtectionRuns"): _jobs("tenant-ember/", "ember-files", (21,)),
    ("tenant-delta/", "kReplicationRuns"): _jobs("tenant-delta/", "delta-rep", (31,)),
    ("tenant-ember/", "kReplicationRuns"): _jobs("tenant-ember/", "ember-rep", (32,)),
    ("tenant-delta/", "kViews"): _jobs("tenant-delta/", "delta-view", (41,)),
    ("tenant-ember/", "kViews"): _jobs("tenant-ember/", "ember-view", (42,)),
}

# Latest value in GiB per (entity, metric); an earlier point is 10% lower.
LATEST_GIB = {
    (11, "ChunkBytesPhysical"): 100, (11, "ChunkBytesMorphed"): 150, (11, "LogicalUsage"): 300,
    (12, "ChunkBytesPhysical"): 50, (12, "ChunkBytesMorphed"): 70, (12, "LogicalUsage"): 140,
    (21, "ChunkBytesPhysical"): 80, (21, "ChunkBytesMorphed"): 90, (21, "LogicalUsage"): 200,
    (31, "ChunkBytesPhysical"): 60, (31, "ChunkBytesMorphed"): 65,
    (32, "ChunkBytesPhysical"): 25, (32, "ChunkBytesMorphed"): 30,
    (41, "ChunkBytesPhysical"): 12, (41, "ChunkBytesMorphed"): 15,
    (42, "ChunkBytesPhysical"): 7, (42, "ChunkBytesMorphed"): 9,
    (71, "kMorphedUsageBytes"): 500, (72, "kMorphedUsageBytes"): 320,
}


def _series(entity_id, metric):
    latest = LATEST_GIB[(entity_id, metric)] * GIB
    return [{"timestampMsecs": START, "data": {"int64Value": int(latest * 0.9)}},
            {"timestampMsecs": END, "data": {"int64Value": latest}}]


def fake_post(url, json=None, **kwargs):
    if url.endswith("/accessTokens"):
        ok = json == {"username": FAKE_USER, "password": FAKE_PASSWORD, "domain": "LOCAL"}
        return make_response(201, {"accessToken": FAKE_TOKEN}) if ok else make_response(401, {})
    return make_response(404, {})


def fake_get(url, params=None, headers=None, **kwargs):
    if headers is None or headers.get("Authorization") != "bearer " + FAKE_TOKEN:
        return make_response(401, {})
    params = params or {}
    if url.endswith("/cluster"):
        return make_response(200, CLUSTER)
    if url.endswith("/tenants"):
        return make_response(200, TENANTS)
    if url.endswith("/vaults"):
        return make_response(200, VAULTS)
    if url.endswith("/stats/consumers"):
        key = (params["organizationsIdList"], params["consumerType"])
        return make_response(200, {"statsList": CONSUMERS[key]})
    if url.endswith("/statistics/timeSeriesStats"):
        entity_id = params.get("entityIdList", params.get("entityId"))
        return make_response(200, {"dataPointVec": _series(entity_id, params["metricName"])})
    return make_response(404, {})


def patch_cluster():
    """Patch requests.post/get; returns a context manager yielding (post, get) mocks."""
    post = mock.patch("requests.post", side_effect=fake_post)
    get = mock.patch("requests.get", side_effect=fake_get)

    class _Both:
        def __enter__(self):
            return post.__enter__(), get.__enter__()

        def __exit__(self, *exc):
            get.__exit__(*exc)
            post.__exit__(*exc)

    return _Both()
