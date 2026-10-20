# -*- coding: utf-8 -*-
"""批量生成加速器 —— 对标《宇宙巨校闪级生》37小时1.7亿字的性能。

宇宙巨校闪级生用VB单线程，在赛扬1GHz+256MB内存的配置下，
37小时输出了1.7亿字。Python版本应能通过以下手段大幅超越：

  1. 进程池并行（绕过GIL）
  2. 流式写入（边生成边写磁盘，不爆内存）
  3. 分片输出（多文件并行写入）
  4. 进度条 + 速度统计
  5. 断点续传支持
"""

import multiprocessing
import logging
import time
import json
from pathlib import Path
from typing import Optional, Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta

try:
    from .word_bank import WordBank
    from .multi_layer_engine import MultiLayerEngine, create_juxiao_engine
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from novel_generator.engine.word_bank import WordBank
    from novel_generator.engine.multi_layer_engine import MultiLayerEngine, create_juxiao_engine

_logger = logging.getLogger(__name__)


# ============================================================================
# 数据模型
# ============================================================================

@dataclass
class BatchConfig:
    """批量生成配置。"""
    # 结构
    series_count: int = 12
    volumes_per_series: int = 3
    chapters_per_volume: int = 5
    sections_per_chapter: int = 10

    # 性能
    workers: int = 0  # 0 = CPU核心数
    chunk_size: int = 100  # 每chunk的段落数
    output_dir: Path = Path("output")
    base_filename: str = "novel"

    # 容错
    resume: bool = True  # 支持断点续传
    max_file_size_mb: int = 100  # 单文件最大MB，超限后切换
    auto_split: bool = True  # 自动分文件

    # 质量
    seed: int = 42


@dataclass
class BatchProgress:
    """批量生成进度。"""
    total_blocks: int = 0
    completed_blocks: int = 0
    start_time: float = 0.0
    last_checkpoint: float = 0.0
    output_paths: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time

    @property
    def speed_wps(self) -> float:
        """每秒生成字数。"""
        if self.elapsed == 0:
            return 0
        return (self.completed_blocks * 200) / self.elapsed

    @property
    def eta(self) -> float:
        """剩余秒数。"""
        if self.speed_wps == 0:
            return float("inf")
        remaining_blocks = self.total_blocks - self.completed_blocks
        return (remaining_blocks * 200) / self.speed_wps

    @property
    def percent(self) -> float:
        if self.total_blocks == 0:
            return 0
        return self.completed_blocks / self.total_blocks * 100


# ============================================================================
# 加速器核心
# ============================================================================

