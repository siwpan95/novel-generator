"""主入口（demo 模式）。

ASP 模板流小说生成器 demo 和交互式入口。

推荐使用：
    python -m novel_generator                    # 统一CLI
    python -m novel_generator --help             # 查看选项
"""

import argparse
import sys
import os

# 将父目录和项目根目录都加入 sys.path，兼容直接 python main.py 运行
# 2026-09-23 去本地化：两个路径均由本文件位置推导，不再写死旧盘符绝对路径
_project_root = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_project_root)
sys.path.insert(0, _parent_dir)      # 上级目录 → import novel_generator.xxx
sys.path.insert(0, _project_root)    # 本仓根 → import engine.xxx
# 2026-09-23 修复：仓目录名（novel-generator）≠ 包名（novel_generator），
# 先用 pkg_alias 把仓根注册成 novel_generator 包，下面的 from novel_generator... 才能导入。
import pkg_alias
pkg_alias.install()

from novel_generator.engine.generators.novel import NovelGenerator
from novel_generator.engine.generators.character import CharacterGenerator
from novel_generator.engine.generators.chapter import ChapterGenerator
from novel_generator.engine.word_bank import WordBank
from novel_generator.unified_engine import ASPNovelEngine


def demo_single_chapter():
    """演示：生成单章样本（增强模式）。"""
    print("=" * 60)
    print("  单章样本生成（增强叙事模式）")
    print("=" * 60)

    engine = ASPNovelEngine(seed=42)
    chapter = engine.generate_single_chapter(
        chapter_num=1,
        volume_title="《厨艺巨校的故事 之 冷峻奇特的面条》",
        opponent_count=2,
        seed=42,
    )

    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "output", "sample_chapter.txt"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(chapter)

    print(f"\n样本章节已生成，共 {len(chapter):,} 字")
    print(f"输出文件：{output_path}")
    print(f"\n前500字预览：")
    print("-" * 40)
    print(chapter[:500])
    print("...")


def demo_single_character():
    """演示：生成单个角色描写。"""
    print("=" * 60)
    print("  单角色生成演示")
    print("=" * 60)

    wb = WordBank(seed=42)
    char_gen = CharacterGenerator(wb)

    # 生成3个角色
    for i in range(3):
        char = char_gen.generate()
        intro = char_gen.format_character_intro(char)
        print(f"\n--- 角色 {i+1}：{char['name']} ---")
        print(intro[:400])
        print(f"...(总计 {len(intro):,} 字)")

    print("\n" + "=" * 60)


def interactive_prompt():
    """交互式生成。"""
    print("\n" + "=" * 60)
    print("  《宇宙巨校闪级生》风格小说生成器 v1.0")
    print("=" * 60)
    print()
    print("基于 ASP 多层嵌套循环 + 词库随机替换的注水风格写作程序。")
    print()
    print("可选模式：")
    print("  1. 演示：生成单章样本")
    print("  2. 演示：生成角色描写")
    print("  3. 完整生成：多部小说")
    print("  4. 自定义参数生成")
    print()

    choice = input("请选择模式 [1/2/3/4] (默认1): ").strip() or "1"

    if choice == "1":
        demo_single_chapter()
    elif choice == "2":
        demo_single_character()
    elif choice == "3":
        volumes = input("部数 [默认3]: ").strip() or "3"
        engine = ASPNovelEngine(seed=42)
        engine.generate_full_novel(volumes=int(volumes))
    elif choice == "4":
        volumes = int(input("部数 [默认3]: ").strip() or "3")
        chapters = int(input("每部章数 [默认7]: ").strip() or "7")
        opponents = int(input("每章对手数 [默认4]: ").strip() or "4")
        seed = int(input("随机种子 [默认42]: ").strip() or "42")
        engine = ASPNovelEngine(seed=seed)
        engine.generate_full_novel(
            volumes=volumes,
            chapters_per_volume=chapters,
            opponents_per_chapter=opponents,
        )
    else:
        print("无效选择。")
        return


def main():
    parser = argparse.ArgumentParser(
        description="《宇宙巨校闪级生》风格小说生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python -m novel_generator.main --demo-chapter    # 生成单章样本
  python -m novel_generator.main --demo-character   # 演示角色生成
  python -m novel_generator.main -v 3 -c 7 -o 4    # 生成3部小说
  python -m novel_generator.main                    # 交互式菜单
        """,
    )

    parser.add_argument("--demo-chapter", action="store_true", help="生成单章样本")
    parser.add_argument("--demo-character", action="store_true", help="演示角色生成")
    parser.add_argument("-v", "--volumes", type=int, default=3, help="部数 (默认3)")
    parser.add_argument("-c", "--chapters", type=int, default=7, help="每部章数 (默认7)")
    parser.add_argument("-o", "--opponents", type=int, default=4, help="每章对手数 (默认4)")
    parser.add_argument("-s", "--seed", type=int, default=42, help="随机种子 (默认42)")
    parser.add_argument("--output", type=str, default=None, help="输出目录")

    args = parser.parse_args()

    if args.demo_chapter:
        demo_single_chapter()
    elif args.demo_character:
        demo_single_character()
    elif len(sys.argv) == 1:
        # 无参数：交互式菜单
        interactive_prompt()
    else:
        # 命令行参数模式
        engine = ASPNovelEngine(seed=args.seed)
        engine.generate_full_novel(
            volumes=args.volumes,
            chapters_per_volume=args.chapters,
            opponents_per_chapter=args.opponents,
            output_dir=args.output,
        )


if __name__ == "__main__":
    main()
