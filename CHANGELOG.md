# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- New backend that copying text into system clipboard with OSC52
- Automatic switch between backends OSC52 and clipboard tools
- Use quantifier to switch path styles
- Override backend with custom options.
- Termux support
- Check OSC 52 support of terminals thru "Ms" termcap

### Changed

- Drop X11 clipboard syncing support, only use OSC52 for conn over SSH

### Fixed

- Fix `tty` output reading
- Drop `kitty` clear sequence, remove redundant tmux passthrough escaping

### Removed

- Remove `$TTY` envrionment variable checking

[Unreleased]: https://github.com/laggardkernel/ranger-oscyank/compare/7debe09...HEAD
