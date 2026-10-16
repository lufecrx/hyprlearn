#!/usr/bin/env bash
#
# HyprLearn - Script de Desinstalação
#

set -e

echo "🗑️ Desinstalando HyprLearn..."

# 1. Parar e desativar timer do systemd
if command -v systemctl >/dev/null 2>&1; then
    systemctl --user stop hyprlearn-notify.timer 2>/dev/null || true
    systemctl --user disable hyprlearn-notify.timer 2>/dev/null || true
    rm -f "$HOME/.config/systemd/user/hyprlearn-notify.service"
    rm -f "$HOME/.config/systemd/user/hyprlearn-notify.timer"
    systemctl --user daemon-reload 2>/dev/null || true
    echo "✅ Serviços do systemd removidos."
fi

# 2. Remover binário
rm -f "$HOME/.local/bin/hyprlearn"
echo "✅ Binário ~/.local/bin/hyprlearn removido."

echo ""
echo "HyprLearn foi desinstalado."
echo "Lembre-se de remover a linha do atalho no seu binds.lua, se aplicável."
