"""Exception hierarchy for BOJ Statistics API client.

API error message IDs and messages from the BOJ API are preserved
in exception attributes and never hidden from the caller.
"""


class BojClientError(Exception):
    """Base exception for all BOJ client errors."""


class BojClientValidationError(BojClientError):
    """Client-side parameter validation error (raised before API call)."""


class BojClientNotFoundError(BojClientError):
    """No data found for the given query.

    Attributes:
        message_id: BOJ API message ID (e.g. 'M181030I').
        api_message: Original message text from the API.
    """

    def __init__(self, message: str, message_id: str = "", api_message: str = ""):
        super().__init__(message)
        self.message_id = message_id
        self.api_message = api_message


class BojApiError(BojClientError):
    """API returned a non-200 status or BOJ-level error.

    Attributes:
        status_code: HTTP or BOJ STATUS code.
        message_id: BOJ API message ID (e.g. 'M181090S').
        api_message: Original message text from the API.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 0,
        message_id: str = "",
        api_message: str = "",
    ):
        super().__init__(message)
        self.status_code = status_code
        self.message_id = message_id
        self.api_message = api_message


class BojClientNetworkError(BojClientError):
    """Network-level communication error (connection, timeout, DNS, etc.)."""
