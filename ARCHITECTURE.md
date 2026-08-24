# ASP 模板流小说生成引擎 v2.0 — 架构文档

## 1. 项目概述

**ASP 模板流**是一种纯规则驱动的程序化文本生成技术路线。其核心原理：

> 多层嵌套循环 × 词库随机替换 = 海量注水小说

灵感来源于《宇宙巨校闪级生》（约5000万字），通过6层嵌套循环驱动111部×11卷×5章的庞大结构，每层循环驱动对应的JSON词库随机挑选，实现天文数字级的文本组合空间。

### 技术特色（v2.0 增强）

| 能力 | 说明 |
|------|------|
| 多层嵌套循环 | 部→卷→章→段→句→词，6层驱动 |
| 词库随机替换 | 27+ JSON词库，`{{bank.key}}` 占位符系统 |
| 高级修饰符 | 加权、分类过滤、重复避免、回退链 |
| 状态变量 | `$var{default}` 跨模板持久化 |
| 条件分支 | `{{?var=value}}...{{/}}` 上下文敏感 |
| Tracery语法 | 动态语法注册表 + 权重规则 + 情感适配 |
| 节奏控制 | 强度曲线 + 句式分布 + 章节分段编排 |
| 上下文管理 | 人物状态、世界状态、叙事弧线、事件日志 |
| 上下文缓存 | 同上下文模板结果一致性 |

---

## 2. 项目结构

```
novel_generator/
├── __init__.py              # 包定义 (ASPNovelEngine 导出)
├── __main__.py              # python -m 入口
├── main.py                  # 交互式/demo 入口
├── run.py                   # 独立启动脚本
├── run.bat                  # Windows 批处理启动
├── unified_engine.py        # ★ 统一引擎：整合所有ASP模块
├── pyproject.toml           # 项目配置
├── ARCHITECTURE.md          # 本文档
│
├── engine/                  # ★ 核心引擎模块
│   ├── __init__.py          # 引擎导出
│   ├── word_bank.py         # 词库引擎（增强版）
│   ├── template.py          # 模板引擎（增强版）
│   ├── tracery_grammar.py   # Tracery语法适配器（增强版）
│   ├── multi_layer_engine.py # 多层嵌套循环引擎
│   ├── flash_marker.py      # 闪记标记强化
│   ├── structure_framework.py # 111部×11卷结构框架
│   ├── monster_generator.py # 怪物生成器
│   ├── batch_writer.py      # 批量并行写作
│   ├── propp_functions.py   # Propp叙事功能模板
│   ├── character_drive.py   # 角色驱动模块
│   ├── narrative_constraints.py # 叙事约束模块
│   ├── word_bank_builder.py # 词库构建器
│   │
│   ├── sentence_rhythm.py   # ★ NEW: 句子节奏与章法控制
│   ├── context_manager.py   # ★ NEW: 上下文状态管理
│   │
│   └── generators/          # 生成器集合
│       ├── __init__.py
│       ├── novel.py          # 整部小说生成器
│       ├── chapter.py        # 单章生成器
│       ├── character.py      # 角色生成器
│       ├── battle.py         # 战斗场面生成器
│       └── dialogue.py       # 对话生成器
│
├── word_banks/              # JSON 词库（27个文件）
│   ├── actions.json         # 动作词库
│   ├── adjectives.json      # 形容词词库
│   ├── weapons.json         # 武器词库
│   ├── ... (共27个词库文件)
│   └── names.json           # 名字词库
│
├── tests/                   # 单元测试
│   ├── conftest.py
│   ├── test_template.py
│   ├── test_word_bank.py
│   ├── test_generation.py
│   └── test_parameterization.py
│
└── output/                  # 生成输出（运行时创建）
```

---

## 3. 核心模块详解

### 3.1 TemplateEngine（template.py）

增强版模板引擎，支持 `{{bank.key:modifiers}}` 语法。

**基础语法：**
```
{{actions.attack}}                → 基础随机选取
{{weapons.sword:w}}               → 权重随机
{{emotions.anger:c=dark}}         → 按分类过滤
{{names.hero:u}}                  → 避免重复
{{moves.special:f=default.basic}} → 回退链
{{items.loot:e=垃圾,普通物品}}    → 排除指定项
```

**状态变量：**
```
$hero_name{张三}  → 首次使用"张三"，后续保持不变
```

