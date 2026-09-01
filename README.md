# ranger-oscyank

[![License: MIT][license icon]][license]

Plugin `ranger-oscyank` introduces a drop-in replacement (command `oscyank`)
for the internal command `yank`. It copies text into the system clipboard
with the [ANSI OSC52][osc52] sequence.

Dependency: [OSC52 support][terminal-osc52-support] in your terminal emulator.

## QuickStart

Git clone the plugin into ranger's plugin folder. (`ranger >= 1.9.3`)

```bash
git clone https://github.com/laggardkernel/ranger-oscyank.git ~/.config/ranger/plugins/oscyank
```

Overrides default `yank` key bindings in `rc.conf`.

```sh
# ~/.config/ranger/rc.conf
map yp oscyank path
map yd oscyank dir
map yn oscyank name
map y. oscyank name_without_extension
```

To use `ranger-oscyank` within `tmux`, enable tmux clipboard integration and
ensure the pane terminfo advertises `Ms`.[tmux-clipboard]

```conf
# ~/.tmux.conf, or ~/.config/tmux/tmux.conf
set -s set-clipboard on
```

The plugin writes a raw OSC52 sequence to the pane tty. tmux handles that
sequence when `set-clipboard` is `on` (or `external`) and the `Ms` capability
is available. `allow-passthrough` is a separate pane option for applications
that send the `ESC Ptmux;... ESC \\` wrapper; this plugin does not use that
bypass, so it does not need `allow-passthrough` enabled.

## Features

### Size Limit

`oscyank` can reject selections above a configurable OSC52 size limit:

```sh
set_oscyank max_length 100000
```

The default is `0` (unlimited), matching `vim-oscyank`. An over-limit
selection is not sent; ranger shows a warning instead of copying partial text.

### Environment Support

`oscyank` emits standard OSC52 for local terminals, SSH, tmux, screen, and
Herdr. End-to-end behavior depends on each intermediary and the outer terminal
forwarding OSC52. The startup check is advisory: a missing `Ms` terminfo
capability does not prove that the outer terminal cannot support OSC52, and a
present one does not prove that it will.

For tmux, use `set-clipboard on` (or `external`) and make sure `Ms` is
present in the pane's terminfo. Screen and Herdr have their own forwarding
behavior; the plugin does not invoke a Herdr-specific clipboard command.

### Quantifier

Switch path styles copied with quantifiers:

- `1` (e.g. `1yp`): replace your home path with tilde `~`
- `2`: strip the leading home path

> quantifier: If this command was mapped to the key "X" and
> the user pressed 6X, self.quantifier will be 6.

## License

The MIT License (MIT)

Copyright (c) 2024 laggardkernel

[license icon]: https://img.shields.io/badge/License-MIT-blue.svg
[license]: https://opensource.org/licenses/MIT
[osc52]: https://invisible-island.net/xterm/ctlseqs/ctlseqs.html#h3-Operating-System-Commands
[terminal-osc52-support]: https://github.com/ojroques/vim-oscyank#vim-oscyank
[tmux-clipboard]: https://github.com/tmux/tmux/wiki/Clipboard
