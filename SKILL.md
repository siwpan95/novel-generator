---
name: novel-generator-asp
description: Maintain the novel_generator ASP template novel engine (本 SKILL.md 所在仓库根). Pure-stdlib offline novel generation.
agent_created: true
---

# novel_generator（ASP 模板流）维护

## 概述
ASP 模板流中文小说自动生成：多层嵌套循环 + 词库随机替换，纯标准库零运行依赖，可离线生成单章/整卷/全本。

## 结构
- run.py / main.py / unified_engine.py：CLI 入口与统一引擎
- engine/：章节、角色、战斗、叙事约束、词库
- word_banks/：题材词库 JSON；tests/：pytest；ARCHITECTURE.md：架构说明

## 常用命令
- python run.py --mode single --chapter-num 1 --seed 42
- python run.py --mode volume --volume-num 1 --chapters 7
- python -m novel_generator --help

## 已知陷阱
- 纯标准库约束：新功能不得引入第三方依赖
- 词库更新走 word_banks/ JSON，改代码前先读 ARCHITECTURE.md
