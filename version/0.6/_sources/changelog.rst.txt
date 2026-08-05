.. _ref_release_notes:

Release notes
#############

This document contains the release notes for the project.

.. vale off

.. towncrier release notes start

`0.6.0 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.6.0>`_ - March 19, 2026
=========================================================================================

.. tab-set::


  .. tab-item:: Added

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Add check-actions-security action
          - `#352 <https://github.com/ansys/pre-commit-hooks/pull/352>`_


  .. tab-item:: Fixed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Replace {project-name} with Ansys Pre-Commit Hooks
          - `#368 <https://github.com/ansys/pre-commit-hooks/pull/368>`_

        * - Remove recursive approach and fix few bugs
          - `#396 <https://github.com/ansys/pre-commit-hooks/pull/396>`_


  .. tab-item:: Dependencies

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - bump sphinx from 8.2.1 to 8.2.3
          - `#295 <https://github.com/ansys/pre-commit-hooks/pull/295>`_

        * - bump pytest from 8.3.4 to 8.3.5
          - `#296 <https://github.com/ansys/pre-commit-hooks/pull/296>`_

        * - bump jinja2 from 3.1.5 to 3.1.6
          - `#298 <https://github.com/ansys/pre-commit-hooks/pull/298>`_

        * - bump ansys-sphinx-theme[autoapi] from 1.3.2 to 1.3.3
          - `#303 <https://github.com/ansys/pre-commit-hooks/pull/303>`_

        * - bump pytest-cov from 6.0.0 to 6.1.1
          - `#305 <https://github.com/ansys/pre-commit-hooks/pull/305>`_

        * - bump ansys-sphinx-theme[autoapi] from 1.3.3 to 1.4.2
          - `#309 <https://github.com/ansys/pre-commit-hooks/pull/309>`_

        * - bump importlib-metadata from 8.6.1 to 8.7.0
          - `#310 <https://github.com/ansys/pre-commit-hooks/pull/310>`_

        * - bump ansys-sphinx-theme[autoapi] from 1.4.2 to 1.4.4
          - `#312 <https://github.com/ansys/pre-commit-hooks/pull/312>`_

        * - Bump ansys-sphinx-theme[autoapi] from 1.4.4 to 1.5.0
          - `#313 <https://github.com/ansys/pre-commit-hooks/pull/313>`_

        * - Bump ansys/actions from 9 to 10
          - `#314 <https://github.com/ansys/pre-commit-hooks/pull/314>`_

        * - Bump pytest from 8.3.5 to 8.4.0
          - `#315 <https://github.com/ansys/pre-commit-hooks/pull/315>`_

        * - Bump ansys-sphinx-theme[autoapi] from 1.5.0 to 1.5.2
          - `#316 <https://github.com/ansys/pre-commit-hooks/pull/316>`_, `#327 <https://github.com/ansys/pre-commit-hooks/pull/327>`_

        * - Bump pytest-cov from 6.1.1 to 6.2.1
          - `#318 <https://github.com/ansys/pre-commit-hooks/pull/318>`_, `#326 <https://github.com/ansys/pre-commit-hooks/pull/326>`_

        * - Bump requests from 2.32.3 to 2.32.4
          - `#319 <https://github.com/ansys/pre-commit-hooks/pull/319>`_, `#329 <https://github.com/ansys/pre-commit-hooks/pull/329>`_

        * - Bump pytest from 8.4.0 to 8.4.1
          - `#320 <https://github.com/ansys/pre-commit-hooks/pull/320>`_

        * - Bump numpydoc from 1.8.0 to 1.9.0
          - `#328 <https://github.com/ansys/pre-commit-hooks/pull/328>`_

        * - Bump pytest from 8.3.5 to 8.4.1
          - `#330 <https://github.com/ansys/pre-commit-hooks/pull/330>`_

        * - Bump ansys-sphinx-theme[autoapi] from 1.5.2 to 1.5.3
          - `#331 <https://github.com/ansys/pre-commit-hooks/pull/331>`_

        * - Bump gitpython from 3.1.44 to 3.1.45
          - `#333 <https://github.com/ansys/pre-commit-hooks/pull/333>`_

        * - Bump actions/download-artifact from 4.1.9 to 5.0.0
          - `#338 <https://github.com/ansys/pre-commit-hooks/pull/338>`_

        * - Bump actions/checkout from 4 to 5
          - `#339 <https://github.com/ansys/pre-commit-hooks/pull/339>`_

        * - Bump requests from 2.32.4 to 2.32.5
          - `#341 <https://github.com/ansys/pre-commit-hooks/pull/341>`_

        * - Bump ansys-sphinx-theme[autoapi] from 1.5.3 to 1.6.0
          - `#342 <https://github.com/ansys/pre-commit-hooks/pull/342>`_

        * - Bump pypa/gh-action-pypi-publish from 1.12.4 to 1.13.0
          - `#343 <https://github.com/ansys/pre-commit-hooks/pull/343>`_

        * - Bump actions/labeler from 5 to 6
          - `#344 <https://github.com/ansys/pre-commit-hooks/pull/344>`_

        * - Bump pytest-cov from 6.2.1 to 6.3.0
          - `#345 <https://github.com/ansys/pre-commit-hooks/pull/345>`_

        * - Bump reuse from 5.0.2 to 5.1.1
          - `#346 <https://github.com/ansys/pre-commit-hooks/pull/346>`_

        * - Bump pytest from 8.4.1 to 8.4.2
          - `#347 <https://github.com/ansys/pre-commit-hooks/pull/347>`_

        * - Bump ansys-sphinx-theme[autoapi] from 1.6.0 to 1.6.1
          - `#348 <https://github.com/ansys/pre-commit-hooks/pull/348>`_

        * - Bump pytest-cov from 6.3.0 to 7.0.0
          - `#349 <https://github.com/ansys/pre-commit-hooks/pull/349>`_

        * - Bump peter-evans/create-or-update-comment from 4.0.0 to 5.0.0
          - `#353 <https://github.com/ansys/pre-commit-hooks/pull/353>`_

        * - Bump actions-ecosystem/action-add-labels from 1.1.0 to 1.1.3
          - `#354 <https://github.com/ansys/pre-commit-hooks/pull/354>`_

        * - Bump ansys-sphinx-theme[autoapi] from 1.6.1 to 1.6.3
          - `#357 <https://github.com/ansys/pre-commit-hooks/pull/357>`_

        * - Bump actions/download-artifact from 5.0.0 to 6.0.0
          - `#359 <https://github.com/ansys/pre-commit-hooks/pull/359>`_

        * - Bump ansys/actions from 10.1.4 to 10.1.5
          - `#360 <https://github.com/ansys/pre-commit-hooks/pull/360>`_

        * - Bump reuse from 5.1.1 to 6.2.0
          - `#361 <https://github.com/ansys/pre-commit-hooks/pull/361>`_

        * - Bump pytest from 8.4.2 to 9.0.0
          - `#362 <https://github.com/ansys/pre-commit-hooks/pull/362>`_

        * - Bump actions/checkout from 5.0.0 to 6.0.0
          - `#365 <https://github.com/ansys/pre-commit-hooks/pull/365>`_

        * - Bump ansys/actions from 10.1.5 to 10.2.2
          - `#369 <https://github.com/ansys/pre-commit-hooks/pull/369>`_

        * - Bump pytest from 9.0.0 to 9.0.2
          - `#370 <https://github.com/ansys/pre-commit-hooks/pull/370>`_

        * - Bump actions/checkout from 6.0.0 to 6.0.1
          - `#371 <https://github.com/ansys/pre-commit-hooks/pull/371>`_

        * - Bump numpydoc from 1.9.0 to 1.10.0
          - `#372 <https://github.com/ansys/pre-commit-hooks/pull/372>`_

        * - Bump ansys-sphinx-theme[autoapi] from 1.6.3 to 1.6.4
          - `#374 <https://github.com/ansys/pre-commit-hooks/pull/374>`_

        * - Bump ansys/actions from 10.2.2 to 10.2.3
          - `#375 <https://github.com/ansys/pre-commit-hooks/pull/375>`_

        * - Bump actions/download-artifact from 6.0.0 to 7.0.0
          - `#377 <https://github.com/ansys/pre-commit-hooks/pull/377>`_

        * - Bump importlib-metadata from 8.7.0 to 8.7.1
          - `#378 <https://github.com/ansys/pre-commit-hooks/pull/378>`_

        * - Bump gitpython from 3.1.45 to 3.1.46
          - `#379 <https://github.com/ansys/pre-commit-hooks/pull/379>`_

        * - Bump actions/checkout from 6.0.1 to 6.0.2
          - `#382 <https://github.com/ansys/pre-commit-hooks/pull/382>`_

        * - Bump ansys/actions from 10.2.3 to 10.2.4
          - `#383 <https://github.com/ansys/pre-commit-hooks/pull/383>`_

        * - Bump ansys-sphinx-theme[autoapi] from 1.6.4 to 1.7.0
          - `#385 <https://github.com/ansys/pre-commit-hooks/pull/385>`_

        * - Bump ansys/actions from 10.2.4 to 10.2.5
          - `#386 <https://github.com/ansys/pre-commit-hooks/pull/386>`_

        * - Bump actions/download-artifact from 7.0.0 to 8.0.0
          - `#393 <https://github.com/ansys/pre-commit-hooks/pull/393>`_

        * - Bump ansys-sphinx-theme[autoapi] from 1.7.0 to 1.7.1
          - `#394 <https://github.com/ansys/pre-commit-hooks/pull/394>`_

        * - Bump ansys-sphinx-theme[autoapi] from 1.7.1 to 1.7.2
          - `#397 <https://github.com/ansys/pre-commit-hooks/pull/397>`_

        * - Bump ansys/actions from 10.2.5 to 10.2.7
          - `#398 <https://github.com/ansys/pre-commit-hooks/pull/398>`_


  .. tab-item:: Documentation

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - add favicon to documentation
          - `#294 <https://github.com/ansys/pre-commit-hooks/pull/294>`_

        * - Update CONTRIBUTORS.md with the latest contributors
          - `#300 <https://github.com/ansys/pre-commit-hooks/pull/300>`_, `#301 <https://github.com/ansys/pre-commit-hooks/pull/301>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - pre-commit automatic update
          - `#297 <https://github.com/ansys/pre-commit-hooks/pull/297>`_, `#299 <https://github.com/ansys/pre-commit-hooks/pull/299>`_, `#304 <https://github.com/ansys/pre-commit-hooks/pull/304>`_, `#307 <https://github.com/ansys/pre-commit-hooks/pull/307>`_

        * - move to v9 ansys/actions
          - `#308 <https://github.com/ansys/pre-commit-hooks/pull/308>`_

        * - Add Python 3.13 to workflow
          - `#311 <https://github.com/ansys/pre-commit-hooks/pull/311>`_

        * - Pre-commit automatic update
          - `#321 <https://github.com/ansys/pre-commit-hooks/pull/321>`_, `#332 <https://github.com/ansys/pre-commit-hooks/pull/332>`_, `#337 <https://github.com/ansys/pre-commit-hooks/pull/337>`_, `#340 <https://github.com/ansys/pre-commit-hooks/pull/340>`_, `#350 <https://github.com/ansys/pre-commit-hooks/pull/350>`_, `#355 <https://github.com/ansys/pre-commit-hooks/pull/355>`_, `#363 <https://github.com/ansys/pre-commit-hooks/pull/363>`_, `#364 <https://github.com/ansys/pre-commit-hooks/pull/364>`_, `#373 <https://github.com/ansys/pre-commit-hooks/pull/373>`_, `#376 <https://github.com/ansys/pre-commit-hooks/pull/376>`_, `#381 <https://github.com/ansys/pre-commit-hooks/pull/381>`_, `#387 <https://github.com/ansys/pre-commit-hooks/pull/387>`_, `#388 <https://github.com/ansys/pre-commit-hooks/pull/388>`_, `#395 <https://github.com/ansys/pre-commit-hooks/pull/395>`_, `#399 <https://github.com/ansys/pre-commit-hooks/pull/399>`_, `#402 <https://github.com/ansys/pre-commit-hooks/pull/402>`_

        * - Add `ansys/actions/check-vulnerabilities` action and `security.md` file
          - `#324 <https://github.com/ansys/pre-commit-hooks/pull/324>`_

        * - Add `codeowners` file
          - `#325 <https://github.com/ansys/pre-commit-hooks/pull/325>`_

        * - Use trusted publishers approach for releases
          - `#336 <https://github.com/ansys/pre-commit-hooks/pull/336>`_

        * - Update missing or outdated files
          - `#367 <https://github.com/ansys/pre-commit-hooks/pull/367>`_

        * - Add dependabot cooldown settings
          - `#384 <https://github.com/ansys/pre-commit-hooks/pull/384>`_


