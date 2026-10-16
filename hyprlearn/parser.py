"""Parser especializado para arquivos de configuração do Hyprland em Lua.

Lê ~./config/hypr/config/binds.lua e variables.lua, extraindo categorias,
combinações de teclas e gerando descrições legíveis em linguagem natural.
"""

from __future__ import annotations
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Shortcut:
    id: str
    category: str
    sub_category: str
    combo: str
    raw_action: str
    description: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "sub_category": self.sub_category,
            "combo": self.combo,
            "raw_action": self.raw_action,
            "description": self.description,
        }


class HyprLuaParser:
    def __init__(
        self,
        binds_path: Optional[str | Path] = None,
        variables_path: Optional[str | Path] = None,
    ):
        base_dir = Path.home() / ".config" / "hypr" / "config"
        self.binds_path = Path(os.path.expanduser(binds_path or (base_dir / "binds.lua")))
        self.variables_path = Path(os.path.expanduser(variables_path or (base_dir / "variables.lua")))
        self.variables: Dict[str, str] = {}

    def load_variables(self) -> Dict[str, str]:
        """Extrai variáveis globais definidas em variables.lua."""
        self.variables = {
            "TERMINAL": "kitty",
            "FILE_MANAGER": "thunar",
            "BROWSER": "firefox",
            "EDITOR": "editor",
            "CALCULATOR": "calculadora",
            "MONITOR1": "Monitor 1",
            "MONITOR2": "Monitor 2",
            "MONITOR3": "Monitor 3",
            "NUM_WPM": "3",
        }

        if not self.variables_path.exists():
            return self.variables

        content = self.variables_path.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("--"):
                continue
            # Casos como TERMINAL = "kitty" ou NUM_WPM = 3
            match = re.match(r'^([A-Z0-9_]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([0-9]+))', line)
            if match:
                key = match.group(1)
                val = match.group(2) or match.group(3) or match.group(4) or ""
                self.variables[key] = val

        return self.variables

    def _resolve_expr(self, expr: str) -> str:
        """Resolve concatenações em Lua como mainMod .. ' + Q'."""
        expr = expr.strip()
        parts = [p.strip() for p in expr.split("..")]
        resolved_parts = []

        for p in parts:
            if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
                resolved_parts.append(p[1:-1])
            elif p in ("mainMod", "SUPER"):
                resolved_parts.append("SUPER")
            elif p.startswith("digitCode(") and p.endswith(")"):
                arg = p[10:-1].strip()
                resolved_parts.append(arg)
            elif p in self.variables:
                resolved_parts.append(self.variables[p])
            else:
                resolved_parts.append(p)

        res = "".join(resolved_parts)
        # Normalizar espaçamento de operadores
        res = re.sub(r"\s*\+\s*", " + ", res).strip()
        return res

    def _humanize_action(self, action: str, subcat: str) -> str:
        """Traduz comandos e dispatchers do Hyprland para português legível."""
        act = action.strip()

        # Janelas e Layout
        if "window.close" in act:
            return "Fechar janela ativa"
        if "hyprctl kill" in act:
            return "Forçar encerramento de janela (Kill)"
        if "window.float" in act:
            return "Alternar modo flutuante (Float)"
        if "fullscreen({ mode = 1 })" in act:
            return "Fullscreen maximizado (manter gaps/painéis)"
        if "window.fullscreen" in act:
            return "Alternar tela cheia (Fullscreen)"
        if "togglesplit" in act:
            return "Alternar divisão de layout (Horizontal/Vertical)"
        if "cycle_next" in act:
            return "Alternar para a próxima janela"
        if "window-switcher" in act:
            return "Abrir alternador de janelas"

        # Foco
        if "focus({" in act:
            if "direction = \"left\"" in act:
                return "Mover foco para a esquerda"
            if "direction = \"right\"" in act:
                return "Mover foco para a direita"
            if "direction = \"up\"" in act:
                return "Mover foco para cima"
            if "direction = \"down\"" in act:
                return "Mover foco para baixo"
            if "workspace = \"m+1\"" in act:
                return "Ir para o próximo workspace no monitor"
            if "workspace = \"m-1\"" in act:
                return "Ir para o workspace anterior no monitor"
            if "workspace = \"emptym\"" in act:
                return "Ir para o próximo workspace vazio"
            if "monitor = " in act:
                for m in ("MONITOR1", "MONITOR2", "MONITOR3"):
                    if m in act:
                        return f"Focar no {self.variables.get(m, m)}"
            if "workspace = " in act:
                ws_m = re.search(r'workspace\s*=\s*(?:i|"m~"\s*\.\.\s*i)', act)
                if ws_m:
                    return "Alternar para workspace número [1..N]"

        # Mover Janelas
        if "window.move({" in act:
            if "direction = \"u\"" in act:
                return "Mover janela ativa para cima"
            if "direction = \"d\"" in act:
                return "Mover janela ativa para baixo"
            if "direction = \"l\"" in act:
                return "Mover janela ativa para a esquerda"
            if "direction = \"r\"" in act:
                return "Mover janela ativa para a direita"
            if "monitor = \"-1\"" in act:
                return "Mover janela para o monitor anterior"
            if "monitor = \"+1\"" in act:
                return "Mover janela para o próximo monitor"
            if "workspace = \"m+1\"" in act:
                return "Mover janela para o próximo workspace"
            if "workspace = \"m-1\"" in act:
                return "Mover janela para o workspace anterior"
            if "workspace = \"special\"" in act:
                return "Mover janela para o Scratchpad (área oculta)"

        # Mouse & Zoom
        if "window.drag" in act:
            return "Arrastar/Mover janela com o mouse"
        if "window.resize" in act:
            return "Redimensionar janela com o mouse"
        if "zoomfunction(-0.3)" in act or "zoomfunction(-" in act:
            return "Diminuir zoom da tela (Afastar)"
        if "zoomfunction(0.3)" in act or "zoomfunction(" in act:
            return "Aumentar zoom da tela (Aproximar)"

        # Special workspace
        if "toggle_special" in act:
            return "Abrir / Ocultar Scratchpad (janelas especiais)"

        # Lançadores de Aplicativos e Utilitários
        if ("hyprlearn" in act or "hyprlearnBin" in act) and "rich" in act:
            return "Abrir Cheatsheet do HyprLearn (Tabela completa e estatísticas)"
        if ("hyprlearn" in act or "hyprlearnBin" in act) and "hud" in act:
            return "Abrir HUD interativo do HyprLearn (Busca rápida e cópia)"
        if ("hyprlearn" in act or "hyprlearnBin" in act) and "tip" in act:
            return "Exibir dica do HyprLearn"
        if "TERMINAL" in act and "btop" in act:
            return "Abrir monitor de sistema (Btop)"
        if "TERMINAL" in act:
            return f"Abrir terminal ({self.variables.get('TERMINAL', 'Terminal')})"
        if "FILE_MANAGER" in act:
            return f"Abrir gerenciador de arquivos ({self.variables.get('FILE_MANAGER', 'Arquivos')})"
        if "EDITOR" in act:
            return f"Abrir editor de texto ({self.variables.get('EDITOR', 'Editor')})"
        if "CALCULATOR" in act:
            return f"Abrir calculadora ({self.variables.get('CALCULATOR', 'Calculadora')})"
        if "BROWSER" in act:
            return f"Abrir navegador ({self.variables.get('BROWSER', 'Navegador')})"

        # Noctalia Controls
        if "settings-toggle" in act:
            return "Abrir configurações do sistema (Noctalia)"
        if "panel-toggle control-center notifications" in act:
            return "Abrir central de notificações"
        if "panel-toggle control-center" in act:
            return "Abrir central de controle (Control Center)"
        if "panel-toggle launcher /emo" in act:
            return "Abrir seletor de emojis"
        if "panel-toggle launcher" in act:
            return "Abrir lançador de aplicativos (Menu)"
        if "session lock" in act:
            return "Bloquear a sessão / Tela de bloqueio"
        if "panel-toggle session" in act:
            return "Menu de encerramento da sessão (Power menu)"
        if "panel-toggle wallpaper" in act:
            return "Seletor de papel de parede (Wallpapers)"
        if "panel-toggle clipboard" in act:
            return "Histórico da área de transferência (Clipboard)"

        # Hardware & Mídia
        if "volume-up" in act:
            return "Aumentar volume"
        if "volume-down" in act:
            return "Diminuir volume"
        if "volume-mute" in act:
            return "Silenciar saída de áudio"
        if "mic-mute" in act:
            return "Silenciar microfone"
        if "media toggle" in act:
            return "Play / Pause reprodução de mídia"
        if "media next" in act:
            return "Próxima faixa de mídia"
        if "media previous" in act:
            return "Faixa de mídia anterior"
        if "brightness-up" in act:
            return "Aumentar brilho da tela"
        if "brightness-down" in act:
            return "Diminuir brilho da tela"

        # Utilitários
        if "hyprpicker" in act:
            return "Conta-gotas de cor (Hyprpicker)"
        if "screenshot-region" in act:
            return "Captura de tela de uma área selecionada"
        if "screenshot-fullscreen" in act:
            return "Captura de tela cheia (Printscreen)"

        if subcat:
            return f"{subcat}: {act}"
        return act

    def parse(self) -> List[Shortcut]:
        """Analisa o arquivo binds.lua e retorna a lista estruturada de atalhos."""
        self.load_variables()

        if not self.binds_path.exists():
            return []

        content = self.binds_path.read_text(encoding="utf-8")
        shortcuts: List[Shortcut] = []

        current_category = "GERAL"
        current_subcategory = ""

        lines = content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Detectar cabeçalhos de categoria principal, ex: ---- WINDOW MANAGEMENT ----
            cat_match = re.search(r"[-=]{3,}\s*([A-Z0-9_\s&]+?)\s*[-=]{3,}", line)
            if cat_match:
                candidate = cat_match.group(1).strip()
                if candidate:
                    current_category = candidate
                i += 1
                continue

            # Detectar subcategorias, ex: -- Window manipulation
            if line.startswith("--") and not line.startswith("---"):
                sub_text = line.lstrip("-# \t").strip()
                # Ignorar comentários explicativos longos
                if sub_text and len(sub_text) < 45 and not sub_text.startswith("AZERTY"):
                    current_subcategory = sub_text

            # Detectar laços for para workspaces (for i = 1, NUM_WPM do ...)
            if line.startswith("for i = 1, NUM_WPM"):
                # Agrupa o laço de workspaces
                loop_block = []
                while i < len(lines) and not lines[i].strip().startswith("end"):
                    loop_block.append(lines[i])
                    i += 1
                loop_block_str = " ".join(loop_block)

                num_wpm = int(self.variables.get("NUM_WPM", "3"))
                if "hl.dsp.window.move" in loop_block_str and "follow = false" in loop_block_str:
                    shortcuts.append(
                        Shortcut(
                            id="move_ws_nofollow",
                            category=current_category,
                            sub_category=current_subcategory or "Workspaces",
                            combo=f"SUPER + SHIFT + ALT + [1..{num_wpm}]",
                            raw_action="window.move(workspace, follow=false)",
                            description=f"Mover janela para workspace [1..{num_wpm}] em segundo plano (sem focar)",
                        )
                    )
                elif "hl.dsp.window.move" in loop_block_str:
                    shortcuts.append(
                        Shortcut(
                            id="move_ws_follow",
                            category=current_category,
                            sub_category=current_subcategory or "Workspaces",
                            combo=f"SUPER + SHIFT + CONTROL + [1..{num_wpm}]",
                            raw_action="window.move(workspace)",
                            description=f"Mover janela e focar workspace [1..{num_wpm}]",
                        )
                    )
                elif "hl.dsp.focus" in loop_block_str and "ALT" in loop_block_str:
                    shortcuts.append(
                        Shortcut(
                            id="focus_ws_abs",
                            category=current_category,
                            sub_category=current_subcategory or "Workspaces",
                            combo=f"SUPER + ALT + [1..{num_wpm}]",
                            raw_action="focus(workspace absolute)",
                            description=f"Alternar para workspace absoluto [1..{num_wpm}]",
                        )
                    )
                elif "hl.dsp.focus" in loop_block_str and "CONTROL" in loop_block_str:
                    shortcuts.append(
                        Shortcut(
                            id="focus_ws_rel",
                            category=current_category,
                            sub_category=current_subcategory or "Workspaces",
                            combo=f"SUPER + CONTROL + [1..{num_wpm}]",
                            raw_action="focus(workspace relative)",
                            description=f"Alternar para workspace relativo no monitor [1..{num_wpm}]",
                        )
                    )
                i += 1
                continue

            # Detectar chamadas hl.bind(...)
            if "hl.bind(" in line:
                bind_content = line[line.find("hl.bind(") + 8 :]
                # Tentar extrair os argumentos: hl.bind(key_expr, action_expr, [options])
                args = self._extract_bind_args(bind_content)
                if args and len(args) >= 2:
                    raw_key = args[0]
                    raw_act = args[1]

                    combo = self._resolve_expr(raw_key)
                    description = self._humanize_action(raw_act, current_subcategory)

                    # Gerar um ID estável a partir do combo
                    slug = re.sub(r"[^a-zA-Z0-9]+", "_", combo.lower()).strip("_")
                    item = Shortcut(
                        id=slug,
                        category=current_category,
                        sub_category=current_subcategory,
                        combo=combo,
                        raw_action=raw_act,
                        description=description,
                    )
                    shortcuts.append(item)

            i += 1

        return shortcuts

    def _extract_bind_args(self, text: str) -> List[str]:
        """Divide argumentos de primeiro nível de hl.bind respeitando parênteses e aspas."""
        args = []
        cur: List[str] = []
        depth = 0
        in_quote = False
        quote_char = ""

        for char in text:
            if in_quote:
                cur.append(char)
                if char == quote_char:
                    in_quote = False
                continue

            if char in ('"', "'"):
                in_quote = True
                quote_char = char
                cur.append(char)
            elif char in ("(", "{", "["):
                depth += 1
                cur.append(char)
            elif char in (")", "}", "]"):
                if depth == 0 and char == ")":
                    # Fim do hl.bind( ... )
                    break
                depth -= 1
                cur.append(char)
            elif char == "," and depth == 0:
                args.append("".join(cur).strip())
                cur = []
            else:
                cur.append(char)

        if cur:
            args.append("".join(cur).strip())

        return args
