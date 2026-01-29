"""Fetch currency exchange rates from Frankfurter API (ECB reference rates)."""
import json
import ssl
import urllib.error
import urllib.request
from typing import Optional

FRANKFURTER_BASE = "https://api.frankfurter.dev/v1/latest"
TIMEOUT_SECONDS = 15
USER_AGENT = "PortfolioTracker/1.0 (https://github.com)"


def fetch_rates(currencies: list[str]) -> tuple[Optional[dict[str, float]], Optional[str], Optional[str]]:
    """Fetch latest EUR-based exchange rates for the given currencies.

    Uses Frankfurter API (no API key, free). EUR is the base; rates are
    "units per 1 EUR". Currencies not supported by the API are
    simply not included in the returned dict.

    Args:
        currencies: List of currency codes (e.g. ["USD", "GBP"]). EUR is ignored.

    Returns:
        On success: (rates_dict, date_str, None) where rates_dict maps currency -> rate
            and date_str is the API date (e.g. "2024-11-25").
        On failure: (None, None, error_message) e.g. "No internet connection" or
            "Service temporarily unavailable".
    """
    symbols = [c for c in currencies if c.upper() != "EUR"]
    if not symbols:
        return {}, "", None

    symbols_str = ",".join(symbols)
    url = f"{FRANKFURTER_BASE}?symbols={symbols_str}"

    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    # Use default SSL context (system certs). Helps on Windows where
    # SSL verification can fail if certs are not loaded.
    ssl_context = ssl.create_default_context()

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS, context=ssl_context) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        if "timed out" in str(e).lower() or isinstance(getattr(e, "reason", None), TimeoutError):
            return None, None, "Request timed out. Check your internet connection."
        reason = getattr(e, "reason", e)
        detail = str(reason) if reason else str(e)
        if not detail:
            detail = "Unknown error"
        return None, None, f"Could not reach rate service.\n\nDetails: {detail}"
    except TimeoutError:
        return None, None, "Request timed out. Check your internet connection."
    except json.JSONDecodeError:
        return None, None, "Invalid response from rate service."
    except OSError as e:
        return None, None, f"Network error: {e}"

    if not isinstance(data, dict):
        return None, None, "Invalid response from rate service."

    rates = data.get("rates")
    if not isinstance(rates, dict):
        return None, None, "Invalid response from rate service."

    date_str = data.get("date", "")
    if not isinstance(date_str, str):
        date_str = ""

    result = {}
    for k, v in rates.items():
        try:
            result[k] = float(v)
        except (TypeError, ValueError):
            continue
    return result, date_str, None
