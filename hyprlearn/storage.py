"""Armazenamento e persistência de dados de aprendizado e estatísticas."""

from __future__ import annotations
import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class ShortcutStat:
    id: str
    mastery_level: int = 1  # 1 (iniciante) a 5 (dominado)
    times_shown: int = 0
    last_seen_ts: float = 0.0
    is_favorite: bool = False
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class Storage:
    def __init__(self, data_path: Optional[str | Path] = None):
        base_dir = Path.home() / ".local" / "share" / "hyprlearn"
        self.data_path = Path(os.path.expanduser(data_path or (base_dir / "stats.json")))
        self.stats: Dict[str, ShortcutStat] = {}
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        if self.data_path.exists():
            try:
                data = json.loads(self.data_path.read_text(encoding="utf-8"))
                for sid, sdata in data.items():
                    self.stats[sid] = ShortcutStat(**sdata)
            except Exception:
                self.stats = {}
        else:
            self.save()

    def get_or_create(self, shortcut_id: str) -> ShortcutStat:
        if shortcut_id not in self.stats:
            self.stats[shortcut_id] = ShortcutStat(id=shortcut_id)
        return self.stats[shortcut_id]

    def record_impression(self, shortcut_id: str) -> ShortcutStat:
        stat = self.get_or_create(shortcut_id)
        stat.times_shown += 1
        stat.last_seen_ts = time.time()
        self.save()
        return stat

    def set_mastery(self, shortcut_id: str, level: int) -> ShortcutStat:
        stat = self.get_or_create(shortcut_id)
        stat.mastery_level = max(1, min(5, level))
        self.save()
        return stat

    def toggle_favorite(self, shortcut_id: str) -> bool:
        stat = self.get_or_create(shortcut_id)
        stat.is_favorite = not stat.is_favorite
        self.save()
        return stat.is_favorite

    def save(self) -> None:
        payload = {k: v.to_dict() for k, v in self.stats.items()}
        self.data_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
