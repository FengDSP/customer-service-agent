import shutil
from pathlib import Path

import pytest

from agent.session import (
    SESSIONS_DIR,
    _cache,
    append_message,
    get_or_create_session,
)

TEST_BIZ = "test_biz"
TEST_CUST = "test_customer"


@pytest.fixture(autouse=True)
def clean_sessions():
    """Clean up test session data before and after each test."""
    test_dir = SESSIONS_DIR / TEST_BIZ
    if test_dir.exists():
        shutil.rmtree(test_dir)
    _cache.clear()
    yield
    if test_dir.exists():
        shutil.rmtree(test_dir)
    _cache.clear()


def test_new_session_returns_empty():
    history = get_or_create_session(TEST_BIZ, TEST_CUST)
    assert history == []


def test_append_and_reload():
    append_message(TEST_BIZ, TEST_CUST, {"role": "user", "content": "hello"})
    append_message(TEST_BIZ, TEST_CUST, {"role": "assistant", "content": "hi there"})

    # Clear cache to force reload from disk
    _cache.clear()

    history = get_or_create_session(TEST_BIZ, TEST_CUST)
    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "hello"}
    assert history[1] == {"role": "assistant", "content": "hi there"}


def test_session_file_is_jsonl():
    append_message(TEST_BIZ, TEST_CUST, {"role": "user", "content": "msg1"})
    append_message(TEST_BIZ, TEST_CUST, {"role": "user", "content": "msg2"})

    path = SESSIONS_DIR / TEST_BIZ / f"{TEST_CUST}.jsonl"
    assert path.exists()
    lines = path.read_text().strip().split("\n")
    assert len(lines) == 2


def test_session_scoped_by_business():
    append_message("biz_a", TEST_CUST, {"role": "user", "content": "from a"})
    append_message("biz_b", TEST_CUST, {"role": "user", "content": "from b"})

    _cache.clear()

    history_a = get_or_create_session("biz_a", TEST_CUST)
    history_b = get_or_create_session("biz_b", TEST_CUST)

    assert len(history_a) == 1
    assert history_a[0]["content"] == "from a"
    assert len(history_b) == 1
    assert history_b[0]["content"] == "from b"

    # Cleanup
    for biz in ["biz_a", "biz_b"]:
        d = SESSIONS_DIR / biz
        if d.exists():
            shutil.rmtree(d)
