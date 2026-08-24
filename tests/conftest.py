"""共享测试 fixtures。"""
import json
import os
import sys
import tempfile

import pytest

# 将项目根目录加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

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
