"""快速冒烟测试"""
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from novel_generator.engine.word_bank import WordBank
from novel_generator.engine.template import TemplateEngine
from novel_generator.engine.context_manager import ContextManager
from novel_generator.engine.sentence_rhythm import SentenceRhythmEngine, ChapterRhythmOrchestrator

# Test 1: WordBank enhancements
print("=== Test 1: WordBank ===")
wb = WordBank(seed=42)
print(f"  pick: {wb.pick('adjectives', 'scene')}")
print(f"  unique: {wb.pick_unique('adjectives', 'scene')}")
print(f"  pool: {wb.pool('adjectives', 'scene')[:3]}...")
print("  PASS")

# Test 2: TemplateEngine with state vars + conditions
print("\n=== Test 2: TemplateEngine ===")
te = TemplateEngine(wb, seed=42)
tpl = '$weather{晴天}，{{?weather=晴天}}阳光明媚{{/}}。{{adjectives.scene}}的世界。'
result = te.resolve(tpl)
print(f"  Input:  {tpl}")
print(f"  Output: {result}")
assert '晴天' in result and '阳光明媚' in result, f"FAIL: {result}"
print("  PASS")

# Test 3: Backward compat fill()
print("\n=== Test 3: fill() backward compat ===")
te2 = TemplateEngine(wb, seed=42)
result2 = te2.fill("{{hero}}拔出{{weapons.name}}。", {"hero": "林动"})
print(f"  Input:  {{{{hero}}}}拔出{{{{weapons.name}}}}。")
print(f"  Output: {result2}")
assert '林动' in result2, f"FAIL: {result2}"
print("  PASS")

# Test 4: ContextManager
print("\n=== Test 4: ContextManager ===")
cm = ContextManager()
cm.register_character("林动", mood="愤怒", location="闪排骨溪")
cm.set_world("weather", "暴雨")
cm.set_chapter(1, 1, 10)
cm.log_event("battle", "林动大战虎尾闪星人", 10)
print(f"  Characters: {cm.list_characters()}")
print(f"  Current phase: {cm.current_phase()}")
print(f"  Recent events: {cm.recent_events(3)}")
print("  PASS")

# Test 5: SentenceRhythm
print("\n=== Test 5: SentenceRhythm ===")
sr = SentenceRhythmEngine(profile="climax", seed=42)
print(f"  Intensity at 0.5: {sr.current_intensity():.2f}")
print(f"  Target sentence length: {sr.target_sentence_length()}")
print(f"  Sentence pattern: {sr.sentence_pattern()}")
print("  PASS")

# Test 6: ChapterRhythmOrchestrator
print("\n=== Test 6: ChapterRhythmOrchestrator ===")
cro = ChapterRhythmOrchestrator(seed=42)
plan = cro.plan_chapter_rhythm(total_sentences=60)
print(f"  Stages: {[(s['stage_name'], s['sentence_count']) for s in plan]}")
print("  PASS")

print("\n" + "=" * 40)
print("ALL TESTS PASSED!")
print("=" * 40)
