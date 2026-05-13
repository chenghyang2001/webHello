# 臨時測試檔案 — 示範 retry loop 用，測試後由 PR 移除
import pytest
from pathlib import Path

_COUNTER_FILE = Path("/tmp/qa_demo_retry_count")

def pytest_configure(config):
    try:
        count = int(_COUNTER_FILE.read_text(encoding="utf-8").strip())
    except FileNotFoundError:
        count = 0
    if count < 2:
        _COUNTER_FILE.write_text(str(count + 1), encoding="utf-8")
        config._qa_demo_force_fail = (
            f"[DEMO] 第 {count + 1}/2 次：故意讓 QA 失敗，示範 retry loop"
        )
    else:
        # 第 3 次（count >= 2）：清除計數器，讓測試正常通過
        _COUNTER_FILE.unlink(missing_ok=True)
        config._qa_demo_force_fail = None

def pytest_runtest_setup(item):
    msg = item.config._qa_demo_force_fail
    if msg:
        pytest.fail(msg)
