import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("leetcode-reminder")

TIMEZONE_NAME = os.getenv("TIMEZONE", "Asia/Kolkata")
LEETCODE_API = "https://leetcode.com/graphql"
TELEGRAM_API = "https://api.telegram.org"
CHECK_INTERVAL_SECONDS = 20


def get_timezone():
    try:
        return ZoneInfo(TIMEZONE_NAME)
    except Exception as error:
        raise RuntimeError(f"Invalid TIMEZONE value: {TIMEZONE_NAME}") from error


def post_json(url, data):
    request = Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "LeetCodeDailyReminder/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=12) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
        raise RuntimeError("An external API request failed.") from error


def solved_problem_today(username, today, timezone):
    query = """
    query recentAccepted($username: String!, $limit: Int!) {
      recentAcSubmissionList(username: $username, limit: $limit) {
        title
        titleSlug
        timestamp
      }
    }
    """
    result = post_json(
        LEETCODE_API,
        {"query": query, "variables": {"username": username, "limit": 20}},
    )
    if result.get("errors"):
        raise RuntimeError("LeetCode returned a submission error.")
    submissions = (result.get("data") or {}).get("recentAcSubmissionList")
    if submissions is None:
        raise RuntimeError("Could not retrieve public submissions.")

    for submission in submissions:
        try:
            submitted_at = datetime.fromtimestamp(
                int(submission["timestamp"]), tz=timezone.utc
            ).astimezone(timezone)
        except (KeyError, TypeError, ValueError, OSError):
            continue
        if submitted_at.date() == today:
            return True
    return False


def reminder_due(now):
    # First five minutes of each half-hour slot, from 3 PM onward.
    return now.hour >= 15 and now.minute % 30 < 5


def send_reminder(bot_token, chat_id, now):
    message = (
        "🔔 LeetCode Daily Reminder\n\n"
        "You haven't completed your daily coding goal yet.\n"
        "Solve at least one LeetCode problem today.\n\n"
        "Choose any problem:\n"
        "https://leetcode.com/problemset/\n\n"
        f"Reminder time: {now.strftime('%I:%M %p')} IST"
    )
    result = post_json(
        f"{TELEGRAM_API}/bot{bot_token}/sendMessage",
        {"chat_id": chat_id, "text": message},
    )
    if not result.get("ok"):
        raise RuntimeError("Telegram could not send the reminder.")


def check_reminder():
    timezone = get_timezone()
    now = datetime.now(timezone)
    username = os.getenv("LEETCODE_USERNAME", "AravindsLeetcode").strip()
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not username or not bot_token or not chat_id:
        raise RuntimeError("Missing required environment variables.")

    if solved_problem_today(username, now.date(), timezone):
        return {"ok": True, "action": "skip", "reason": "Daily goal completed", "date_ist": now.date().isoformat(), "time_ist": now.strftime("%H:%M:%S")}
    if not reminder_due(now):
        return {"ok": True, "action": "skip", "reason": "No reminder due at this time", "date_ist": now.date().isoformat(), "time_ist": now.strftime("%H:%M:%S")}

    send_reminder(bot_token, chat_id, now)
    logger.info("Reminder sent for %s at %s", now.date().isoformat(), now.strftime("%H:%M:%S"))
    return {"ok": True, "action": "sent", "date_ist": now.date().isoformat(), "time_ist": now.strftime("%H:%M:%S")}


class RequestHandler(BaseHTTPRequestHandler):
    def send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self.send_json(200, {"ok": True, "service": "leetcode-reminder"})
            return
        if path != "/api/check":
            self.send_json(404, {"ok": False, "error": "Not found."})
            return

        secret = os.getenv("CRON_SECRET", "").strip()
        token = parse_qs(urlparse(self.path).query).get("token", [""])[0]
        if not secret or token != secret:
            self.send_json(401, {"ok": False, "error": "Unauthorized."})
            return
        try:
            self.send_json(200, check_reminder())
        except RuntimeError as error:
            logger.warning("Reminder check failed: %s", error)
            self.send_json(502, {"ok": False, "error": str(error)})
        except Exception:
            logger.exception("Unexpected API error")
            self.send_json(500, {"ok": False, "error": "Unexpected server error."})

    def do_HEAD(self):
        path = urlparse(self.path).path
        if path == "/health":
            self.send_json(200, {"ok": True})
        else:
            self.send_json(404, {"ok": False, "error": "Not found."})

    def log_message(self, fmt, *args):
        logger.info("%s - %s", self.address_string(), fmt % args)


def scheduler_loop():
    """Run the reminder check once during each eligible half-hour slot."""
    last_slot = None
    while True:
        try:
            timezone = get_timezone()
            now = datetime.now(timezone)
            slot = (now.date().isoformat(), now.hour, now.minute // 30)
            if reminder_due(now) and slot != last_slot:
                # Mark first so a temporary API error does not create a request loop.
                last_slot = slot
                try:
                    result = check_reminder()
                    logger.info("Scheduled check: %s", result)
                except Exception:
                    logger.exception("Scheduled reminder check failed")
        except Exception:
            logger.exception("Scheduler error")
        time.sleep(CHECK_INTERVAL_SECONDS)


def main():
    port = int(os.getenv("PORT", "8080"))
    threading.Thread(target=scheduler_loop, name="reminder-scheduler", daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", port), RequestHandler)
    logger.info("LeetCode Reminder service listening on port %s", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping service")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
