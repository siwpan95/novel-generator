# Changelog

本项目所有值得注意的变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [2.0.0] - 2026-10-20

**PyPI 首发**：<https://pypi.org/project/novel-generator/2.0.0/>（发行名 `novel-generator`，导入名 `novel_generator`）。

> 注：本次沿用了代码内既有的 2.0.0 版本号（`src/novel_generator/__init__.py` 的 `__version__`），
> 未另起 1.0.0 —— 以免 PyPI 版本与仓库版本互相矛盾。CHANGELOG 中此前的 `## [1.0.0] - 2026-08-27`
> 记的是 2026-08-27 那次 Gitee release（便携源码 zip），与本次 PyPI 首发不是同一条序列。

### Added

- `pyproject.toml` 补齐打包配置（此前 `build-backend` 写成不存在的
  `setuptools.backends._legacy:_Backend`，且 `packages.find` 的 `include = ["novel_generator*"]`
  在仓根找不到同名目录 —— 两个问题叠加导致**根本构建不出包**）。
- 控制台入口 `novel-gen`（`novel_generator.unified_engine:main`）；`python -m novel_generator` 亦可用。
- 26 个 `word_banks/*.json` 随包分发（`package-data`）。

### Changed

- **改为 src 布局**：`__init__.py` / `__main__.py` / `unified_engine.py` / `engine/` / `word_banks/`
  迁入 `src/novel_generator/`。
- 混用的两种导入统一为绝对导入 `from novel_generator.engine.xxx import ...`
  （原 `unified_engine.py` 用 `from engine.` 共 13 处）。

### Removed

- `pkg_alias.py`：它存在的唯一理由是「仓目录名 novel-generator ≠ 包名 novel_generator，
  需把仓根注册成包」。src 布局后仓根不再是包，该模块连同 3 处自举调用一并删除。

### Fixed

- **pytest 30 个 ERROR 全部修复**（30 ERROR → 30 passed）。根因是仓根有 `__init__.py`，
  pytest 沿 `tests/__init__.py` 上溯把仓根当包导入，触发
  `ImportError: attempted relative import with no known parent package`。src 布局后仓根无 `__init__.py`，
  该问题从根上消失。
- `engine/output/` 下 9MB 历史生成产物（3 个 txt）不再进 wheel（`packages.find` 显式 exclude）。

### Known issues

- `tests/test_generation.py`、`tests/test_parameterization.py` 仍为收集失败（存量）：
  二者引用 `UnifiedNovelEngine`、`engine.beat_orchestrator`、`engine.beat_narratives`、
  `engine.text_quality`，这些实现只存在于 `novel` 仓（事件驱动分支），本仓没有，
  属测试文件跨仓误植。重构前后同样失败，待处置。

## [1.0.0] - 2026-08-27

### Added

- 首个发行版：便携源码 zip（剔除 .venv/构建产物/输出物，依赖见 README）。
- 发布面：gitee [siwpan/novel-generator](https://gitee.com/siwpan/novel-generator) release `v1.0.0`（novel_generator v1.0.0）。