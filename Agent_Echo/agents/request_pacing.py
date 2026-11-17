"""Process-wide request spacing for profiles sharing an endpoint and credential."""

from contextvars import ContextVar
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import math
import threading
import time

from .execution_log import record


request_deadline = ContextVar("echo_request_deadline", default=None)
# Set only for a call with its own deadline (Discovery); it also enables the per-request timeout.
call_deadline = ContextVar("echo_call_deadline", default=None)


class DiscoveryTimeout(RuntimeError):
    """Discovery's own time or call budget cannot cover the request; the run continues."""


def check_request_deadline():
    deadline = request_deadline.get()
    if deadline is not None and time.monotonic() >= deadline:
        if call_deadline.get() is not None:
            raise DiscoveryTimeout("Discovery request deadline reached.")
        raise RuntimeError("Workflow elapsed-time budget exceeded.")


def request_timeout(model_timeout):
    """Seconds left for one provider request when the call has its own deadline; otherwise None."""
    if call_deadline.get() is None:
        return None
    left = max(0.0, request_deadline.get() - time.monotonic())
    return min(left, model_timeout) if model_timeout else left


class RequestPacer:
    def __init__(self, interval):
        self.interval = interval
        self.next_request = 0.0
        self.lock = threading.Lock()

    def acquire(self):
        # Reserve actual starts, not future slots: slow requests cannot create bursts.
        with self.lock:
            wait = self.next_request - time.monotonic()
            if wait > 0:
                record("request_pacing_wait", seconds=round(wait, 3))
            while wait > 0:
                time.sleep(min(wait, 30))
                wait = self.next_request - time.monotonic()
            self.next_request = time.monotonic() + self.interval

    def defer(self, seconds):
        with self.lock:
            self.next_request = max(self.next_request, time.monotonic() + seconds)


_pacers = {}
_pool_lock = threading.Lock()


def shared_pacer(endpoint, key, interval):
    # No credentials are logged or used as plain-text dictionary identifiers.
    identity = (endpoint.rstrip("/"), hashlib.sha256(key.encode()).digest())
    with _pool_lock:
        pacer = _pacers.setdefault(identity, RequestPacer(interval))
        # A second profile cannot weaken the spacing of the same credential.
        with pacer.lock:
            previous = pacer.interval
            pacer.interval = max(previous, interval)
            if pacer.next_request:
                pacer.next_request += pacer.interval - previous
        return pacer


def retry_after_seconds(error, fallback):
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", {}) or {}
    value = headers.get("retry-after") or headers.get("Retry-After")
    if value is not None:
        try:
            seconds = float(value)
        except (TypeError, ValueError):
            try:
                moment = parsedate_to_datetime(value)
                if moment.tzinfo is None:
                    moment = moment.replace(tzinfo=timezone.utc)
                seconds = (moment - datetime.now(timezone.utc)).total_seconds()
            except (TypeError, ValueError, OverflowError):
                return fallback
        if math.isfinite(seconds) and seconds >= 0:
            return max(seconds, fallback)
    return fallback
