from __future__ import absolute_import, division, print_function
import os
import subprocess

# from ranger.api.commands import Command
from ranger.config.commands import yank, set_


class TTYNotFound(Exception):
    pass


class set_oscyank(set_):
    """:set_oscyank <option name>=<string>

    Bypass limit of `set` that not support custom options.
    Note: don't quote string values.
    """

    name = "set_oscyank"

    def execute(self):
        name = self.arg(1)
        name, value, _, toggle = self.parse_setting_line_v2()
        name = self.__class__.name[4:] + ":" + name
        if name.endswith("?"):
            self.fm.notify(self.fm.settings._settings.get(name[:-1], ""), 10)
        elif toggle:
            # self.fm.toggle_option(name)
            self.toggle_option(name)
        else:
            # self.fm.set_option_from_string(name, value)
            self.set_option_from_string(name, value)

    def toggle_option(self, option_name):
        current = self.fm.settings._settings.get(option_name, False)
        if isinstance(current, bool):
            self.fm.settings._settings[option_name] = not current
        else:
            self.fm.notify(option_name + " is not a boolean option", bad=True)

    def set_option_from_string(self, option_name, value):
        if not isinstance(value, str):
            raise ValueError("The value for an option needs to be a string.")
        self.fm.settings._settings[option_name] = self._parse_option_value(
            option_name, value
        )

    def _parse_option_value(self, name, value):
        if value.lower() in ("true", "on", "yes", "1"):
            return True
        if value.lower() in ("false", "off", "no", "0"):
            return False
        if value.lower() == "none":
            return None
        # All other values are strings. No int, float, list support yet
        return value


class oscyank(yank):
    """:oscyank [name|dir|path]

    Copies the file's name (default), directory or path into system clipboard
    with OSC 52 support. Fallbacks to default 'yank' command which uses
    the primary X selection and the clipboard.
    """

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
        explicit_backend = self.fm.settings._settings.get("oscyank:backend", "auto")
        if explicit_backend in ("osc52", "osc"):
            return True
        elif explicit_backend == "manager":
            return False

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
            r = b""  # osc sequence

            # kitty has obsolete the modified chunking protocol since 0.22.
            # No need to keep the clear sequence for backward support.
            # if (
            #     "kitty" == os.environ.get("LC_TERMINAL")
            #     or "KITTY_WINDOW_ID" in os.environ
            #     or "xterm-kitty" == os.environ.get("TERM")
            # ):
            #     r += b"\033]52;c;!\a"

            r += b"\033]52;c;%s\a" % base64.b64encode(content.encode("utf-8"))

            # No need to passthrough escape sequence for osc 52.
            # https://github.com/tmux/tmux/wiki/FAQ#what-is-the-passthrough-escape-sequence-and-how-do-i-use-it
            # if os.environ.get("TMUX"):
            #     r = r.replace(b"\033", b"\033\033")
            #     r = b"\033Ptmux;%s\033\\" % r

            # TODO: size limit? Non block writing?
            fobj.write(r)

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
        tty = None
        try:
            tty = subprocess.check_output(["tty"]).strip()
            if tty == "not a tty":
                tty = None
        except subprocess.CalledProcessError:
            pass

        if not tty:
            if "TMUX" in os.environ:
                tty = self.get_tty_from_tmux()
            else:
                self.fm.notify("No available tty is found!", bad=True)
                raise TTYNotFound
        return tty


# References
# - https://github.com/tmux/tmux/issues/1477