`0.5.2 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.5.2>`_ - February 26, 2025
============================================================================================

.. tab-set::

  .. tab-item:: Dependencies

    .. list-table::
        :header-rows: 0
        :widths: auto


        * - bump ansys-sphinx-theme[autoapi] from 1.2.4 to 1.2.6
          - `#279 <https://github.com/ansys/pre-commit-hooks/pull/279>`_

        * - bump sphinx-autodoc-typehints from 3.0.0 to 3.0.1
          - `#281 <https://github.com/ansys/pre-commit-hooks/pull/281>`_

        * - bump importlib-metadata from 8.5.0 to 8.6.1
          - `#283 <https://github.com/ansys/pre-commit-hooks/pull/283>`_

        * - bump semver from 3.0.2 to 3.0.4
          - `#284 <https://github.com/ansys/pre-commit-hooks/pull/284>`_

        * - bump ansys-sphinx-theme[autoapi] from 1.2.6 to 1.3.1
          - `#287 <https://github.com/ansys/pre-commit-hooks/pull/287>`_

        * - bump sphinx-autodoc-typehints from 3.0.1 to 3.1.0
          - `#290 <https://github.com/ansys/pre-commit-hooks/pull/290>`_

        * - bump ansys-sphinx-theme[autoapi] from 1.3.1 to 1.3.2
          - `#291 <https://github.com/ansys/pre-commit-hooks/pull/291>`_

        * - bump sphinx from 8.1.3 to 8.2.1
          - `#292 <https://github.com/ansys/pre-commit-hooks/pull/292>`_

  .. tab-item:: Documentation

    .. list-table::
        :header-rows: 0
        :widths: auto


        * - Improve documentation
          - `#289 <https://github.com/ansys/pre-commit-hooks/pull/289>`_

  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto


        * - Bump `ansys-pre-commit-hooks` from 0.4.4 to 0.5.1
          - `#276 <https://github.com/ansys/pre-commit-hooks/pull/276>`_

        * - pre-commit automatic update
          - `#285 <https://github.com/ansys/pre-commit-hooks/pull/285>`_, `#286 <https://github.com/ansys/pre-commit-hooks/pull/286>`_, `#288 <https://github.com/ansys/pre-commit-hooks/pull/288>`_, `#293 <https://github.com/ansys/pre-commit-hooks/pull/293>`_

