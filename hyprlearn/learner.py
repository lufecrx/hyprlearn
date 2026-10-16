"""Algoritmo de seleção ponderada e lógica de Micro-Learning."""

from __future__ import annotations
import math
import random
import time
from typing import List, Optional

from .parser import Shortcut
from .storage import Storage, ShortcutStat


class LearnerEngine:
    def __init__(self, shortcuts: List[Shortcut], storage: Optional[Storage] = None):
        self.shortcuts = shortcuts
        self.storage = storage or Storage()

    def select_next(self, category_filter: Optional[str] = None) -> Optional[Shortcut]:
        """Seleciona o próximo atalho com base no algoritmo ponderado de repetição espaçada."""
        pool = self.shortcuts
        if category_filter:
            pool = [s for s in pool if s.category.lower() == category_filter.lower()]

        if not pool:
            return None

        now = time.time()
        weights: List[float] = []

        for item in pool:
            stat: ShortcutStat = self.storage.get_or_create(item.id)

            # 1. Peso inversamente proporcional ao nível de maestria (1 a 5)
            # Nível 1 tem peso 10, nível 5 tem peso 1
            mastery_weight = (6 - stat.mastery_level) * 2.0

            # 2. Bônus para atalhos nunca vistos
            if stat.times_shown == 0:
                novelty_weight = 15.0
            else:
                # 3. Spaced repetition: bônus pelo tempo decorrido desde a última visualização
                hours_since = (now - stat.last_seen_ts) / 3600.0
                novelty_weight = min(10.0, math.log1p(hours_since) * 2.5)

            # 4. Bônus para favoritos
            favorite_bonus = 5.0 if stat.is_favorite else 0.0

            total_weight = mastery_weight + novelty_weight + favorite_bonus
            weights.append(max(0.1, total_weight))

        chosen = random.choices(pool, weights=weights, k=1)[0]
        self.storage.record_impression(chosen.id)
        return chosen

    def get_progress_summary(self) -> dict:
        """Gera métricas agregadas sobre a maestria do usuário."""
        total = len(self.shortcuts)
        seen = 0
        mastered = 0  # nível 4 ou 5
        learning = 0  # nível 2 ou 3
        newbie = 0    # nível 1 ou não visto

        for item in self.shortcuts:
            stat = self.storage.get_or_create(item.id)
            if stat.times_shown > 0:
                seen += 1
            if stat.mastery_level >= 4:
                mastered += 1
            elif stat.mastery_level in (2, 3):
                learning += 1
            else:
                newbie += 1

        percent_mastered = (mastered / total * 100) if total > 0 else 0.0

        return {
            "total_shortcuts": total,
            "seen_shortcuts": seen,
            "mastered": mastered,
            "learning": learning,
            "newbie": newbie,
            "mastery_percentage": round(percent_mastered, 1),
        }
