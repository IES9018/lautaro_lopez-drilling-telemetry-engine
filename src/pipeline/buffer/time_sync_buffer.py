"""Búfer circular de sincronización temporal (fixed-lag journal UKF)."""

from __future__ import annotations

import asyncio
from bisect import bisect_right
from collections import deque
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class UkfJournalEntry:
    """Snapshot del filtro tras un paso de superficie (journal fixed-lag).

    Parameters
    ----------
    timestamp_s : float
        Tiempo de simulación del snapshot [s].
    state : NDArray[np.float64]
        Estado ``x`` justo **después** del update de superficie.
    covariance : NDArray[np.float64]
        Covarianza ``P`` justo **después** del update de superficie.
    dt : float
        Paso usado para llegar a este snapshot [s].
    u_top_rad_s : float
        Entrada de top-drive aplicada en el paso [rad/s].
    wob_kn : float
        Weight on Bit aplicado en el paso [kN].
    z_surface : NDArray[np.float64] or None
        Medición de superficie usada en el update (si hubo).
    r_surface : NDArray[np.float64] or None
        Covarianza de medición de superficie asociada a ``z_surface``.
    """

    timestamp_s: float
    state: NDArray[np.float64]
    covariance: NDArray[np.float64]
    dt: float
    u_top_rad_s: float
    wob_kn: float
    z_surface: NDArray[np.float64] | None
    r_surface: NDArray[np.float64] | None


@dataclass(frozen=True, slots=True)
class AlignmentResult:
    """Resultado de alinear un origen MWD con el journal de superficie.

    Parameters
    ----------
    anchor : UkfJournalEntry
        Último snapshot con ``timestamp_s <= origin_time_s``.
    anchor_index : int
        Índice del ancla en la copia del journal.
    replay_entries : tuple[UkfJournalEntry, ...]
        Entradas **posteriores** al ancla (exclusive) hasta el más reciente.
    """

    anchor: UkfJournalEntry
    anchor_index: int
    replay_entries: tuple[UkfJournalEntry, ...]


class TimeSyncBuffer:
    """Journal circular O(1) de estados UKF para fixed-lag smoothing.

    Parameters
    ----------
    window_sec : float
        Ventana temporal mínima retenida [s] (informativa; el límite duro
        es ``max_entries``).
    max_entries : int
        Capacidad del ``deque`` (``maxlen``); evicción automática O(1).
    """

    def __init__(self, window_sec: float, max_entries: int) -> None:
        if window_sec <= 0.0:
            msg = f"window_sec must be > 0, got {window_sec}"
            raise ValueError(msg)
        if max_entries < 1:
            msg = f"max_entries must be >= 1, got {max_entries}"
            raise ValueError(msg)
        self.window_sec = window_sec
        self.max_entries = max_entries
        self._entries: deque[UkfJournalEntry] = deque(maxlen=max_entries)
        self._lock = asyncio.Lock()

    async def record(self, entry: UkfJournalEntry) -> None:
        """Inserta un snapshot (O(1)); evicta el más antiguo si está lleno.

        Parameters
        ----------
        entry : UkfJournalEntry
            Snapshot a registrar (se guarda una copia de arrays).
        """
        stored = UkfJournalEntry(
            timestamp_s=float(entry.timestamp_s),
            state=np.array(entry.state, dtype=np.float64, copy=True),
            covariance=np.array(entry.covariance, dtype=np.float64, copy=True),
            dt=float(entry.dt),
            u_top_rad_s=float(entry.u_top_rad_s),
            wob_kn=float(entry.wob_kn),
            z_surface=(
                None
                if entry.z_surface is None
                else np.array(entry.z_surface, dtype=np.float64, copy=True)
            ),
            r_surface=(
                None
                if entry.r_surface is None
                else np.array(entry.r_surface, dtype=np.float64, copy=True)
            ),
        )
        async with self._lock:
            self._entries.append(stored)

    async def align(self, origin_time_s: float) -> AlignmentResult | None:
        """Alinea un origen MWD con el histórico de superficie.

        Parameters
        ----------
        origin_time_s : float
            Tiempo de origen de la medición MWD [s].

        Returns
        -------
        AlignmentResult or None
            Ancla + cola de replay, o ``None`` si el origen es más viejo
            que la ventana retenida (drop documentado, sin excepción).
        """
        if origin_time_s < 0.0:
            msg = f"origin_time_s must be >= 0, got {origin_time_s}"
            raise ValueError(msg)

        async with self._lock:
            snapshot = list(self._entries)

        if not snapshot:
            return None

        oldest = snapshot[0].timestamp_s
        if origin_time_s < oldest - 1e-12:
            return None

        timestamps = [e.timestamp_s for e in snapshot]
        # bisect_right → último índice con timestamp <= origin_time_s
        idx = bisect_right(timestamps, origin_time_s) - 1
        if idx < 0:
            return None

        anchor = snapshot[idx]
        replay = tuple(snapshot[idx + 1 :])
        return AlignmentResult(
            anchor=anchor,
            anchor_index=idx,
            replay_entries=replay,
        )

    def __len__(self) -> int:
        """Número de entradas actualmente retenidas."""
        return len(self._entries)

    def clear(self) -> None:
        """Vacía el journal (uso en reset/start)."""
        self._entries.clear()


__all__ = [
    "AlignmentResult",
    "TimeSyncBuffer",
    "UkfJournalEntry",
]