`0.5.1 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.5.1>`_ - January 17, 2025
===========================================================================================

Fixed
^^^^^

- fix: Update license headers and fix broken tests `#271 <https://github.com/ansys/pre-commit-hooks/pull/271>`_
- fix: Fix "success" statements being printed and LICENSE file updates `#273 <https://github.com/ansys/pre-commit-hooks/pull/273>`_


Dependencies
^^^^^^^^^^^^

- build(deps-dev): bump ansys-sphinx-theme[autoapi] from 1.2.0 to 1.2.1 `#257 <https://github.com/ansys/pre-commit-hooks/pull/257>`_
- build(deps-dev): bump ansys-sphinx-theme[autoapi] from 1.2.1 to 1.2.2 `#259 <https://github.com/ansys/pre-commit-hooks/pull/259>`_
- build(deps-dev): bump pytest from 8.3.3 to 8.3.4 `#260 <https://github.com/ansys/pre-commit-hooks/pull/260>`_
- build(deps-dev): bump ansys-sphinx-theme[autoapi] from 1.2.2 to 1.2.3 `#264 <https://github.com/ansys/pre-commit-hooks/pull/264>`_
- build(deps): bump jinja2 from 3.1.4 to 3.1.5 `#267 <https://github.com/ansys/pre-commit-hooks/pull/267>`_
- build(deps-dev): bump ansys-sphinx-theme[autoapi] from 1.2.3 to 1.2.4 `#268 <https://github.com/ansys/pre-commit-hooks/pull/268>`_
- build(deps): bump gitpython from 3.1.43 to 3.1.44 `#269 <https://github.com/ansys/pre-commit-hooks/pull/269>`_
- build(deps-dev): bump sphinx-autodoc-typehints from 2.5.0 to 3.0.0 `#270 <https://github.com/ansys/pre-commit-hooks/pull/270>`_


