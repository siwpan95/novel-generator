"""novel_generator 包入口。"""
# src 布局：包在 src/novel_generator/，直接 `python -m novel_generator` 即可，
# 无需 pkg_alias（1.0.0 起随仓库改为 src 布局，pkg_alias.py 已删除）。

from novel_generator.unified_engine import main

if __name__ == "__main__":
    main()
