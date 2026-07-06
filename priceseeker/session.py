"""Remember toolbar state between runs (last tickers, period, toggles).

Stored as a small JSON file under the user's config directory
($XDG_CONFIG_HOME or ~/.config). Both directions are best-effort: a
missing or corrupt file means a default session, and a failed write is
silently dropped — closing the app must never fail.
"""

import json
import os


def _path():
    base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return os.path.join(base, "priceseeker.json")


def load():
    """The last saved session dict, or {} if there is none."""
    try:
        with open(_path()) as f:
            state = json.load(f)
        return state if isinstance(state, dict) else {}
    except Exception:
        return {}


def save(state):
    """Write the session dict; never raises."""
    try:
        os.makedirs(os.path.dirname(_path()), exist_ok=True)
        with open(_path(), "w") as f:
            json.dump(state, f, indent=2)
    except OSError:
        pass