Miscellaneous
^^^^^^^^^^^^^

- [pre-commit.ci] pre-commit autoupdate `#272 <https://github.com/ansys/pre-commit-hooks/pull/272>`_


Maintenance
^^^^^^^^^^^

- chore: Update code for reuse v5.0.2 `#263 <https://github.com/ansys/pre-commit-hooks/pull/263>`_
- chore: Use `pathlib.Path` instead of `os` in add_license_headers.py `#266 <https://github.com/ansys/pre-commit-hooks/pull/266>`_
- Update changelog file and fragment files `#275 <https://github.com/ansys/pre-commit-hooks/pull/275>`_

`0.4.4 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.4.4>`_ - November 07, 2024
============================================================================================

Fixed
^^^^^

- fix: there is no "owner" of libraries `#233 <https://github.com/ansys/pre-commit-hooks/pull/233>`_
- fix: LICENSE line endings `#236 <https://github.com/ansys/pre-commit-hooks/pull/236>`_
- fix: AUTHORS and CONTRIBUTORS.md files `#240 <https://github.com/ansys/pre-commit-hooks/pull/240>`_

Dependencies
^^^^^^^^^^^^

- build(deps-dev): bump sphinx from 7.4.7 to 8.0.2 `#212 <https://github.com/ansys/pre-commit-hooks/pull/212>`_
- build(deps-dev): bump numpydoc from 1.7.0 to 1.8.0 `#218 <https://github.com/ansys/pre-commit-hooks/pull/218>`_
- build(deps-dev): bump ansys-sphinx-theme[autoapi] from 1.0.3 to 1.0.5 `#222 <https://github.com/ansys/pre-commit-hooks/pull/222>`_
- build(deps-dev): bump ansys-sphinx-theme[autoapi] from 1.0.5 to 1.0.7 `#223 <https://github.com/ansys/pre-commit-hooks/pull/223>`_
- build(deps): bump importlib-metadata from 8.2.0 to 8.4.0 `#224 <https://github.com/ansys/pre-commit-hooks/pull/224>`_
- build(deps-dev): bump ansys-sphinx-theme[autoapi] from 1.0.7 to 1.0.8 `#227 <https://github.com/ansys/pre-commit-hooks/pull/227>`_
- build(deps-dev): bump sphinx-autodoc-typehints from 2.3.0 to 2.4.0 `#228 <https://github.com/ansys/pre-commit-hooks/pull/228>`_
- build(deps): bump importlib-metadata from 8.4.0 to 8.5.0 `#229 <https://github.com/ansys/pre-commit-hooks/pull/229>`_
- build(deps-dev): bump pytest from 8.3.2 to 8.3.3 `#230 <https://github.com/ansys/pre-commit-hooks/pull/230>`_
- build(deps-dev): bump sphinx-autodoc-typehints from 2.4.0 to 2.4.1 `#231 <https://github.com/ansys/pre-commit-hooks/pull/231>`_
- build(deps-dev): bump ansys-sphinx-theme[autoapi] from 1.0.8 to 1.0.11 `#234 <https://github.com/ansys/pre-commit-hooks/pull/234>`_
- build(deps-dev): bump sphinx-autodoc-typehints from 2.4.1 to 2.4.4 `#235 <https://github.com/ansys/pre-commit-hooks/pull/235>`_
- build(deps-dev): bump ansys-sphinx-theme[autoapi] from 1.0.11 to 1.1.2 `#242 <https://github.com/ansys/pre-commit-hooks/pull/242>`_
- build(deps-dev): bump sphinx from 8.0.2 to 8.1.3 `#246 <https://github.com/ansys/pre-commit-hooks/pull/246>`_
- build(deps-dev): bump ansys-sphinx-theme[autoapi] from 1.1.2 to 1.1.3 `#247 <https://github.com/ansys/pre-commit-hooks/pull/247>`_
- build(deps-dev): bump sphinx-autodoc-typehints from 2.4.4 to 2.5.0 `#248 <https://github.com/ansys/pre-commit-hooks/pull/248>`_
- build(deps-dev): bump ansys-sphinx-theme[autoapi] from 1.1.6 to 1.1.7 `#252 <https://github.com/ansys/pre-commit-hooks/pull/252>`_
- build(deps-dev): bump ansys-sphinx-theme[autoapi] from 1.1.7 to 1.2.0 `#255 <https://github.com/ansys/pre-commit-hooks/pull/255>`_
- build(deps-dev): bump pytest-cov from 5.0.0 to 6.0.0 `#256 <https://github.com/ansys/pre-commit-hooks/pull/256>`_