**条件分支：**
```
{{?phase=climax}}激烈战斗！{{/}} → 仅在climax阶段输出
```

**上下文缓存：**
```python
engine.resolve_with_context(text, context={"scene": "forest"})
# 同样上下文+同样模板 → 同样结果（一致性）
```

### 3.2 WordBank（word_bank.py）

增强版词库引擎，在原有基础上新增：

| 方法 | 功能 |
|------|------|
| `pick_weighted()` | 按权重随机选取 |
| `pick_by_category()` | 按分类标签过滤 |
| `pick_fallback()` | 失败时沿回退链尝试 |
| `pick_unique()` | 避免最近重复（滑动窗口） |
| `pool()` | 暴露完整词池（供Tracery使用） |

### 3.3 SentenceRhythmEngine（sentence_rhythm.py）

句子节奏与章法控制。核心概念：

```
强度曲线 (Intensity Curve)
  1.0 ┤          ╭──╮
  0.5 ┤    ╭─────╯  ╰──╮
  0.0 ┤────╯            ╰────
       opening → build → climax → ending

高强度 → 短句（冲击力）
低强度 → 长句（铺陈描述）
```

**预设节奏配置：**
- `build_up` — 线性递增，句长中长
- `climax` — 高位震荡，句短有力
- `resolution` — 渐降收束
- `breather` — 低位轻震，过渡休息
- `exposition` — 中位缓动，说明性文字

**ChapterRhythmOrchestrator** 将章节分为6段：
```
opening(0-15%) → build_1(15-35%) → midpoint(35-55%) 
→ build_2(55-75%) → climax_peak(75-90%) → ending(90-100%)
```

### 3.4 ContextManager（context_manager.py）

全局上下文状态追踪：

- **人物状态**：姓名、情绪、位置、属性
- **世界状态**：时间、天气、地点、场景编号
- **叙事弧线**：部/卷/章位置、阶段、紧张度
- **事件日志**：历史事件，供后文引用
- **关系图**：人物之间关系强度追踪
- **序列化**：支持 JSON 保存/加载（断点续写）

### 3.5 TraceryAdapter（tracery_grammar.py）

将 Tracery 语法与 ASP 词库桥接：

- **动态语法注册表**：`register()` 注册语法规则集
- **命名空间隔离**：不同场景/世界用不同语法包
- **权重分支**：`{"text": "...", "weight": 3}` 加权选择
- **情感适配**：按 `emotion` 标签过滤分支
- **语法模块组合**：`merge_namespace()` 合并多个包
- **预设语法包**：combat / psychology / environment / dialogue

### 3.6 ASPNovelEngine（unified_engine.py）

统一入口引擎，整合所有模块：

```python
engine = ASPNovelEngine(seed=42)

# 全量生成（巨校模式）
engine.generate_full_novel(volumes=20)

# 单章生成
engine.generate_single_chapter(chapter_num=1)

# 整卷生成
engine.generate_volume(volume_num=1, volume_title="厨艺巨校")

# 上下文管理
engine.save_context("checkpoint.json")
engine.load_context("checkpoint.json")  # 断点续写
```

---

## 4. 数据流

```
[CLI 参数]
    │
    ▼
[ASPNovelEngine]  ◄── 统一调度
    │
    ├── [WordBank]        加载27个JSON词库
    ├── [TemplateEngine]   解析 {{bank.key:modifiers}}
    ├── [ContextManager]   追踪人物/世界/叙事状态
    ├── [SentenceRhythm]   控制句长/段落/节奏
    └── [TraceryAdapter]   动态语法规则
    │
    ▼
[MultiLayerEngine]  6层嵌套循环
    │
    ├── NovelGenerator   → 全量生成
    ├── ChapterGenerator → 单章生成
    ├── CharacterGenerator → 角色生成
    ├── BattleGenerator  → 战斗生成
    └── DialogueGenerator → 对话生成
    │
    ▼
[输出]  output/*.txt
```

---

## 5. 使用方法

```bash
# 交互式菜单
python main.py

# 生成单章
python -m novel_generator --mode single --chapter-num 1

# 生成整卷
python -m novel_generator --mode volume --volume-num 1 --volume-title "厨艺巨校"

# 全量生成
python -m novel_generator --mode full --volumes 20

# Windows批处理
run.bat
```
