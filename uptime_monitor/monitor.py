"""
Uptime monitor for TED Bot backend.

Polls the health endpoint at a configurable interval and sends Telegram
notifications when the service goes down or recovers.
"""

import asyncio
import os
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

TARGET_URL: str = os.environ.get("MONITOR_TARGET_URL", "http://backend:8000/api/v1/health")
CHECK_INTERVAL: int = int(os.environ.get("MONITOR_CHECK_INTERVAL", "60"))   # seconds
REQUEST_TIMEOUT: int = int(os.environ.get("MONITOR_REQUEST_TIMEOUT", "10"))  # seconds
CONSECUTIVE_FAILURES: int = int(os.environ.get("MONITOR_FAILURES_BEFORE_ALERT", "2"))
SERVICE_NAME: str = os.environ.get("MONITOR_SERVICE_NAME", "TED Bot Backend")

TELEGRAM_BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID: str = os.environ["TELEGRAM_CHAT_ID"]

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# ── State ─────────────────────────────────────────────────────────────────────

@dataclass
class MonitorState:
    is_up: bool = True
    failure_streak: int = 0
    last_down_at: Optional[float] = None
    downtime_notified: bool = False


# ── Telegram ──────────────────────────────────────────────────────────────────

async def send_telegram(client: httpx.AsyncClient, text: str) -> None:
    try:
        resp = await client.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        resp.raise_for_status()
        log.info("Telegram notification sent")
    except Exception as exc:
        log.error("Failed to send Telegram notification: %s", exc)


def fmt_duration(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


# ── Health check ──────────────────────────────────────────────────────────────

async def check_health(client: httpx.AsyncClient) -> tuple[bool, str]:
    """Return (is_healthy, reason)."""
    try:
        resp = await client.get(TARGET_URL, timeout=REQUEST_TIMEOUT)
        if resp.status_code < 500:
            return True, f"HTTP {resp.status_code}"
        return False, f"HTTP {resp.status_code}"
    except httpx.TimeoutException:
        return False, "request timed out"
    except httpx.ConnectError:
        return False, "connection refused"
    except Exception as exc:
        return False, str(exc)


# ── Monitor loop ──────────────────────────────────────────────────────────────

async def run() -> None:
    state = MonitorState()
    log.info("Uptime monitor started — checking %s every %ds", TARGET_URL, CHECK_INTERVAL)

    async with httpx.AsyncClient() as client:
        # Send startup message
        await send_telegram(client, f"🟢 <b>{SERVICE_NAME}</b> uptime monitor started.\nWatching: <code>{TARGET_URL}</code>")

        while True:
            healthy, reason = await check_health(client)

            if healthy:
                if not state.is_up and state.downtime_notified:
                    # Recovery
                    duration = fmt_duration(time.time() - state.last_down_at)
                    await send_telegram(
                        client,
                        f"✅ <b>{SERVICE_NAME}</b> is back online!\nDowntime: {duration}",
                    )
                    log.info("Service recovered after %s", duration)

                state.is_up = True
                state.failure_streak = 0
                state.last_down_at = None
                state.downtime_notified = False
                log.debug("Health check OK (%s)", reason)

            else:
                state.failure_streak += 1
                log.warning("Health check failed (%s) — streak: %d", reason, state.failure_streak)

                if state.failure_streak >= CONSECUTIVE_FAILURES and not state.downtime_notified:
                    state.is_up = False
                    state.last_down_at = state.last_down_at or time.time()
                    state.downtime_notified = True

                    await send_telegram(
                        client,
                        f"🔴 <b>{SERVICE_NAME}</b> is DOWN!\n"
                        f"Reason: <code>{reason}</code>\n"
                        f"Endpoint: <code>{TARGET_URL}</code>",
                    )
                    log.error("Service is DOWN — notified via Telegram")

                elif state.failure_streak == 1:
                    state.last_down_at = state.last_down_at or time.time()

            await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(run())
