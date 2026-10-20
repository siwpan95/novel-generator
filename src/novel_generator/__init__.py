"""ASP 小说生成引擎 —— 多层嵌套循环 + 词库随机替换。

    用法：
        python -m novel_generator                        # 交互运行
        python -m novel_generator --mode single          # 生成单章
        python -m novel_generator --mode volume          # 生成整卷
        python -m novel_generator --mode full            # 全量生成
    """

__version__ = "2.0.0"
__description__ = "ASP 模板流小说自动生成引擎"

from .unified_engine import ASPNovelEngine, main

__all__ = ["ASPNovelEngine", "main"]
