"""Gerenciador de notificações periódicas para micro-learning no Hyprland."""

from __future__ import annotations
import json
import logging
import shutil
import subprocess
import time
from typing import Optional

from .learner import LearnerEngine
from .parser import Shortcut

logger = logging.getLogger("hyprlearn.notifier")


class Notifier:
    def __init__(self, learner: LearnerEngine, pause_on_fullscreen: bool = True):
        self.learner = learner
        self.pause_on_fullscreen = pause_on_fullscreen

    def is_fullscreen_active(self) -> bool:
        """Verifica se existe uma janela em fullscreen ativa no Hyprland."""
        if not shutil.which("hyprctl"):
            return False

        try:
            res = subprocess.run(
                ["hyprctl", "activewindow", "-j"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                # No Hyprland, "fullscreen": true ou "fullscreenClient": 1 ou 2
                return bool(data.get("fullscreen", False) or data.get("fullscreenMode", 0) > 0)
        except Exception as e:
            logger.debug(f"Erro ao verificar activewindow no hyprctl: {e}")

        return False

    def send_notification(self, shortcut: Optional[Shortcut] = None) -> bool:
        """Envia uma notificação com o atalho selecionado."""
        if self.pause_on_fullscreen and self.is_fullscreen_active():
            logger.info("Janela fullscreen detectada no Hyprland. Notificação adiada.")
            return False

        item = shortcut or self.learner.select_next()
        if not item:
            return False

        title = f"💡 Dica Hyprland: {item.category}"
        body = f"⌨ {item.combo}\n➔ {item.description}"


        cmd = [
            "notify-send",
            "-a", "HyprLearn",
            "-i", "input-keyboard",
            "-u", "normal",
            title,
            body,
        ]

        try:
            subprocess.run(cmd, check=True)
            return True
        except Exception as e:
            logger.error(f"Falha ao executar notify-send: {e}")
            return False

    def run_daemon(self, interval_minutes: int = 45) -> None:
        """Loop contínuo de notificações passivas."""
        logger.info(f"Iniciando daemon de micro-learning com intervalo de {interval_minutes} minutos.")
        interval_seconds = interval_minutes * 60

        while True:
            try:
                self.send_notification()
            except Exception as e:
                logger.error(f"Erro no ciclo de notificação: {e}")
            time.sleep(interval_seconds)
