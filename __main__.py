"""novel_generator 包入口。"""
# 2026-09-23 修复：仓目录名（novel-generator）≠ 包名（novel_generator），
# 先用 pkg_alias 把仓根注册成 novel_generator 包，下面的 from novel_generator... 才能导入。
import pkg_alias
pkg_alias.install()

from novel_generator.unified_engine import main

if __name__ == "__main__":
    main()
