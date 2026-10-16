# 🧠 HyprLearn

> Cheatsheet interativo e Micro-Learning com repetição espaçada para atalhos do **Hyprland** (Wayland).

O **HyprLearn** acelera a memorização dos seus atalhos lendo diretamente a sua configuração do Hyprland (`binds.lua` e `variables.lua`). Ele combina uma barra de pesquisa instantânea (integrada ao **Noctalia** ou **FZF**) com notificações periódicas discretas para treino passivo da memória muscular.

---

## ⚡ Instalação Rápida (1 Comando)

Clone o repositório e execute o script de instalação:

```bash
git clone https://github.com/seu-usuario/hyprland-shortcuts.git
cd hyprland-shortcuts
./install.sh
```

O instalador automaticamente:
1. Vincula o comando global `hyprlearn` em `~/.local/bin/hyprlearn`;
2. Garante o `$PATH` do systemd (`~/.config/environment.d/path.conf`);
3. Habilita o timer do systemd para dicas passivas a cada 45 minutos.

*(Para desinstalar no futuro, basta executar `./uninstall.sh`).*

---

## ⌨️ Integração com o Hyprland

Adicione os atalhos no seu arquivo de configuração (`~/.config/hypr/config/binds.lua`):

```lua
-- HyprLearn (Shortcuts HUD & Cheatsheet)
local hyprlearnBin = (os.getenv("HOME") or "/home/luiz") .. "/.local/bin/hyprlearn"

-- SUPER + / ou SUPER + F1: Barra de pesquisa instantânea (Noctalia dmenu / FZF)
hl.bind(mainMod .. " + slash",         hl.dsp.exec_cmd(launchPrefix .. hyprlearnBin .. " hud"))
hl.bind(mainMod .. " + F1",            hl.dsp.exec_cmd(launchPrefix .. hyprlearnBin .. " hud"))

-- SUPER + Shift + /: Menu interativo FZF no terminal flutuante
hl.bind(mainMod .. " + SHIFT + slash", hl.dsp.exec_cmd(launchPrefix .. TERMINAL .. " --class hyprlearn-hud -e " .. hyprlearnBin .. " hud --fzf"))
```


Depois de editar, recarregue o Hyprland:
```bash
hyprctl reload
```

---

## 🚀 Uso e Comandos

Você pode usar o comando `hyprlearn` em qualquer terminal:

| Comando | Descrição |
| :--- | :--- |
| `hyprlearn hud` | Abre o menu de busca rápida (usa `noctalia dmenu` ou `fzf`). Copia a tecla com <kbd>Enter</kbd>. |
| `hyprlearn hud --rich` | Exibe a tabela completa dividida por categorias no terminal. |
| `hyprlearn tip` | Exibe uma dica rápida de atalho no terminal (ótimo para colocar no `.bashrc` / `.zshrc`). |
| `hyprlearn tip -n` | Exibe a dica no terminal **e** envia notificação no desktop. |
| `hyprlearn notify` | Dispara uma notificação de treino na tela imediatamente. |
| `hyprlearn stats` | Mostra seu nível de maestria e atalhos já visualizados. |
| `hyprlearn parse` | Lista todos os atalhos encontrados na configuração para conferência. |

---

## ⚙️ Como Funciona o Micro-Learning

* **Algoritmo de Repetição Espaçada:** Prioriza atalhos que você ainda não viu ou que tem menor nível de familiaridade.
* **Detecção Inteligente de Tela Cheia:** Pausa notificações automaticamente se você estiver jogando ou assistindo a um vídeo em tela cheia (`hyprctl activewindow`).
* **Armazenamento Transparente:** O progresso fica salvo localmente no padrão XDG em `~/.local/share/hyprlearn/stats.json`.

---

## 📋 Requisitos

* Linux com **Hyprland** (Wayland)
* **Python 3.10+** (com biblioteca `rich`)
* `notify-send` (qualquer daemon de notificação, como Noctalia, Dunst, SwayNC ou Mako)
* `wl-copy` (para copiar atalhos ao clipboard)
* `noctalia` ou `fzf` (para o HUD de busca rápida)
