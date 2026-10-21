"""Authentication module: obtain a bearer token from a Cohesity cluster."""
from typing import Union

import requests
from requests.structures import CaseInsensitiveDict

ACCESS_TOKEN_ENDPOINT = "/irisservices/api/v1/public/accessTokens"
DEFAULT_TIMEOUT = 60


class CohesityAPIError(ValueError):
    """Raised when the Cohesity API returns an unexpected status code.

    Subclasses ValueError so callers written against a bare ValueError keep working.
    The message never includes request bodies or credentials.
    """

    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


def normalize_cluster_url(cluster_url: str) -> str:
    """Return a bare host[:port] with any scheme and trailing slash removed."""
    host = str(cluster_url).strip()
    for scheme in ("https://", "http://"):
        if host.lower().startswith(scheme):
            host = host[len(scheme):]
    return host.rstrip("/")


class CohesityUserAuthentication:
    """Cohesity authentication helper.

    Args:
        cluster_url: Cluster host name or address (optionally with port).
        verify: TLS verification. True (default) uses the system trust store; pass a
            path to a CA bundle for clusters with a private CA. Pass False only for
            throwaway lab use; it is never the default.
        timeout: Per-request timeout in seconds.
    """

    def __init__(self, cluster_url: str, verify: Union[bool, str] = True,
                 timeout: int = DEFAULT_TIMEOUT):
        json_type = "application/json"
        self.cluster_url = normalize_cluster_url(cluster_url)
        self.protocol = "https://"
        self.verify = verify
        self.timeout = timeout
        self.headers = CaseInsensitiveDict()
        self.headers["Accept"] = json_type
        self.headers["Content-type"] = json_type

    def get_bearer_token(self, username: str, password: str, domain: str) -> str:
        """Request a bearer token.

        Args:
            username: Cohesity user name.
            password: Cohesity password (never logged or stored on the object).
            domain: Cohesity domain (e.g. "LOCAL").

        Raises:
            CohesityAPIError: If the response status is not 201.

        Returns:
            The access token string.
        """
        url = self.protocol + self.cluster_url + ACCESS_TOKEN_ENDPOINT
        payload = {"username": username, "password": password, "domain": domain}
        response = requests.post(url=url, json=payload, headers=self.headers,
                                 verify=self.verify, timeout=self.timeout)
        if response.status_code != 201:
            raise CohesityAPIError(
                f"Token request failed with HTTP {response.status_code}", response.status_code)
        return response.json()["accessToken"]
