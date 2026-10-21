from unittest import mock

import pytest

from cohesity_rest_helper import CohesityAPIError, CohesityUserAuthentication
from tests.conftest import HOST, make_response


def test_token_success_verifies_tls_by_default():
    auth = CohesityUserAuthentication("https://" + HOST + "/")
    assert auth.cluster_url == HOST
    ok = make_response(201, {"accessToken": "tok"})
    with mock.patch("requests.post", return_value=ok) as post:
        assert auth.get_bearer_token("svc-user", "not-a-real-password", "LOCAL") == "tok"
    kwargs = post.call_args.kwargs
    assert kwargs["verify"] is True
    assert kwargs["timeout"] == 60
    assert kwargs["url"] == f"https://{HOST}/irisservices/api/v1/public/accessTokens"
    assert kwargs["json"]["domain"] == "LOCAL"


def test_custom_ca_bundle_passed_through():
    auth = CohesityUserAuthentication(HOST, verify="/etc/ssl/example-ca.pem")
    with mock.patch("requests.post", return_value=make_response(201, {"accessToken": "t"})) as post:
        auth.get_bearer_token("u", "p", "LOCAL")
    assert post.call_args.kwargs["verify"] == "/etc/ssl/example-ca.pem"


def test_failure_raises_without_leaking_credentials():
    auth = CohesityUserAuthentication(HOST)
    with mock.patch("requests.post", return_value=make_response(401, {})):
        with pytest.raises(CohesityAPIError) as err:
            auth.get_bearer_token("svc-user", "hunter2-synthetic", "LOCAL")
    assert err.value.status_code == 401
    assert "hunter2-synthetic" not in str(err.value)
    assert isinstance(err.value, ValueError)