Miscellaneous
^^^^^^^^^^^^^

- [pre-commit.ci] pre-commit autoupdate `#221 <https://github.com/ansys/pre-commit-hooks/pull/221>`_, `#225 <https://github.com/ansys/pre-commit-hooks/pull/225>`_, `#237 <https://github.com/ansys/pre-commit-hooks/pull/237>`_, `#245 <https://github.com/ansys/pre-commit-hooks/pull/245>`_, `#249 <https://github.com/ansys/pre-commit-hooks/pull/249>`_
- chore: update CONTRIBUTORS.md to match guide lines `#254 <https://github.com/ansys/pre-commit-hooks/pull/254>`_

Documentation
^^^^^^^^^^^^^

- build(deps-dev): bump ansys-sphinx-theme[autoapi] from 0.16.6 to 1.0.3 `#219 <https://github.com/ansys/pre-commit-hooks/pull/219>`_
- build(deps-dev): bump sphinx-autodoc-typehints from 2.2.3 to 2.3.0 `#226 <https://github.com/ansys/pre-commit-hooks/pull/226>`_
- build(deps-dev): bump ansys-sphinx-theme[autoapi] from 1.1.3 to 1.1.6 `#251 <https://github.com/ansys/pre-commit-hooks/pull/251>`_

Maintenance
^^^^^^^^^^^

- build(deps): bump ansys/actions from 6 to 7 `#220 <https://github.com/ansys/pre-commit-hooks/pull/220>`_
- CHORE: Add hacktoberfest labels `#241 <https://github.com/ansys/pre-commit-hooks/pull/241>`_
- build(deps): bump ansys/actions from 7 to 8 `#243 <https://github.com/ansys/pre-commit-hooks/pull/243>`_

`0.4.3 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.4.3>`_ - August 07, 2024
==========================================================================================

Added
^^^^^

- feat: leverage reuse vcs Git strategy `#217 <https://github.com/ansys/pre-commit-hooks/pull/217>`_

Maintenance
^^^^^^^^^^^

- [pre-commit.ci] pre-commit autoupdate `#213 <https://github.com/ansys/pre-commit-hooks/pull/213>`_

`0.4.2 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.4.2>`_ - August 01, 2024
==========================================================================================

Changed
^^^^^^^

- chore: update CHANGELOG for v0.4.1 `#201 <https://github.com/ansys/pre-commit-hooks/pull/201>`_
- Bump version to v0.4.1 and uncomment tech review hook `#202 <https://github.com/ansys/pre-commit-hooks/pull/202>`_
- chore: adjust add-license-headers script to work with reuse 4.0.3 `#211 <https://github.com/ansys/pre-commit-hooks/pull/211>`_

Dependencies
^^^^^^^^^^^^