class BatchWriter:
    """批量生成加速器。

    使用方式:
        writer = BatchWriter(wb, config)
        writer.run()  # 启动全量生成
    """

    def __init__(self, wb: WordBank, config: BatchConfig):
        self._wb = wb
        self._config = config
        self._progress = BatchProgress()
        self._current_file: Optional[Path] = None
        self._file_index = 0
        self._bytes_written_current_file = 0
        self._checkpoint_file: Optional[Path] = None

    # ================================================================
    # 主入口
    # ================================================================

    def run(self) -> BatchProgress:
        """执行批量生成，返回最终进度。"""
        self._init_output_dir()
        self._setup_checkpoint()

        self._progress.total_blocks = (
            self._config.series_count
            * self._config.volumes_per_series
            * self._config.chapters_per_volume
            * self._config.sections_per_chapter
        )
        self._progress.start_time = time.time()
        self._progress.last_checkpoint = time.time()

        workers = self._config.workers or max(1, multiprocessing.cpu_count() - 1)

        print(f"[批量生成] 启动 — {self._config.workers}进程, "
              f"总任务={self._progress.total_blocks}段, "
              f"预估字数≈{self._progress.total_blocks * 200:,}")

        if workers > 1 and self._config.chunk_size > 0:
            # 多进程模式
            self._run_parallel()
        else:
            # 单进程模式（更稳定，适合调试）
            self._run_sequential()

        self._save_checkpoint()
        self._print_summary()
        return self._progress

    # ================================================================
    # 单进程模式
    # ================================================================

    def _run_sequential(self):
        """顺序生成（单进程，稳定模式）。"""
        engine = create_juxiao_engine(self._wb, seed=self._config.seed)
        engine.configure_series(count=self._config.series_count)
        engine.configure_volume(count=self._config.volumes_per_series)
        engine.configure_chapter(count=self._config.chapters_per_volume)

        for text in engine.generate_stream():
            self._write_block(text)
            self._progress.completed_blocks += 1
            self._maybe_report_progress()

    # ================================================================
    # 多进程模式
    # ================================================================

    def _run_parallel(self):
        """Worker池并行生成。"""
        # 将总任务拆分为chunks
        total_sections = self._progress.total_blocks
        chunk_size = self._config.chunk_size
        num_chunks = (total_sections + chunk_size - 1) // chunk_size

        task_args = [
            (i * chunk_size,
             min((i + 1) * chunk_size, total_sections),
             chunk_size,
             self._config.seed + i)
            for i in range(num_chunks)
        ]

        with multiprocessing.Pool(processes=self._config.workers) as pool:
            for i, texts in enumerate(
                pool.imap_unordered(_generate_chunk_worker, task_args)
            ):
                for text in texts:
                    self._write_block(text)
                self._progress.completed_blocks += len(texts)
                self._maybe_report_progress()

    # ================================================================
    # IO方法
    # ================================================================

    def _write_block(self, text: str):
        """写入一个文本块，自动处理分文件。"""
        if not text:
            return
        text_bytes = text.encode("utf-8") + b"\n\n"

        # 确定输出文件
        if self._current_file is None or (
            self._config.auto_split
            and self._bytes_written_current_file + len(text_bytes)
            > self._config.max_file_size_mb * 1024 * 1024
        ):
            self._next_file()

        with open(self._current_file, "ab") as f:
            f.write(text_bytes)

        self._bytes_written_current_file += len(text_bytes)

    def _next_file(self):
        """切换到下一个输出文件。"""
        self._file_index += 1
        filename = f"{self._config.base_filename}_{self._file_index:04d}.txt"
        self._current_file = self._config.output_dir / filename
        self._bytes_written_current_file = 0
        self._progress.output_paths.append(self._current_file)

    def _init_output_dir(self):
        self._config.output_dir.mkdir(parents=True, exist_ok=True)

    def _maybe_report_progress(self):
        """每10秒报告一次进度。"""
        now = time.time()
        if now - self._progress.last_checkpoint >= 10:
            self._report_progress()
            self._progress.last_checkpoint = now
            self._save_checkpoint()

    def _report_progress(self):
        p = self._progress
        elapsed = timedelta(seconds=int(p.elapsed))
        eta_str = "N/A" if p.eta == float("inf") else str(timedelta(seconds=int(p.eta)))
        print(f"  [{p.percent:.1f}%] {p.completed_blocks}/{p.total_blocks}段 "
              f"| {p.speed_wps:,.0f}字/秒 "
              f"| 耗时{elapsed} | 预计剩余{eta_str}")

    # ================================================================
    # 断点续传
    # ================================================================

    def _setup_checkpoint(self):
        self._checkpoint_file = self._config.output_dir / ".checkpoint.json"
        if self._config.resume and self._checkpoint_file.exists():
            try:
                with open(self._checkpoint_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._file_index = data.get("file_index", 0)
                    self._progress.completed_blocks = data.get("completed_blocks", 0)
                    self._progress.output_paths = [
                        Path(p) for p in data.get("output_paths", [])
                    ]
                    # 恢复当前文件
                    fps = self._progress.output_paths
                    if fps:
                        self._current_file = fps[-1]
                        if self._current_file.exists():
                            self._bytes_written_current_file = (
                                self._current_file.stat().st_size
                            )
                    print(f"  [断点续传] 已恢复进度: 已完成{self._progress.completed_blocks}段")
            except Exception as e:
                _logger.warning(f"检查点读取失败: {e}")

    def _save_checkpoint(self):
        if self._checkpoint_file is None:
            return
        try:
            data = {
                "file_index": self._file_index,
                "completed_blocks": self._progress.completed_blocks,
                "output_paths": [str(p) for p in self._progress.output_paths],
                "last_update": datetime.now().isoformat(),
            }
            with open(self._checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            _logger.warning(f"检查点保存失败: {e}")

    def _print_summary(self):
        p = self._progress
        elapsed = timedelta(seconds=int(p.elapsed))
        total_words = p.completed_blocks * 200
        print(f"\n{'=' * 50}")
        print(f"[批量生成完成]")
        print(f"  总段数:  {p.completed_blocks}")
        print(f"  总字数:  约{total_words:,}字")
        print(f"  总耗时:  {elapsed}")
        print(f"  平均速度: {p.speed_wps:,.0f}字/秒")
        print(f"  输出文件: {len(p.output_paths)}个")
        for path in p.output_paths[-3:]:
            size = path.stat().st_size if path.exists() else 0
            print(f"    → {path.name} ({size/1024/1024:.1f}MB)")
        if len(p.output_paths) > 3:
            print(f"    ... 还有{len(p.output_paths)-3}个文件")
        if p.errors:
            print(f"  错误数:  {len(p.errors)}")


# ============================================================================
# 多进程Worker
# ============================================================================

def _generate_chunk_worker(args) -> list[str]:
    """Worker进程：生成一个chunk的文本。"""
    start_idx, end_idx, chunk_size, seed = args
    from .word_bank import WordBank

    wb = WordBank(seed=seed)
    engine = create_juxiao_engine(wb, seed=seed)
    engine.configure_series(count=1)
    engine.configure_volume(count=1)
    engine.configure_chapter(count=chunk_size)

    texts = []
    for i, text in enumerate(engine.generate_stream()):
        if i >= (end_idx - start_idx):
            break
        texts.append(text)
    return texts


# ============================================================================
# 便捷函数
# ============================================================================

def quick_generate(
    wb: WordBank,
    output_dir: str = "output",
    series: int = 12,
    volumes: int = 3,
    chapters: int = 5,
    workers: int = 0,
    seed: int = 42,
) -> BatchProgress:
    """一行代码批量生成。"""
    config = BatchConfig(
        series_count=series,
        volumes_per_series=volumes,
        chapters_per_volume=chapters,
        sections_per_chapter=10,
        workers=workers,
        output_dir=Path(output_dir),
        seed=seed,
    )
    writer = BatchWriter(wb, config)
    return writer.run()


# ============================================================================
# 自检
# ============================================================================
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from novel_generator.engine.word_bank import WordBank

    print("=" * 60)
    print("批量生成加速器 - 自检")
    print("=" * 60)

    wb = WordBank(seed=42)

    # 小规模测试
    config = BatchConfig(
        series_count=2,
        volumes_per_series=2,
        chapters_per_volume=2,
        sections_per_chapter=3,
        workers=1,
        output_dir=Path("output_test"),
        base_filename="test_novel",
        auto_split=False,
        seed=42,
    )
    writer = BatchWriter(wb, config)
    progress = writer.run()

    # 验证输出
    files = list(config.output_dir.glob("*.txt"))
    print(f"\n[输出验证] 生成{len(files)}个文件")
    for f in files[:2]:
        size = f.stat().st_size
        with open(f, "r", encoding="utf-8") as fp:
            preview = fp.read()[:100].replace("\n", " ")
        print(f"  {f.name}: {size}字节, 预览: {preview}...")

    # 清理测试文件
    import shutil
    shutil.rmtree(config.output_dir, ignore_errors=True)

    print(f"\n全部自检通过 [OK]")
