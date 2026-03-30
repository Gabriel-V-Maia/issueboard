import threading
import time
import requests
from typing import Callable

CLIENT_ID      = "Ov23li0DqEQROkXMdstK"
SCOPES_PUBLIC  = "read:user public_repo"
SCOPES_PRIVATE = "read:user repo"


def device_flow_start(scopes: str) -> dict:
    r = requests.post(
        "https://github.com/login/device/code",
        headers={"Accept": "application/json"},
        data={"client_id": CLIENT_ID, "scope": scopes},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def device_flow_poll(
    device_code: str,
    interval: int,
    stop_event: threading.Event,
    on_token: Callable[[str], None],
    on_error: Callable[[str], None],
):
    while not stop_event.is_set():
        time.sleep(interval)
        try:
            r = requests.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id":   CLIENT_ID,
                    "device_code": device_code,
                    "grant_type":  "urn:ietf:params:oauth:grant-type:device_code",
                },
                timeout=10,
            )
            data = r.json()
        except Exception as e:
            on_error(str(e))
            return

        err = data.get("error")
        if err == "authorization_pending":
            continue
        elif err == "slow_down":
            interval += 5
            continue
        elif err == "expired_token":
            on_error("Code expired. Please try again.")
            return
        elif err == "access_denied":
            on_error("Access denied.")
            return
        elif "access_token" in data:
            on_token(data["access_token"])
            return
        else:
            on_error(f"Unexpected response: {data}")
            return