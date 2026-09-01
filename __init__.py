import curses

import ranger.api

from .oscyank import oscyank, set_oscyank  # noqa: F401


_previous_hook_ready = ranger.api.hook_ready
_warned = False


def osc52_supported():
    try:
        return bool(curses.tigetstr("Ms"))
    except curses.error:
        return False


def hook_ready(fm):
    global _warned
    if not _warned:
        _warned = True
        if not osc52_supported():
            fm.notify(
                "OSC52 support could not be verified from terminal terminfo; "
                "clipboard copying may not work.",
                bad=True,
            )
    _previous_hook_ready(fm)


ranger.api.hook_ready = hook_ready
