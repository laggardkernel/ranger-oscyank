# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

None.

## [0.4.0] - 2026-09-02

### Changed

- Write OSC52 directly to `/dev/tty` without tmux or Herdr pane discovery.

## [0.3.0] - 2026-09-01

### Changed

- Use OSC52 as the only clipboard backend.
- Warn once at startup when terminal terminfo does not advertise OSC52.
- Reject selections over the configurable `oscyank:max_length` limit.
- Fix tty and tmux byte parsing for OSC52 routing.

## [0.2.0]

### Added

- Termux support
- Check OSC 52 support of terminals thru "Ms" termcap

### Changed

- Drop X11 clipboard syncing support, only use OSC52 for conn over SSH

### Fixed

- Drop `kitty` clear sequence, remove redundant tmux passthrough escaping

## [0.1.0]

### Added

- New backend that copying text into system clipboard with OSC52
- Automatic switch between backends OSC52 and clipboard tools
- Use quantifier to switch path styles
- Override backend with custom options.

### Fixed

- Fix `tty` output reading

### Removed

- Remove `$TTY` envrionment variable checking

[Unreleased]: https://github.com/laggardkernel/ranger-oscyank/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/laggardkernel/ranger-oscyank/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/laggardkernel/ranger-oscyank/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/laggardkernel/ranger-oscyank/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/laggardkernel/ranger-oscyank/compare/7debe09...v0.1.0