- build(deps-dev): bump sphinx from 7.4.0 to 7.4.7 `#204 <https://github.com/ansys/pre-commit-hooks/pull/204>`_
- build(deps-dev): bump pytest from 8.2.2 to 8.3.1 `#206 <https://github.com/ansys/pre-commit-hooks/pull/206>`_
- build(deps): bump importlib-metadata from 8.0.0 to 8.2.0 `#207 <https://github.com/ansys/pre-commit-hooks/pull/207>`_
- build(deps-dev): bump pytest from 8.3.1 to 8.3.2 `#208 <https://github.com/ansys/pre-commit-hooks/pull/208>`_

Miscellaneous
^^^^^^^^^^^^^

- chore: update code base to fix bandit warnings `#209 <https://github.com/ansys/pre-commit-hooks/pull/209>`_
- [pre-commit.ci] pre-commit autoupdate `#210 <https://github.com/ansys/pre-commit-hooks/pull/210>`_

`0.4.1 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.4.1>`_ - July 15, 2024
========================================================================================

Changed
^^^^^^^

- chore: update CHANGELOG for v0.4.0 `#193 <https://github.com/ansys/pre-commit-hooks/pull/193>`_

Fixed
^^^^^

- Fix semantic versioning check in tech-review hook `#194 <https://github.com/ansys/pre-commit-hooks/pull/194>`_

Dependencies
^^^^^^^^^^^^

- build(deps): bump sphinx from 7.3.7 to 7.4.0 `#198 <https://github.com/ansys/pre-commit-hooks/pull/198>`_

Miscellaneous
^^^^^^^^^^^^^

- [pre-commit.ci] pre-commit autoupdate `#196 <https://github.com/ansys/pre-commit-hooks/pull/196>`_

`0.4.0 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.4.0>`_ - July 01, 2024
========================================================================================

Added
^^^^^

- feat: technical review hook `#183 <https://github.com/ansys/pre-commit-hooks/pull/183>`_

Changed
^^^^^^^

- chore: update CHANGELOG for v0.3.2 `#186 <https://github.com/ansys/pre-commit-hooks/pull/186>`_

Dependencies
^^^^^^^^^^^^

- build(deps): bump importlib-metadata from 7.1.0 to 7.2.1 `#187 <https://github.com/ansys/pre-commit-hooks/pull/187>`_
- build(deps): bump sphinx-autodoc-typehints from 2.1.1 to 2.2.2 `#188 <https://github.com/ansys/pre-commit-hooks/pull/188>`_
- build(deps): bump ansys-sphinx-theme[autoapi] from 0.16.5 to 0.16.6 `#189 <https://github.com/ansys/pre-commit-hooks/pull/189>`_
- build(deps): bump importlib-metadata from 7.2.1 to 8.0.0 `#192 <https://github.com/ansys/pre-commit-hooks/pull/192>`_

Miscellaneous
^^^^^^^^^^^^^

- [pre-commit.ci] pre-commit autoupdate `#190 <https://github.com/ansys/pre-commit-hooks/pull/190>`_

`0.3.2 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.3.2>`_ - June 20, 2024
========================================================================================

Fixed
^^^^^

- fix: add recursive argument and code to add-license-headers `#185 <https://github.com/ansys/pre-commit-hooks/pull/185>`_

Dependencies
^^^^^^^^^^^^

- build(deps): bump pytest from 8.1.1 to 8.2.0 `#172 <https://github.com/ansys/pre-commit-hooks/pull/172>`_
- build(deps): bump ansys-sphinx-theme[autoapi] from 0.15.2 to 0.16.0 `#175 <https://github.com/ansys/pre-commit-hooks/pull/175>`_
- build(deps): bump pytest from 8.2.0 to 8.2.1 `#176 <https://github.com/ansys/pre-commit-hooks/pull/176>`_
- build(deps): bump ansys-sphinx-theme[autoapi] from 0.16.0 to 0.16.2 `#178 <https://github.com/ansys/pre-commit-hooks/pull/178>`_
- build(deps): bump ansys-sphinx-theme[autoapi] from 0.16.2 to 0.16.5 `#180 <https://github.com/ansys/pre-commit-hooks/pull/180>`_
- build(deps): bump pytest from 8.2.1 to 8.2.2 `#181 <https://github.com/ansys/pre-commit-hooks/pull/181>`_
- build(deps): bump sphinx-autodoc-typehints from 2.1.0 to 2.1.1 `#182 <https://github.com/ansys/pre-commit-hooks/pull/182>`_

Miscellaneous
^^^^^^^^^^^^^

- [pre-commit.ci] pre-commit autoupdate `#173 <https://github.com/ansys/pre-commit-hooks/pull/173>`_, `#174 <https://github.com/ansys/pre-commit-hooks/pull/174>`_, `#177 <https://github.com/ansys/pre-commit-hooks/pull/177>`_, `#179 <https://github.com/ansys/pre-commit-hooks/pull/179>`_, `#184 <https://github.com/ansys/pre-commit-hooks/pull/184>`_

