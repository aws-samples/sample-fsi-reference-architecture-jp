"""HTTP client for the BOJ Time-Series Statistics API.

Wraps all three API endpoints (Code, Layer, Metadata) with:
- Automatic gzip handling
- Exponential backoff with jitter (min 2 s base)
- Automatic pagination via NEXTPOSITION
- Rate-limiting between consecutive requests

Uses only Python standard library (urllib.request) for HTTP access.
"""

from __future__ import annotations

import gzip
import json as _json
import logging
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .constants import (
    API_MAX_SERIES_PER_REQUEST,
    DEFAULT_MAX_PAGES,
    DEFAULT_REQUEST_INTERVAL,
    ENDPOINTS,
    VALID_FREQUENCIES,
    VALID_LANGS,
)
from .exceptions import (
    BojApiError,
    BojClientNetworkError,
    BojClientNotFoundError,
    BojClientValidationError,
)
from .models import (
    ApiParams,
    ApiStatus,
    DataPoint,
    DataResponse,
    MetadataResponse,
    SeriesData,
    SeriesMeta,
)

logger = logging.getLogger(__name__)

# BOJ message IDs that indicate "no data" (not a hard error)
_NO_DATA_MESSAGE_IDS = {"M181030I"}

# BOJ status codes that are retryable
_RETRYABLE_STATUS_CODES = {500, 503}

# Maximum retry attempts
_MAX_RETRIES = 3


