# CHANGELOG

This document follows the conventions laid out in [Keep a CHANGELOG](https://keepachangelog.com/en/1.0.0).

This project uses [towncrier](https://towncrier.readthedocs.io/) and the changes for the upcoming release can be found in <https://github.com/ansys/pre-commit-hooks/tree/main/doc/changelog.d/>.

<!-- towncrier release notes start -->

## [0.2.9](https://github.com/ansys/pre-commit-hooks/releases/tag/v0.2.9) - February 16 2024

### Changed

- Pinned all dependencies

## [0.2.8](https://github.com/ansys/pre-commit-hooks/releases/tag/v0.2.8) - January 17 2024

### Fixed

- Add upper limit to reuse dependency

## [0.2.7](https://github.com/ansys/pre-commit-hooks/releases/tag/v0.2.7) - January 16 2024

### Fixed

- Fix pytest python versions and fileinput [#118](https://github.com/ansys/pre-commit-hooks/pull/118)

### Dependencies

- Bump `gitpython` from 3.1.40 to 3.1.41 [#120](https://github.com/ansys/pre-commit-hooks/pull/120)
- Bump `ansys-sphinx-theme` from 0.13.0 to 0.13.1 [#121](https://github.com/ansys/pre-commit-hooks/pull/121)

## [0.2.6](https://github.com/ansys/pre-commit-hooks/releases/tag/v0.2.6) - January 11 2024

### Added

- Add full header to file if empty ([#116](https://github.com/ansys/pre-commit-hooks/pull/116))

## [0.2.5](https://github.com/ansys/pre-commit-hooks/releases/tag/v0.2.5) - January 10 2024

### Added

- Added custom argument for the copyright's start year & updated add_hook_changes ([#111](https://github.com/ansys/pre-commit-hooks/pull/111))

## [0.2.4](https://github.com/ansys/pre-commit-hooks/releases/tag/v0.2.4) - January 4 2024

### Fixed
- Apply hook changes after add-license-headers runs ([#108](https://github.com/ansys/pre-commit-hooks/pull/108))

## [0.2.3](https://github.com/ansys/pre-commit-hooks/releases/tag/v0.2.3) - January 2 2024

### Changed
- Remove python 3.8 and add python 3.12 ([#106](https://github.com/ansys/pre-commit-hooks/pull/106))
- Update year to 2024 in license files ([#107](https://github.com/ansys/pre-commit-hooks/pull/107))

### Dependencies
- `pre-commit` autoupdate ([#97](https://github.com/ansys/pre-commit-hooks/pull/97), [#99](https://github.com/ansys/pre-commit-hooks/pull/99), [#100](https://github.com/ansys/pre-commit-hooks/pull/100), [#103](https://github.com/ansys/pre-commit-hooks/pull/103))
- Bump `actions/labeler` from 4 to 5 ([#98](https://github.com/ansys/pre-commit-hooks/pull/98))
- Bump `ansys/actions` from 4 to 5 ([#102](https://github.com/ansys/pre-commit-hooks/pull/102))
- Bump `pytest` from 7.4.3 to 7.4.4 ([#104](https://github.com/ansys/pre-commit-hooks/pull/104))

## [0.2.2](https://github.com/ansys/pre-commit-hooks/releases/tag/v0.2.2) - November 15 2023

### Added

- Add headers to tests and examples ([#85](https://github.com/ansys/pre-commit-hooks/pull/85))
- Add typehints to add-license-headers functions ([#93](https://github.com/ansys/pre-commit-hooks/pull/93))

### Fixed

- Fix add-license-headers to keep edits from previously run hooks ([#88](https://github.com/ansys/pre-commit-hooks/pull/88))

### Changed

- Remove dep5 files from repository ([#89](https://github.com/ansys/pre-commit-hooks/pull/89))
- Remove .reuse and LICENSES folders ([#95](https://github.com/ansys/pre-commit-hooks/pull/95))

### Dependencies

- Bump `sphinx-autodoc-typehints` from 1.24.0 to 1.25.2 ([#86](https://github.com/ansys/pre-commit-hooks/pull/86), [#90](https://github.com/ansys/pre-commit-hooks/pull/90))
- `pre-commit` autoupdate ([#87](https://github.com/ansys/pre-commit-hooks/pull/87), [#94](https://github.com/ansys/pre-commit-hooks/pull/94))
- Bump `ansys-sphinx-theme` from 0.12.4 to 0.12.5 ([#91](https://github.com/ansys/pre-commit-hooks/pull/91))

## [0.2.1](https://github.com/ansys/pre-commit-hooks/releases/tag/v0.2.1) - October 31 2023

### Added

- Added difference check between original file and updated file ([#77](https://github.com/ansys/pre-commit-hooks/pull/77))

### Dependencies

- `pre-commit` autoupdate ([#76](https://github.com/ansys/pre-commit-hooks/pull/76))
- Bump `ansys-sphinx-theme` from 0.12.3 to 0.12.4 ([#80](https://github.com/ansys/pre-commit-hooks/pull/80))
- Bump `pytest` from 7.4.2 to 7.4.3 ([#81](https://github.com/ansys/pre-commit-hooks/pull/81))

## [0.2.0](https://github.com/ansys/pre-commit-hooks/releases/tag/v0.2.0) - October 17 2023

### Added

- Added check_license argument ([#64](https://github.com/ansys/pre-commit-hooks/pull/64))
- Run hook on specific directories and files ([#65](https://github.com/ansys/pre-commit-hooks/pull/65))
- Update headers & improve unit tests ([#69](https://github.com/ansys/pre-commit-hooks/pull/69))
- Create assets folder with common REUSE templates ([#72](https://github.com/ansys/pre-commit-hooks/pull/72))
- Run add-license-headers hook serially ([#74](https://github.com/ansys/pre-commit-hooks/pull/74))

### Changed

- Removed loc argument & passed in committed files ([#57](https://github.com/ansys/pre-commit-hooks/pull/57))

### Dependencies

- Bump `ansys-sphinx-theme` from 0.12.1 to 0.12.2 ([#70](https://github.com/ansys/pre-commit-hooks/pull/70))
- Bump `pre-commit` from v4.4.0 to v4.5.0 ([#71](https://github.com/ansys/pre-commit-hooks/pull/71))

## [0.1.3](https://github.com/ansys/pre-commit-hooks/releases/tag/v0.1.3) - September 8 2023

### Added

- Create custom flags for add-license-header ([#44](https://github.com/ansys/pre-commit-hooks/pull/44))

### Changed

- Update descriptions for add-license-headers in README ([#40](https://github.com/ansys/pre-commit-hooks/pull/40))

## [0.1.2](https://github.com/ansys/pre-commit-hooks/releases/tag/v0.1.2) - September 5 2023

### Dependencies

- [pre-commit.ci] pre-commit autoupdate [#39](https://github.com/ansys/pre-commit-hooks/pull/39)

## [0.1.1](https://github.com/ansys/pre-commit-hooks/releases/tag/v0.1.1) - September 4 2023

### Added

- Directory checks & print statement updates [#34](https://github.com/ansys/pre-commit-hooks/pull/34)

### Dependencies

- build(deps-dev): bump gitpython from 3.1.32 to 3.1.34 [#35](https://github.com/ansys/pre-commit-hooks/pull/35)
- build(deps-dev): bump pytest from 7.3.0 to 7.4.1 [#38](https://github.com/ansys/pre-commit-hooks/pull/38)
- build(deps-dev): bump sphinx from 7.2.4 to 7.2.5 [#37](https://github.com/ansys/pre-commit-hooks/pull/37)
- build(deps-dev): bump ansys-sphinx-theme from 0.10.4 to 0.10.5 [#36](https://github.com/ansys/pre-commit-hooks/pull/36)

## [0.1.0](https://github.com/ansys/pre-commit-hooks/releases/tag/v0.1.0) - September 1 2023

### Added

- Create pre-commit hook to add license header to all files ([#7](https://github.com/ansys/pre-commit-hooks/pull/7))
- Default args in pre-commit-hooks.yaml ([#11](https://github.com/ansys/pre-commit-hooks/pull/11))
- feat: ignore links (temp) ([#20](https://github.com/ansys/pre-commit-hooks/pull/20))

### Changed

- Update the readme file ([#21](https://github.com/ansys/pre-commit-hooks/pull/21))
- Edits to RST and PY files ([#28](https://github.com/ansys/pre-commit-hooks/pull/28))

### Fixed

- Fix add-license-headers for reuse version >=2 ([#10](https://github.com/ansys/pre-commit-hooks/pull/10))
- Fix reuse 2.0 implementation ([#17](https://github.com/ansys/pre-commit-hooks/pull/17))
