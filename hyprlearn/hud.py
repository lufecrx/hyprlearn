"""Módulo de interface do usuário para o HUD (Cheatsheet interativo)."""

from __future__ import annotations
import shutil
import subprocess
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .learner import LearnerEngine
from .parser import Shortcut


class HUD:
    def __init__(self, shortcuts: List[Shortcut], learner: Optional[LearnerEngine] = None):
        self.shortcuts = shortcuts
        self.learner = learner
        self.console = Console()

    def run(self, mode: Optional[str] = None, action: str = "copy") -> Optional[Shortcut]:
        """Abre o HUD no melhor modo disponível ou no modo explicitamente solicitado.
        
        Ordem de prioridade padrão:
        1. 'noctalia' (Menu nativo integrado do Wayland/Noctalia)
        2. 'fzf' (Busca difusa em terminal)
        3. 'rich' (Tabela formatada no terminal)
        """
        if mode == "rich":
            self.render_rich_table()
            return None

        if mode == "fzf":
            return self.run_fzf(action=action)

        if mode == "noctalia" or (mode is None and shutil.which("noctalia")):
            res = self.run_noctalia(action=action)
            if res is not None:
                return res
            # Se não conseguiu ou cancelou, retorna
            return None

        # Fallback para fzf ou rich se noctalia não existir
        if shutil.which("fzf"):
            return self.run_fzf(action=action)
        else:
            self.render_rich_table()
            return None

    def run_noctalia(self, action: str = "copy") -> Optional[Shortcut]:
        """Abre o menu de busca nativo do Noctalia via dmenu."""
        if not shutil.which("noctalia"):
            self.console.print("[red]Erro: 'noctalia' não encontrado no PATH.[/red]")
            return None

        lines = []
        mapping = {}

        # Formatação limpa para o launcher gráfico
        for s in self.shortcuts:
            line_str = f"{s.combo:<24}  •  {s.description}  ({s.category})"
            lines.append(line_str)
            mapping[line_str] = s

        input_data = "\n".join(lines)
        cmd = ["noctalia", "dmenu", "-p", "⌨ Atalhos Hyprland"]


        try:
            res = subprocess.run(cmd, input=input_data, capture_output=True, text=True)
            if res.returncode == 0:
                selected_line = res.stdout.strip()
                selected_shortcut = mapping.get(selected_line)
                if selected_shortcut:
                    if action == "copy":
                        self._copy_to_clipboard(selected_shortcut.combo, selected_shortcut.description)
                    if self.learner:
                        self.learner.storage.record_impression(selected_shortcut.id)
                    return selected_shortcut
        except Exception as e:
            self.console.print(f"[red]Erro ao executar noctalia dmenu: {e}[/red]")

        return None

    def run_fzf(self, action: str = "copy") -> Optional[Shortcut]:
        """Abre menu interativo de busca difusa usando fzf."""
        if not shutil.which("fzf"):
            self.console.print("[red]Erro: 'fzf' não encontrado no PATH. Usando modo tabela do Rich.[/red]")
            self.render_rich_table()
            return None

        lines = []
        mapping = {}

        max_cat = max(len(s.category) for s in self.shortcuts) if self.shortcuts else 15
        max_combo = max(len(s.combo) for s in self.shortcuts) if self.shortcuts else 20

        for s in self.shortcuts:
            line_str = f"[{s.category:<{max_cat}}]  {s.combo:<{max_combo}}  ➔  {s.description}"
            lines.append(line_str)
            mapping[line_str] = s

        fzf_input = "\n".join(lines).encode("utf-8")
        cmd = [
            "fzf",
            "--prompt=⌨ Atalhos Hyprland > ",
            "--header=ENTER: Copiar atalho | ESC: Sair",
            "--layout=reverse",
            "--border=rounded",
            "--info=inline",
            "--ansi",
        ]

        try:
            res = subprocess.run(cmd, input=fzf_input, capture_output=True)
            if res.returncode == 0:
                selected_line = res.stdout.decode("utf-8").strip()
                selected_shortcut = mapping.get(selected_line)
                if selected_shortcut:
                    if action == "copy":
                        self._copy_to_clipboard(selected_shortcut.combo, selected_shortcut.description)
                    if self.learner:
                        self.learner.storage.record_impression(selected_shortcut.id)
                return selected_shortcut
        except Exception as e:
            self.console.print(f"[red]Erro ao executar fzf: {e}[/red]")

        return None

    def _copy_to_clipboard(self, combo: str, desc: str = "") -> None:
        """Copia texto para a área de transferência via wl-copy."""
        if shutil.which("wl-copy"):
            try:
                subprocess.run(["wl-copy"], input=combo.encode("utf-8"), check=True)
                if shutil.which("notify-send"):
                    body = f"'{combo}' copiado para a área de transferência!"
                    if desc:
                        body += f"\n➔ {desc}"
                    subprocess.run(
                        ["notify-send", "-a", "HyprLearn", "-t", "2000", "-i", "input-keyboard", "Atalho Copiado", body]
                    )

            except Exception:
                pass

    def render_rich_table(self, category_filter: Optional[str] = None) -> None:
        """Renderiza uma tabela estilizada com cores no terminal."""
        categories = sorted(list({s.category for s in self.shortcuts}))

        if category_filter:
            categories = [c for c in categories if c.lower() == category_filter.lower()]

        for cat in categories:
            table = Table(title=f"📌 {cat}", show_header=True, header_style="bold magenta", expand=True)
            table.add_column("Combinação de Teclas", style="bold cyan", no_wrap=True, width=32)
            table.add_column("Ação / Descrição", style="white")
            table.add_column("Subcategoria", style="dim", width=24)

            cat_shortcuts = [s for s in self.shortcuts if s.category == cat]
            for s in cat_shortcuts:
                table.add_row(s.combo, s.description, s.sub_category)

            self.console.print(table)
            self.console.print()

        if self.learner:
            summary = self.learner.get_progress_summary()
            stats_text = (
                f"[bold green]Total de Atalhos:[/bold green] {summary['total_shortcuts']} | "
                f"[bold yellow]Visualizados:[/bold yellow] {summary['seen_shortcuts']} | "
                f"[bold blue]Dominados:[/bold blue] {summary['mastered']} | "
                f"[bold magenta]Maestria Geral:[/bold magenta] {summary['mastery_percentage']}%"
            )
            self.console.print(Panel(stats_text, title="🎯 Estatísticas de Memorização", border_style="green"))