class BojClient:
    """Client for the BOJ Time-Series Statistics Search Site API.

    Args:
        lang: Default language ('jp' or 'en').
        max_pages: Maximum pagination requests per query.
        request_interval: Base interval between requests in seconds.
        timeout: HTTP request timeout in seconds.
    """

    def __init__(
        self,
        lang: str = "jp",
        max_pages: int = DEFAULT_MAX_PAGES,
        request_interval: float = DEFAULT_REQUEST_INTERVAL,
        timeout: float = 30.0,
        accept_gzip: bool = True,
    ):
        if lang not in VALID_LANGS:
            raise BojClientValidationError(f"Invalid lang '{lang}'. Must be one of: {VALID_LANGS}")
        self.lang = lang
        self.max_pages = max_pages
        self.request_interval = request_interval
        self.timeout = timeout
        # Request gzip-compressed responses. Disable to fetch uncompressed
        # (e.g. for testing that both paths return identical data).
        self.accept_gzip = accept_gzip

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_data_by_code(
        self,
        db: str,
        codes: list[str],
        start_date: str = "",
        end_date: str = "",
    ) -> DataResponse:
        """Fetch time-series data via the Code API.

        Automatically paginates and splits requests when codes exceed 250.
        """
        self._validate_db(db)
        if not codes:
            raise BojClientValidationError("At least one series code is required.")

        all_series: list[SeriesData] = []
        last_status: ApiStatus | None = None
        last_params: ApiParams | None = None

        # Split codes into chunks of 250
        for i in range(0, len(codes), API_MAX_SERIES_PER_REQUEST):
            chunk = codes[i : i + API_MAX_SERIES_PER_REQUEST]
            params: dict[str, str] = {
                "format": "json",
                "lang": self.lang,
                "db": db,
                "code": ",".join(chunk),
            }
            if start_date:
                params["startDate"] = start_date
            if end_date:
                params["endDate"] = end_date

            response = self._paginated_request("code", params)
            for page in response:
                parsed = self._parse_data_response(page)
                last_status = parsed.status
                last_params = parsed.params
                all_series.extend(parsed.series)

            if i + API_MAX_SERIES_PER_REQUEST < len(codes):
                self._wait()

        return DataResponse(
            status=last_status or ApiStatus(status=200, message_id="", message=""),
            params=last_params or ApiParams(),
            series=all_series,
        )

    def get_data_by_layer(
        self,
        db: str,
        layer: str,
        frequency: str,
        start_date: str = "",
        end_date: str = "",
    ) -> DataResponse:
        """Fetch time-series data via the Layer API."""
        self._validate_db(db)
        freq_upper = frequency.upper()
        if freq_upper not in VALID_FREQUENCIES:
            raise BojClientValidationError(
                f"Invalid frequency '{frequency}'. Must be one of: {VALID_FREQUENCIES}"
            )

        params: dict[str, str] = {
            "format": "json",
            "lang": self.lang,
            "db": db,
            "layer": layer,
            "frequency": freq_upper,
        }
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        all_series: list[SeriesData] = []
        last_status: ApiStatus | None = None
        last_params: ApiParams | None = None

        for page in self._paginated_request("layer", params):
            parsed = self._parse_data_response(page)
            last_status = parsed.status
            last_params = parsed.params
            all_series.extend(parsed.series)

        return DataResponse(
            status=last_status or ApiStatus(status=200, message_id="", message=""),
            params=last_params or ApiParams(),
            series=all_series,
        )

    def get_metadata(self, db: str) -> MetadataResponse:
        """Fetch metadata (series list and attributes) via the Metadata API."""
        self._validate_db(db)
        params: dict[str, str] = {
            "format": "json",
            "lang": self.lang,
            "db": db,
        }
        data = self._request("metadata", params)
        return self._parse_metadata_response(data)

    def search_series(self, db: str, keywords: list[str]) -> list[SeriesMeta]:
        """Search series by keyword against series names.

        Fetches metadata for the given DB and filters locally by keyword
        match (case-insensitive, OR logic) on series name fields.

        If db is "all", searches across all known databases. Each DB is
        queried sequentially with rate limiting between requests.
        """
        if db.lower() == "all":
            return self._search_all_dbs(keywords)

        meta = self.get_metadata(db)
        return self._filter_series(meta.series, keywords)

    def _search_all_dbs(self, keywords: list[str]) -> list[SeriesMeta]:
        """Search across all databases in DB_CATALOG."""
        from .constants import DB_CATALOG

        all_results: list[SeriesMeta] = []
        for i, db_name in enumerate(DB_CATALOG):
            if i > 0:
                self._wait()
            try:
                meta = self.get_metadata(db_name)
                matched = self._filter_series(meta.series, keywords)
                # Tag each result with its DB name in notes field for identification
                for s in matched:
                    if not s.notes_jp:
                        s.notes_jp = f"DB:{db_name}"
                    if not s.notes_en:
                        s.notes_en = f"DB:{db_name}"
                all_results.extend(matched)
            except (BojApiError, BojClientNetworkError) as exc:
                logger.warning("Skipping DB '%s': %s", db_name, exc)
        return all_results

    @staticmethod
    def _filter_series(series: list[SeriesMeta], keywords: list[str]) -> list[SeriesMeta]:
        """Filter series by keyword match on name fields (OR, case-insensitive)."""
        kw_lower = [k.lower() for k in keywords]
        results: list[SeriesMeta] = []
        for s in series:
            name_text = f"{s.name_jp} {s.name_en}".lower()
            if any(k in name_text for k in kw_lower):
                results.append(s)
        return results

    def get_latest(
        self,
        db: str,
        codes: list[str],
    ) -> DataResponse:
        """Fetch only the most recent data point for each series."""
        meta = self.get_metadata(db)
        code_set = {c.upper() for c in codes}
        # Find the latest end period for each requested code
        end_dates: dict[str, str] = {}
        for s in meta.series:
            if s.series_code.upper() in code_set:
                end_dates[s.series_code] = s.end_period

        if not end_dates:
            raise BojClientNotFoundError(
                f"None of the specified codes found in DB '{db}'."
            )

        # Use the latest end_period as both start and end to get just the last point
        response = self.get_data_by_code(db, codes)
        # Trim to only the last data point per series
        for series in response.series:
            if series.data_points:
                non_null = [dp for dp in series.data_points if dp.value is not None]
                if non_null:
                    series.data_points = [non_null[-1]]
                else:
                    series.data_points = [series.data_points[-1]]
        return response

    # ------------------------------------------------------------------
    # Internal HTTP helpers
    # ------------------------------------------------------------------

    def _request(self, endpoint_key: str, params: dict[str, str]) -> dict[str, Any]:
        """Execute a single API request with retry logic."""
        base_url = ENDPOINTS[endpoint_key]
        full_url = f"{base_url}?{urllib.parse.urlencode(params)}"
        scheme = urllib.parse.urlparse(full_url).scheme
        if scheme not in ("http", "https"):
            raise ValueError(f"unsupported URL scheme '{scheme}': {full_url}")
        headers = {"Accept-Encoding": "gzip"} if self.accept_gzip else {}
        req = urllib.request.Request(full_url, headers=headers)  # noqa: S310 - scheme validated above
        last_exc: Exception | None = None

        for attempt in range(_MAX_RETRIES + 1):
            if attempt > 0:
                backoff = self._backoff_delay(attempt)
                logger.info("Retry %d/%d after %.1fs", attempt, _MAX_RETRIES, backoff)
                time.sleep(backoff)

            http_status = 0
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310 - scheme validated above  # nosec B310
                    http_status = resp.status
                    raw = resp.read()
                    if resp.headers.get("Content-Encoding") == "gzip":
                        raw = gzip.decompress(raw)
                    body = raw.decode("utf-8")
            except urllib.error.HTTPError as exc:
                http_status = exc.code
                try:
                    raw = exc.read()
                    if exc.headers.get("Content-Encoding") == "gzip":
                        raw = gzip.decompress(raw)
                    body = raw.decode("utf-8")
                except Exception:
                    last_exc = BojClientNetworkError(f"Network error: {exc}")
                    logger.warning("Network error (attempt %d): %s", attempt + 1, exc)
                    continue
            except (urllib.error.URLError, OSError) as exc:
                last_exc = BojClientNetworkError(f"Network error: {exc}")
                logger.warning("Network error (attempt %d): %s", attempt + 1, exc)
                continue

            try:
                data: dict[str, Any] = _json.loads(body)
            except ValueError:
                last_exc = BojApiError(
                    f"Invalid JSON response (HTTP {http_status})",
                    status_code=http_status,
                )
                continue

            boj_status = int(data.get("STATUS", http_status))
            msg_id = str(data.get("MESSAGEID", ""))
            msg = str(data.get("MESSAGE", ""))

            if boj_status == 200:
                if msg_id in _NO_DATA_MESSAGE_IDS:
                    resultset = data.get("RESULTSET", [])
                    if not resultset:
                        raise BojClientNotFoundError(
                            f"No data found: {msg}", message_id=msg_id, api_message=msg
                        )
                return data

            if boj_status in _RETRYABLE_STATUS_CODES:
                last_exc = BojApiError(
                    f"API error ({boj_status}): [{msg_id}] {msg}",
                    status_code=boj_status,
                    message_id=msg_id,
                    api_message=msg,
                )
                logger.warning(
                    "Retryable API error %d (attempt %d): %s",
                    boj_status,
                    attempt + 1,
                    msg,
                )
                continue

            raise BojApiError(
                f"API error ({boj_status}): [{msg_id}] {msg}",
                status_code=boj_status,
                message_id=msg_id,
                api_message=msg,
            )

        raise last_exc  # type: ignore[misc]

    def _paginated_request(
        self, endpoint_key: str, params: dict[str, str]
    ) -> list[dict[str, Any]]:
        """Execute paginated requests, following NEXTPOSITION."""
        pages: list[dict[str, Any]] = []
        current_params = dict(params)

        for page_num in range(self.max_pages):
            if page_num > 0:
                self._wait()

            data = self._request(endpoint_key, current_params)
            pages.append(data)

            next_pos = data.get("NEXTPOSITION")
            if next_pos is None or next_pos == "null" or next_pos == "":
                break

            current_params["startPosition"] = str(next_pos)
            logger.info("Pagination: page %d, next position %s", page_num + 1, next_pos)
        else:
            logger.warning("Reached max pages limit (%d)", self.max_pages)

        return pages

    def _wait(self) -> None:
        """Wait with jitter between requests to avoid overloading the API."""
        jitter = random.uniform(-1.0, 1.0)  # noqa: S311
        delay = max(1.0, self.request_interval + jitter)
        time.sleep(delay)

    @staticmethod
    def _backoff_delay(attempt: int) -> float:
        """Calculate exponential backoff delay with jitter.

        Base is 2 seconds ± 1 second random, then doubles each attempt.
        """
        base = 2.0 + random.uniform(-1.0, 1.0)  # noqa: S311
        return base * (2 ** (attempt - 1))

    @staticmethod
    def _validate_db(db: str) -> None:
        if not db:
            raise BojClientValidationError("DB name is required.")

    # ------------------------------------------------------------------
    # Response parsers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_status(data: dict[str, Any]) -> ApiStatus:
        return ApiStatus(
            status=int(data.get("STATUS", 0)),
            message_id=str(data.get("MESSAGEID", "")),
            message=str(data.get("MESSAGE", "")),
            date=str(data.get("DATE", "")),
        )

    @staticmethod
    def _parse_params(data: dict[str, Any]) -> ApiParams:
        """Parse PARAMETER block (Code/Layer APIs nest params under PARAMETER key)."""
        p = data.get("PARAMETER", data)
        return ApiParams(
            format=str(p.get("FORMAT", "")),
            lang=str(p.get("LANG", "")),
            db=str(p.get("DB", "")),
            start_date=str(p.get("STARTDATE", "")),
            end_date=str(p.get("ENDDATE", "")),
            start_position=str(p.get("STARTPOSITION", "")),
            layer1=str(p.get("LAYER1", "")),
            layer2=str(p.get("LAYER2", "")),
            layer3=str(p.get("LAYER3", "")),
            layer4=str(p.get("LAYER4", "")),
            layer5=str(p.get("LAYER5", "")),
            frequency=str(p.get("FREQUENCY", "")),
        )

    @staticmethod
    def _parse_data_response(data: dict[str, Any]) -> DataResponse:
        """Parse Code API / Layer API JSON response into DataResponse.

        Actual API structure:
          - Top-level: STATUS, MESSAGEID, MESSAGE, DATE, PARAMETER, NEXTPOSITION, RESULTSET
          - PARAMETER: {FORMAT, LANG, DB, STARTDATE, ENDDATE, STARTPOSITION, ...}
          - RESULTSET: [{SERIES_CODE, NAME_OF_TIME_SERIES_J, UNIT_J, FREQUENCY,
                         CATEGORY_J, LAST_UPDATE, VALUES: {SURVEY_DATES: [...], VALUES: [...]}}]
        """
        status = BojClient._parse_status(data)
        params = BojClient._parse_params(data)

        next_pos_raw = data.get("NEXTPOSITION")
        next_position = int(next_pos_raw) if next_pos_raw not in (None, "", "null") else None

        series_list: list[SeriesData] = []
        for item in data.get("RESULTSET", []):
            data_points: list[DataPoint] = []
            values_block = item.get("VALUES", {})
            if isinstance(values_block, dict):
                dates = values_block.get("SURVEY_DATES", [])
                vals = values_block.get("VALUES", [])
                for d, v in zip(dates, vals):
                    data_points.append(DataPoint(
                        date=str(d),
                        value=str(v) if v is not None else None,
                    ))

            series_list.append(SeriesData(
                series_code=str(item.get("SERIES_CODE", "")),
                name=str(
                    item.get("NAME_OF_TIME_SERIES_J", "")
                    or item.get("NAME_OF_TIME_SERIES", "")
                ),
                unit=str(item.get("UNIT_J", "") or item.get("UNIT", "")),
                frequency=str(item.get("FREQUENCY", "")),
                category=str(item.get("CATEGORY_J", "") or item.get("CATEGORY", "")),
                last_update=str(item.get("LAST_UPDATE", "")),
                data_points=data_points,
            ))

        return DataResponse(
            status=status, params=params, next_position=next_position, series=series_list
        )

    @staticmethod
    def _parse_metadata_response(data: dict[str, Any]) -> MetadataResponse:
        """Parse Metadata API JSON response into MetadataResponse.

        Actual API structure:
          - Top-level: STATUS, MESSAGEID, MESSAGE, DATE, DB, RESULTSET
          - RESULTSET: [{SERIES_CODE, NAME_OF_TIME_SERIES_J, ..., LAYER1..5, ...}]
        """
        status = BojClient._parse_status(data)
        series_list: list[SeriesMeta] = []
        for item in data.get("RESULTSET", []):
            series_list.append(SeriesMeta(
                series_code=str(item.get("SERIES_CODE", "")),
                name_jp=str(item.get("NAME_OF_TIME_SERIES_J", "")),
                name_en=str(item.get("NAME_OF_TIME_SERIES", "")),
                unit_jp=str(item.get("UNIT_J", "")),
                unit_en=str(item.get("UNIT", "")),
                frequency=str(item.get("FREQUENCY", "")),
                category_jp=str(item.get("CATEGORY_J", "")),
                category_en=str(item.get("CATEGORY", "")),
                layer1=str(item.get("LAYER1", "")),
                layer2=str(item.get("LAYER2", "")),
                layer3=str(item.get("LAYER3", "")),
                layer4=str(item.get("LAYER4", "")),
                layer5=str(item.get("LAYER5", "")),
                start_period=str(item.get("START_OF_THE_TIME_SERIES", "")),
                end_period=str(item.get("END_OF_THE_TIME_SERIES", "")),
                last_update=str(item.get("LAST_UPDATE", "")),
                notes_jp=str(item.get("NOTES_J", "")),
                notes_en=str(item.get("NOTES", "")),
            ))

        return MetadataResponse(
            status=status,
            db=str(data.get("DB", "")),
            series=series_list,
        )
