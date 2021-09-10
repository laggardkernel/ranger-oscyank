from __future__ import absolute_import, division, print_function
import os
import subprocess

# from ranger.config.commands import yank
from ranger.api.commands import Command


class TTYNotFound(Exception):
    pass


class oscyank(Command):
    """:oscyank [name|dir|path]

    Copies the file's name (default), directory or path into system clipboard
    with OSC 52 support. Fallbacks to default 'yank' command which uses
    the primary X selection and the clipboard.
    """

    modes = {
        "": "basename",
        "name_without_extension": "basename_without_extension",
        "name": "basename",
        "dir": "dirname",
        "path": "path",
    }

    def execute(self):
        # TODO: Any way to detect OSC 52 support from terminal?
        copy_func = None
        if self.do_prefer_osc():
            copy_func = self.osc_copy
        else:
            clipboard_commands = self.clipboards()
            if len(clipboard_commands) > 0:
                from functools import partial

                copy_func = partial(self.clipboard_copy, clipboard_commands)
        if copy_func is None:
            copy_func = self.osc_copy

        mode = self.modes[self.arg(1)]
        selection = self.get_selection_attr(mode)
        selection = self.process_selection(mode, selection)
        content = "\n".join(selection)

        copy_func(content)

    def process_selection(self, mode, selection):
        if mode.startswith("basename") or self.quantifier is None:
            return selection

        home_with_slash = os.path.expanduser("~")
        if not home_with_slash.endswith(os.sep):
            home_with_slash = os.path.join(home_with_slash, "")
        length = len(home_with_slash)
        if self.quantifier == 1:
            selection = [
                os.path.join("~", _[length:]) if _.startswith(home_with_slash) else _
                for _ in selection
            ]
        elif self.quantifier == 2:
            selection = [
                _[length:] if _.startswith(home_with_slash) else _ for _ in selection
            ]
        return selection

    def clipboard_copy(self, clipboard_commands, content):
        for command in clipboard_commands:
            process = subprocess.Popen(
                command, universal_newlines=True, stdin=subprocess.PIPE
            )
            process.communicate(input=content)

    def do_prefer_osc(self):
        # X11 forwarding detection (`$DISPLAY`) is skipped. Prefer more
        # lightweighted osc_copy over SSH clipboard syncing by default.
        if (
            "SSH_CLIENT" in os.environ
            or "SSH_CONNECTION" in os.environ
            and "DISPLAY" not in os.environ
        ):
            return True
        return False

    def osc_copy(self, content):
        import base64

        tty = self.get_tty()
        with open(tty, "wb") as fobj:
            osc_sequence = b""
            # Deprecation: kitty has obsolete the modified chunking protocol
            # since 0.22. Still keep the clear sequence for backward support.
            if (
                "kitty" == os.environ.get("LC_TERMINAL")
                or "KITTY_WINDOW_ID" in os.environ
                or "xterm-kitty" == os.environ.get("TERM")
            ):
                osc_sequence += b"\033]52;c;!\a"

            osc_sequence += (
                b"\033]52;c;" + base64.b64encode(content.encode("utf-8")) + b"\a"
            )
            # TODO: size limit? Non block writing?
            fobj.write(osc_sequence)

    def clipboards(self):
        from ranger.ext.get_executables import get_executables

        clipboard_managers = {
            "xclip": [
                ["xclip"],
                ["xclip", "-selection", "clipboard"],
            ],
            "xsel": [
                ["xsel"],
                ["xsel", "-b"],
            ],
            "wl-copy": [
                ["wl-copy"],
            ],
            "pbcopy": [
                ["pbcopy"],
            ],
        }
        ordered_managers = ["pbcopy", "wl-copy", "xclip", "xsel"]
        executables = get_executables()
        for manager in ordered_managers:
            if manager in executables:
                return clipboard_managers[manager]
        return []

    def get_tty_from_tmux(self):
        try:
            tmux_tty = [
                tty
                for is_active, tty in (
                    line.split()
                    for line in subprocess.check_output(
                        ["tmux", "list-panes", "-F", "#{pane_active} #{pane_tty}"]
                    )
                    .strip()
                    .split(b"\n")
                )
                if is_active
            ][0]
        except (subprocess.CalledProcessError, IndexError):
            raise TTYNotFound
        return tmux_tty

    def get_tty(self):
        if "TTY" in os.environ:  # ZSH
            return os.environ.get("TTY")

        try:
            tty = subprocess.check_output(["tty"]).strip()
        except subprocess.CalledProcessError:
            if "TMUX" in os.environ:
                tty = self.get_tty_from_tmux()
            else:
                raise TTYNotFound
        return tty

    def get_selection_attr(self, attr):
        return [getattr(item, attr) for item in self.fm.thistab.get_selection()]

    def tab(self, tabnum):
        return (self.start(1) + mode for mode in sorted(self.modes.keys()) if mode)


# References
# - https://github.com/tmux/tmux/issues/1477
# - https://github.com/ranger/ranger/pull/2409
