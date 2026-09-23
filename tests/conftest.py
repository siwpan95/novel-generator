"""共享测试 fixtures。"""
import json
import os
import sys
import tempfile

import pytest

# 将项目根目录加入 sys.path
# 2026-09-23 修复：原来插入的是「仓根的上两级」（G:\），而包名 novel_generator 并不在那个目录下，
# 故 from novel_generator... 必然失败。改为：插入仓根 + 用 pkg_alias 注册包别名（与 main.py 同一套做法）。
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
import pkg_alias  # noqa: E402
pkg_alias.install()

from novel_generator.engine.word_bank import WordBank
from novel_generator.engine.context_manager import ContextManager


@pytest.fixture
def empty_context():
    """创建一个空的 ContextManager 实例（用于需要上下文的测试）。"""
    return ContextManager()


@pytest.fixture
def seeded_word_bank():
    """固定 seed 的 WordBank（确定性输出）。"""
    return WordBank(seed=42)


@pytest.fixture
def temp_word_bank_dir():
    """创建临时词库目录，包含最小测试用词库。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_bank = {
            "test_key": ["alpha", "beta", "gamma"],
            "emotions": ["愤怒", "悲伤", "喜悦"],
            "senses": ["视觉", "听觉", "触觉"],
        }
        bank_path = os.path.join(tmpdir, 'test_bank.json')
        with open(bank_path, 'w', encoding='utf-8') as f:
            json.dump(test_bank, f, ensure_ascii=False)
        yield tmpdir
