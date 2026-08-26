"""Historial acotado de recomendaciones del Advisor (estado de API)."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.advisor.schemas import AdvisorIncidentSnapshot, AdvisorRecommendation


class AdvisorRecommendationRecordDTO(BaseModel):
    """Registro persistido en el historial de la API.

    Attributes
    ----------
    recommendation : AdvisorRecommendation
        Recomendación estructurada emitida.
    triggered_at : datetime
        Instantánea UTC del disparo.
    snapshot : AdvisorIncidentSnapshot
        Features que motivaron el disparo.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    recommendation: AdvisorRecommendation
    triggered_at: datetime
    snapshot: AdvisorIncidentSnapshot


@dataclass
class AdvisorHistoryStore:
    """Cola circular de recomendaciones recientes.

    Parameters
    ----------
    maxlen : int
        Capacidad máxima del historial.
    """

    maxlen: int = 100
    _records: deque[AdvisorRecommendationRecordDTO] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.maxlen < 1:
            msg = f"maxlen must be >= 1, got {self.maxlen}"
            raise ValueError(msg)
        self._records = deque(maxlen=self.maxlen)

    def append(self, record: AdvisorRecommendationRecordDTO) -> None:
        """Inserta un registro (O(1); evicta el más antiguo si está lleno)."""
        self._records.append(record)

    def list_recent(self, limit: int = 50) -> list[AdvisorRecommendationRecordDTO]:
        """Devuelve los ``limit`` registros más recientes (más nuevo primero)."""
        if limit < 1:
            return []
        items = list(self._records)
        items.reverse()
        return items[:limit]

    def clear(self) -> None:
        """Vacía el historial."""
        self._records.clear()

    def __len__(self) -> int:
        return len(self._records)


__all__ = [
    "AdvisorHistoryStore",
    "AdvisorRecommendationRecordDTO",
]
