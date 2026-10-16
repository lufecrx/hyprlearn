#!/usr/bin/env bash
#
# HyprLearn - Script de Instalação Rápida
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_PATH="$HOME/.local/bin/hyprlearn"
TARGET_RUNNER="$SCRIPT_DIR/hyprlearn-bin"

echo "🧠 Instalando HyprLearn..."

# 1. Verificar dependências básicas
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 não encontrado. Instale o python3 primeiro."; exit 1; }

# 2. Criar ~/.local/bin se não existir
mkdir -p "$HOME/.local/bin"

# 3. Garantir permissão de execução e criar link simbólico
chmod +x "$TARGET_RUNNER"
ln -sf "$TARGET_RUNNER" "$BIN_PATH"
echo "✅ Comando 'hyprlearn' vinculado em: $BIN_PATH"

# 4. Configurar PATH para sessão systemd/Wayland (garante funcionamento via atalhos do Hyprland)
mkdir -p "$HOME/.config/environment.d"
PATH_CONF="$HOME/.config/environment.d/path.conf"
if ! grep -q '\$HOME/\.local/bin' "$PATH_CONF" 2>/dev/null; then
    echo 'PATH=$HOME/.local/bin:$PATH' >> "$PATH_CONF"
    echo "✅ PATH adicionado em $PATH_CONF"
fi
if command -v systemctl >/dev/null 2>&1; then
    systemctl --user import-environment PATH 2>/dev/null || true
fi

# 5. Instalar serviços do systemd para micro-learning passivo
if command -v systemctl >/dev/null 2>&1; then
    SYSTEMD_DIR="$HOME/.config/systemd/user"
    mkdir -p "$SYSTEMD_DIR"
    cp "$SCRIPT_DIR/systemd/hyprlearn-notify.service" "$SYSTEMD_DIR/"
    cp "$SCRIPT_DIR/systemd/hyprlearn-notify.timer" "$SYSTEMD_DIR/"
    systemctl --user daemon-reload
    systemctl --user enable --now hyprlearn-notify.timer 2>/dev/null || true
    echo "✅ Notificações periódicas (timer systemd) ativadas a cada 45min"
fi

echo ""
echo "🎉 Instalação concluída com sucesso!"
echo ""
echo "Comandos rápidos:"
echo "  hyprlearn hud       - Abre o menu de busca de atalhos (Noctalia / FZF)"
echo "  hyprlearn notify    - Dispara uma notificação de dica agora"
echo "  hyprlearn tip       - Exibe uma dica no terminal (ideal para seu .bashrc/.zshrc)"
echo "  hyprlearn stats     - Mostra seu progresso de memorização"
echo ""
echo "Para integrar ao Hyprland, adicione em ~/.config/hypr/config/binds.lua:"
echo '  hl.bind(mainMod .. " + slash", hl.dsp.exec_cmd(launchPrefix .. os.getenv("HOME") .. "/.local/bin/hyprlearn hud"))'
echo ""