`0.3.1 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.3.1>`_ - April 23, 2024
=========================================================================================

Changed
^^^^^^^

- chore: update CHANGELOG for v0.3.0 `#167 <https://github.com/ansys/pre-commit-hooks/pull/167>`_
- build(deps): bump ansys/actions from 5 to 6 `#170 <https://github.com/ansys/pre-commit-hooks/pull/170>`_

Dependencies
^^^^^^^^^^^^

- build(deps): bump sphinx from 7.2.6 to 7.3.7 `#168 <https://github.com/ansys/pre-commit-hooks/pull/168>`_
- build(deps): bump sphinx-autodoc-typehints from 2.0.1 to 2.1.0 `#169 <https://github.com/ansys/pre-commit-hooks/pull/169>`_

`0.3.0 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.3.0>`_ - April 18, 2024
=========================================================================================

Added
^^^^^

- feat: add doc-changelog and doc-deploy-changelog actions `#164 <https://github.com/ansys/pre-commit-hooks/pull/164>`_

Changed
^^^^^^^

- maint: bump reuse to v3.0.2 in add-license-headers `#163 <https://github.com/ansys/pre-commit-hooks/pull/163>`_

`0.2.9 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.2.9>`_ - February 16, 2024
============================================================================================

Changed
^^^^^^^

- Pinned all dependencies

`0.2.8 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.2.8>`_ - January 17, 2024
===========================================================================================

Fixed
^^^^^

- Add upper limit to reuse dependency

`0.2.7 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.2.7>`_ - January 16, 2024
===========================================================================================

Fixed
^^^^^

- Fix pytest python versions and fileinput `#118 <https://github.com/ansys/pre-commit-hooks/pull/118>`_

Dependencies
^^^^^^^^^^^^

- Bump `gitpython` from 3.1.40 to 3.1.41 `#120 <https://github.com/ansys/pre-commit-hooks/pull/120>`_
- Bump `ansys-sphinx-theme` from 0.13.0 to 0.13.1 `#121 <https://github.com/ansys/pre-commit-hooks/pull/121>`_

`0.2.6 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.2.6>`_ - January 11, 2024
===========================================================================================

Added
^^^^^

- Add full header to file if empty `#116 <https://github.com/ansys/pre-commit-hooks/pull/116>`_

`0.2.5 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.2.5>`_ - January 10, 2024
===========================================================================================

Added
^^^^^

- Added custom argument for the copyright's start year & updated add_hook_changes `#111 <https://github.com/ansys/pre-commit-hooks/pull/111>`_

`0.2.4 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.2.4>`_ - January 4, 2024
==========================================================================================

Fixed
^^^^^

- Apply hook changes after add-license-headers runs `#108 <https://github.com/ansys/pre-commit-hooks/pull/108>`_

`0.2.3 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.2.3>`_ - January 2, 2024
==========================================================================================

Changed
^^^^^^^

- Remove python 3.8 and add python 3.12 `#106 <https://github.com/ansys/pre-commit-hooks/pull/106>`_
- Update year to 2024 in license files `#107 <https://github.com/ansys/pre-commit-hooks/pull/107>`_

Dependencies
^^^^^^^^^^^^

- `pre-commit` autoupdate `#97 <https://github.com/ansys/pre-commit-hooks/pull/97>`_, `#99 <https://github.com/ansys/pre-commit-hooks/pull/99>`_, `#100 <https://github.com/ansys/pre-commit-hooks/pull/100>`_, `#103 <https://github.com/ansys/pre-commit-hooks/pull/103>`_
- Bump `actions/labeler` from 4 to 5 `#98 <https://github.com/ansys/pre-commit-hooks/pull/98>`_
- Bump `ansys/actions` from 4 to 5 `#102 <https://github.com/ansys/pre-commit-hooks/pull/102>`_
- Bump `pytest` from 7.4.3 to 7.4.4 `#104 <https://github.com/ansys/pre-commit-hooks/pull/104>`_

`0.2.2 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.2.2>`_ - November 15, 2023
============================================================================================

Added
^^^^^

- Add headers to tests and examples `#85 <https://github.com/ansys/pre-commit-hooks/pull/85>`_
- Add typehints to add-license-headers functions `#93 <https://github.com/ansys/pre-commit-hooks/pull/93>`_

Fixed
^^^^^

- Fix add-license-headers to keep edits from previously run hooks `#88 <https://github.com/ansys/pre-commit-hooks/pull/88>`_

Changed
^^^^^^^

- Remove dep5 files from repository `#89 <https://github.com/ansys/pre-commit-hooks/pull/89>`_
- Remove .reuse and LICENSES folders `#95 <https://github.com/ansys/pre-commit-hooks/pull/95>`_

Dependencies
^^^^^^^^^^^^

