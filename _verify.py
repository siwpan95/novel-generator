"""综合验收测试"""
import sys
import io
# 修复GBK编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')

from engine.word_bank import WordBank
from engine.template import TemplateEngine
from engine.context_manager import ContextManager
from engine.sentence_rhythm import SentenceRhythmEngine
from engine.tracery_grammar import TraceryAdapter
from unified_engine import ASPNovelEngine

# 1. 模板引擎 + Tracery
print('=== Test 1: Template + Tracery ===')
wb = WordBank(seed=42)
te = TemplateEngine(wb, seed=42)
ta = TraceryAdapter(wb)
ta.register_preset_grammars()

r1 = te.resolve('测试$var1{hello} {{?var1=hello}}成功{{/}}')
print(f'  State var + condition: {r1}')
assert 'hello' in r1 and '成功' in r1

r2 = ta.resolve('#env_open#')
print(f'  Tracery env: {r2[:60]}...')
assert len(r2) > 0 and '缺失' not in r2

r3 = ta.resolve('#combat_sequence#')
print(f'  Tracery combat ({len(r3)} chars): {r3[:80]}')
assert len(r3) > 0

# 2. 统一引擎
print('\n=== Test 2: Unified Engine ===')
e = ASPNovelEngine(seed=42)
print(f'  Phase: {e.context.current_phase()}')
chars = e.context.list_characters()
print(f'  Characters: {chars}')
e.context.register_character('TestHero', mood='brave')
e.context.set_world('weather', '晴朗')
print(f'  Context: {e.get_context_info()}')

# 3. 上下文管理
print('\n=== Test 3: ContextManager ===')
cm = ContextManager()
cm.set_chapter(1, 1, 10)
print(f'  Chapter phase: {cm.current_phase()}, tension: {cm.current_tension():.2f}')
assert cm.current_phase() in ('opening', 'build', 'climax', 'ending')

# 4. 句子节奏
print('\n=== Test 4: Rhythm ===')
sr = SentenceRhythmEngine(seed=42)
sr.set_progress(0.5)
print(f'  Intensity at 50%: {sr.current_intensity():.2f}')
print(f'  Sentence length: {sr.target_sentence_length()}')
print(f'  Pattern: {sr.sentence_pattern()}')

# 5. 向后兼容fill()
print('\n=== Test 5: Backward Compat ===')
te2 = TemplateEngine(wb, seed=42)
r5 = te2.fill('{{hero}}拿起{{equipment.weapon_type}}', {'hero': '小明'})
print(f'  fill(): {r5}')
assert '小明' in r5

r6 = te2.fill_loop('{{循环索引}}: {{hero}}', {'hero': '战士'}, 3)
print(f'  fill_loop(): {r6}')
assert len(r6) == 3

print('\n' + '=' * 50)
print('  ALL TESTS PASSED!')
print('=' * 50)
