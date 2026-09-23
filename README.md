# novel_generator

> 仓库：<https://gitee.com/siwpan/novel-generator> ｜ 许可：MIT（见 [LICENSE](LICENSE)）

**ASP 模板流中文小说自动生成引擎**：基于多层嵌套循环 + 词库随机替换，可离线生成单章、整卷乃至全本小说。

## 语言 / 类型

- 语言：Python 3（纯标准库，无第三方运行依赖）
- 类型：命令行程序（含 setuptools 打包，`python -m novel_generator` 可用）

## 目录要点

- `main.py` / `run.py` / `unified_engine.py`：命令行入口与统一引擎
- `engine/`：生成器核心（章节、角色、战斗、叙事约束、词库等）
- `word_banks/`：各类 JSON 词库（修仙、科幻、克苏鲁、武侠等题材）
- `tests/`：pytest 测试；`output/`：历史生成结果
- `ARCHITECTURE.md`：架构说明；`pyproject.toml`：打包配置

## 运行方式与依赖

无第三方运行依赖，Python >= 3.9。

```bash
python run.py --mode single --chapter-num 1 --seed 42
python run.py --mode volume --volume-num 1 --chapters 7
python -m novel_generator --help
```

## 测试状态

- 语法检查：通过（34 个 `.py` 文件无语法错误）
- 运行：单章生成实测通过（`--mode single --chapter-num 1 --seed 42`，输出 3412 字，退出码 0）
