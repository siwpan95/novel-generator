#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ASP 小说生成引擎 启动脚本。"""

import sys
import os

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from novel_generator.unified_engine import main

if __name__ == "__main__":
    main()