- Bump `sphinx-autodoc-typehints` from 1.24.0 to 1.25.2 `#86 <https://github.com/ansys/pre-commit-hooks/pull/86>`_, `#90 <https://github.com/ansys/pre-commit-hooks/pull/90>`_
- `pre-commit` autoupdate `#87 <https://github.com/ansys/pre-commit-hooks/pull/87>`_, `#94 <https://github.com/ansys/pre-commit-hooks/pull/94>`_
- Bump `ansys-sphinx-theme` from 0.12.4 to 0.12.5 `#91 <https://github.com/ansys/pre-commit-hooks/pull/91>`_

`0.2.1 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.2.1>`_ - October 31, 2023
===========================================================================================

Added
^^^^^

- Added difference check between original file and updated file `#77 <https://github.com/ansys/pre-commit-hooks/pull/77>`_

Dependencies
^^^^^^^^^^^^

- `pre-commit` autoupdate `#76 <https://github.com/ansys/pre-commit-hooks/pull/76>`_
- Bump `ansys-sphinx-theme` from 0.12.3 to 0.12.4 `#80 <https://github.com/ansys/pre-commit-hooks/pull/80>`_
- Bump `pytest` from 7.4.2 to 7.4.3 `#81 <https://github.com/ansys/pre-commit-hooks/pull/81>`_

`0.2.0 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.2.0>`_ - October 17, 2023
===========================================================================================

Added
^^^^^

- Added check_license argument `#64 <https://github.com/ansys/pre-commit-hooks/pull/64>`_
- Run hook on specific directories and files `#65 <https://github.com/ansys/pre-commit-hooks/pull/65>`_
- Update headers & improve unit tests `#69 <https://github.com/ansys/pre-commit-hooks/pull/69>`_
- Create assets folder with common REUSE templates `#72 <https://github.com/ansys/pre-commit-hooks/pull/72>`_
- Run add-license-headers hook serially `#74 <https://github.com/ansys/pre-commit-hooks/pull/74>`_

Changed
^^^^^^^

- Removed loc argument & passed in committed files `#57 <https://github.com/ansys/pre-commit-hooks/pull/57>`_

Dependencies
^^^^^^^^^^^^

- Bump `ansys-sphinx-theme` from 0.12.1 to 0.12.2 `#70 <https://github.com/ansys/pre-commit-hooks/pull/70>`_
- Bump `pre-commit` from v4.4.0 to v4.5.0 `#71 <https://github.com/ansys/pre-commit-hooks/pull/71>`_

`0.1.3 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.1.3>`_ - September 8, 2023
============================================================================================

Added
^^^^^

- Create custom flags for add-license-header `#44 <https://github.com/ansys/pre-commit-hooks/pull/44>`_

Changed
^^^^^^^

- Update descriptions for add-license-headers in README `#40 <https://github.com/ansys/pre-commit-hooks/pull/40>`_

`0.1.2 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.1.2>`_ - September 5, 2023
============================================================================================

Dependencies
^^^^^^^^^^^^

- [pre-commit.ci] pre-commit autoupdate `#39 <https://github.com/ansys/pre-commit-hooks/pull/39>`_

`0.1.1 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.1.1>`_ - September 4, 2023
============================================================================================

Added
^^^^^

- Directory checks & print statement updates `#34 <https://github.com/ansys/pre-commit-hooks/pull/34>`_

Dependencies
^^^^^^^^^^^^

- build(deps-dev): bump gitpython from 3.1.32 to 3.1.34 `#35 <https://github.com/ansys/pre-commit-hooks/pull/35>`_
- build(deps-dev): bump pytest from 7.3.0 to 7.4.1 `#38 <https://github.com/ansys/pre-commit-hooks/pull/38>`_
- build(deps-dev): bump sphinx from 7.2.4 to 7.2.5 `#37 <https://github.com/ansys/pre-commit-hooks/pull/37>`_
- build(deps-dev): bump ansys-sphinx-theme from 0.10.4 to 0.10.5 `#36 <https://github.com/ansys/pre-commit-hooks/pull/36>`_

`0.1.0 <https://github.com/ansys/pre-commit-hooks/releases/tag/v0.1.0>`_ - September 1, 2023
============================================================================================

Added
^^^^^

- Create pre-commit hook to add license header to all files `#7 <https://github.com/ansys/pre-commit-hooks/pull/7>`_
- Default args in pre-commit-hooks.yaml `#11 <https://github.com/ansys/pre-commit-hooks/pull/11>`_
- feat: ignore links (temp) `#20 <https://github.com/ansys/pre-commit-hooks/pull/20>`_

Changed
^^^^^^^

- Update the readme file `#21 <https://github.com/ansys/pre-commit-hooks/pull/21>`_
- Edits to RST and PY files `#28 <https://github.com/ansys/pre-commit-hooks/pull/28>`_

Fixed
^^^^^

- Fix add-license-headers for reuse version >=2 `#10 <https://github.com/ansys/pre-commit-hooks/pull/10>`_
- Fix reuse 2.0 implementation `#17 <https://github.com/ansys/pre-commit-hooks/pull/17>`_

.. vale on