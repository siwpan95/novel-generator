# novel_generator

## 仓库角色定位（投资组合分级 ②）

> 本仓在 siwpan 投资组合（D:/projects/repos，共 133 仓）中定级为 **② 保留**，领域 **小说/网文**。
> **角色**：小说库。
> **维护策略**：② 旗舰 / 枢纽仓库打磨保留，作为能力展示或收敛点；② 保留类仓库低优先维持、不主动扩张。
> 投资组合统一分级索引（多机可查）：[组合分级决策索引 · allin 事实源](https://gitee.com/siwpan/allin/blob/master/docs/事实源/组合分级决策索引.md)。

[![PyPI](https://img.shields.io/pypi/v/novel-generator.svg)](https://pypi.org/project/novel-generator/)
[![Python](https://img.shields.io/pypi/pyversions/novel-generator.svg)](https://pypi.org/project/novel-generator/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Gitee](https://img.shields.io/badge/Gitee-siwpan%2Fnovel--generator-orange.svg)](https://gitee.com/siwpan/novel-generator)

> 仓库：<https://gitee.com/siwpan/novel-generator> ｜ 许可：MIT（见 [LICENSE](LICENSE)）

**ASP 模板流中文小说自动生成引擎**：基于多层嵌套循环 + 词库随机替换，可离线生成单章、整卷乃至全本小说。

## 发行名 vs 导入名

| 用途 | 名字 |
|---|---|
| PyPI 发行名（`pip install`） | `novel-generator` |
| Python 导入名（`import`） | `novel_generator` |

两者不可混用：`pip install novel_generator` 也能装上（PyPI 会归一化），但**规范写法是 `novel-generator`**。

## 语言 / 类型

- 语言：Python 3（纯标准库，无第三方运行依赖）
- 类型：命令行程序（含 setuptools 打包，`python -m novel_generator` 可用）

## 目录要点

2.0.0 起改为 **src 布局**，包位于 `src/novel_generator/`（此前仓根即包根，靠 `pkg_alias.py` 注册别名，
该模块已随本次重构删除）：

- `src/novel_generator/`：包主体（`unified_engine.py` 统一引擎、`engine/` 生成器核心、`word_banks/` JSON 词库）
- `main.py` / `run.py` / `run.bat`：仓根启动脚本（内部把 `src/` 加入 `sys.path`）
- `tests/`：pytest 测试；`output/` / `release/`：历史生成产物（不进包）
- `ARCHITECTURE.md`：架构说明；`pyproject.toml`：打包配置

## 运行方式与依赖

无第三方运行依赖，Python >= 3.9。

```bash
# 安装（PyPI）
pip install novel-generator
novel-gen --mode single --chapter-num 1 --seed 42
python -m novel_generator --help

# 或仓库内直接跑（无需安装）
python run.py --mode single --chapter-num 1 --seed 42
python run.py --mode volume --volume-num 1 --chapters 7
```

## 测试状态

- `pytest tests -q`：**30 passed**（`tests/test_word_bank.py`、`test_template.py` 等）
- 运行：单章生成实测通过（`--mode single --chapter-num 1 --seed 42`）
- ⚠️ `tests/test_generation.py`、`tests/test_parameterization.py` 为**存量红灯**：
  二者引用 `UnifiedNovelEngine`、`engine.beat_orchestrator`、`engine.beat_narratives`、
  `engine.text_quality`——这些实现只存在于 `novel` 仓（事件驱动分支），本仓（ASP 模板流分支）没有，
  属测试文件跨仓误植，收集即失败。与本次 src 布局重构无关，重构前后同样失败。
