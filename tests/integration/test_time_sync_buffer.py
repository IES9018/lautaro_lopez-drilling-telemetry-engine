"""Tests del TimeSyncBuffer (alineación temporal / fixed-lag journal)."""

from __future__ import annotations

import asyncio

import numpy as np
import pytest

from src.pipeline.buffer.time_sync_buffer import TimeSyncBuffer, UkfJournalEntry


def _entry(t: float, value: float = 0.0) -> UkfJournalEntry:
    state = np.asarray([value, value], dtype=np.float64)
    cov = np.eye(2, dtype=np.float64)
    return UkfJournalEntry(
        timestamp_s=t,
        state=state,
        covariance=cov,
        dt=0.01,
        u_top_rad_s=12.0,
        wob_kn=80.0,
        z_surface=np.asarray([100.0, 5.0], dtype=np.float64),
        r_surface=np.eye(2, dtype=np.float64),
    )


async def _record_respects_maxlen() -> None:
    buf = TimeSyncBuffer(window_sec=1.0, max_entries=5)
    for i in range(8):
        await buf.record(_entry(float(i) * 0.01, float(i)))
    assert len(buf) == 5
    alignment = await buf.align(0.03)
    assert alignment is not None
    assert alignment.anchor.timestamp_s == pytest.approx(0.03)


def test_record_respects_maxlen_eviction() -> None:
    asyncio.run(_record_respects_maxlen())


async def _align_anchor_and_replay() -> None:
    buf = TimeSyncBuffer(window_sec=10.0, max_entries=1000)
    for i in range(100):
        await buf.record(_entry(float(i) * 0.1))
    result = await buf.align(5.05)
    assert result is not None
    assert result.anchor.timestamp_s == pytest.approx(5.0)
    assert result.replay_entries[0].timestamp_s == pytest.approx(5.1)
    assert result.replay_entries[-1].timestamp_s == pytest.approx(9.9)


def test_align_returns_anchor_and_replay_sequence() -> None:
    asyncio.run(_align_anchor_and_replay())


async def _align_drop_old() -> None:
    buf = TimeSyncBuffer(window_sec=1.0, max_entries=10)
    for i in range(10):
        await buf.record(_entry(10.0 + float(i) * 0.1))
    dropped = await buf.align(0.5)
    assert dropped is None


def test_align_returns_none_when_origin_older_than_window() -> None:
    asyncio.run(_align_drop_old())


async def _align_empty() -> None:
    buf = TimeSyncBuffer(window_sec=1.0, max_entries=10)
    assert await buf.align(0.0) is None


def test_align_empty_buffer_returns_none() -> None:
    asyncio.run(_align_empty())


def test_buffer_rejects_invalid_ctor_args() -> None:
    with pytest.raises(ValueError):
        TimeSyncBuffer(window_sec=0.0, max_entries=10)
    with pytest.raises(ValueError):
        TimeSyncBuffer(window_sec=1.0, max_entries=0)


async def _align_negative() -> None:
    buf = TimeSyncBuffer(window_sec=1.0, max_entries=10)
    await buf.record(_entry(1.0))
    with pytest.raises(ValueError):
        await buf.align(-0.1)


def test_align_rejects_negative_origin() -> None:
    asyncio.run(_align_negative())


async def _clear() -> None:
    buf = TimeSyncBuffer(window_sec=1.0, max_entries=10)
    await buf.record(_entry(1.0))
    buf.clear()
    assert len(buf) == 0


def test_clear_empties_buffer() -> None:
    asyncio.run(_clear())
