# ranger-oscyank

[![License: MIT][license icon]][license]

Plugin `ranger-oscyank` introduces a drop-in replacement (command `oscyank`)
for the internal command `yank`. Besides the old integration with
system clipboard manager tools (like `pbcopy`, `xsel`) in `yank`, `oscynak`
enables copying text into system clipbard with [ANSI OSC52][osc52] sequence.

Dependency: [OSC52 support][terminal-osc52-support] in your terminal emulator.

## Installation

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

## Features

### Backend Switch
`oscyank` supports two backends:

- system clipboard manager tools, like `pbcopy`, `wl-copy`, `xclip`, `xsel`.
- ANSI OSC 52 sequence

The backend selection priority is,

1. OSC 52 when connecting by SSH without X forwarding
2. Clipboard tools if any of them is available
3. Fallback to OSC 52 if none former conditions being matched

You can choose the backend explicitly with special option setting:

```sh
# Force OSC 52 copying. NOTE: don't quote the value like 'osc52'.
set_oscyank backend osc52

# or
set_oscyank backend manager
```

### Quantifier

Switch path styles copied with quantifiers:

- `1` (e.g. `1yp`): replace your home path with tilde `~`
- `2`: strip the leading home path

> quantifier: If this command was mapped to the key "X" and
> the user pressed 6X, self.quantifier will be 6.

## License

The MIT License (MIT)

Copyright (c) 2021 laggardkernel

[license icon]: https://img.shields.io/badge/License-MIT-blue.svg
[license]: https://opensource.org/licenses/MIT
[osc52]: https://invisible-island.net/xterm/ctlseqs/ctlseqs.html#h3-Operating-System-Commands
[terminal-osc52-support]: https://github.com/ojroques/vim-oscyank#vim-oscyank
