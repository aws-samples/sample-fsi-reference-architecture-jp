"""Tests for exception hierarchy."""

from boj_statistics.exceptions import (
    BojApiError,
    BojClientError,
    BojClientNetworkError,
    BojClientNotFoundError,
    BojClientValidationError,
)


class TestExceptionHierarchy:
    def test_all_inherit_from_base(self):
        assert issubclass(BojClientValidationError, BojClientError)
        assert issubclass(BojClientNotFoundError, BojClientError)
        assert issubclass(BojApiError, BojClientError)
        assert issubclass(BojClientNetworkError, BojClientError)

    def test_base_is_exception(self):
        assert issubclass(BojClientError, Exception)

    def test_api_error_attributes(self):
        exc = BojApiError("test", status_code=400, message_id="M181005E", api_message="DB名が正しくありません。")
        assert exc.status_code == 400
        assert exc.message_id == "M181005E"
        assert exc.api_message == "DB名が正しくありません。"
        assert str(exc) == "test"

    def test_not_found_attributes(self):
        exc = BojClientNotFoundError("no data", message_id="M181030I", api_message="該当データなし")
        assert exc.message_id == "M181030I"
        assert exc.api_message == "該当データなし"

    def test_catch_by_base(self):
        try:
            raise BojApiError("api error", status_code=500)
        except BojClientError as e:
            assert isinstance(e, BojApiError)
