"""Interface de linha de comando principal (CLI) para o HyprLearn."""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

# Garante que o pacote raiz esteja no sys.path independentemente do diretório atual
_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

from rich.console import Console
from rich.panel import Panel

try:
    from .hud import HUD
    from .learner import LearnerEngine
    from .notifier import Notifier
    from .parser import HyprLuaParser
    from .storage import Storage
except ImportError:
    from hyprlearn.hud import HUD
    from hyprlearn.learner import LearnerEngine
    from hyprlearn.notifier import Notifier
    from hyprlearn.parser import HyprLuaParser
    from hyprlearn.storage import Storage



def main() -> None:
    parser = argparse.ArgumentParser(
        prog="hyprlearn",
        description="HyprLearn: Cheatsheet interativo e Micro-Learning para Hyprland",
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando: hud
    hud_p = subparsers.add_parser("hud", help="Abre o cheatsheet / HUD de atalhos")
    hud_p.add_argument("--noctalia", action="store_true", help="Usa o menu gráfico nativo do Noctalia (padrão se disponível)")
    hud_p.add_argument("--fzf", action="store_true", help="Usa a busca interativa no terminal via FZF")
    hud_p.add_argument("--rich", action="store_true", help="Usa a visualização em tabela do Rich")
    hud_p.add_argument("--category", type=str, default=None, help="Filtrar por categoria específica")


    # Comando: tip
    tip_p = subparsers.add_parser("tip", help="Exibe uma dica de atalho estilizada no terminal")
    tip_p.add_argument("-n", "--notify", action="store_true", help="Também dispara uma notificação no desktop")


    # Comando: notify
    subparsers.add_parser("notify", help="Dispara uma notificação passiva imediatamente")

    # Comando: daemon
    daemon_p = subparsers.add_parser("daemon", help="Inicia o serviço em background de notificações periódicas")
    daemon_p.add_argument("--interval", type=int, default=45, help="Intervalo em minutos entre notificações (padrão: 45)")
    daemon_p.add_argument("--no-pause", action="store_true", help="Não pausar quando em fullscreen")

    # Comando: stats
    subparsers.add_parser("stats", help="Exibe as estatísticas de aprendizado e maestria")

    # Comando: parse
    subparsers.add_parser("parse", help="Lista todos os atalhos extraídos de binds.lua")

    args = parser.parse_args()

    # Inicialização do core
    lua_parser = HyprLuaParser()
    shortcuts = lua_parser.parse()
    storage = Storage()
    learner = LearnerEngine(shortcuts=shortcuts, storage=storage)
    console = Console()

    if args.command in (None, "hud"):
        hud = HUD(shortcuts=shortcuts, learner=learner)
        if getattr(args, "rich", False):
            hud.render_rich_table(category_filter=getattr(args, "category", None))
        elif getattr(args, "fzf", False):
            hud.run_fzf()
        elif getattr(args, "noctalia", False):
            hud.run_noctalia()
        else:
            # Padrão: usa o menu nativo do Noctalia se presente, ou FZF/Rich como fallback
            hud.run()


    elif args.command == "tip":
        item = learner.select_next()
        if item:
            tip_msg = f"[bold cyan]{item.combo}[/bold cyan]  ➔  [white]{item.description}[/white]  [dim]({item.category})[/dim]"
            console.print(Panel(tip_msg, title="💡 Dica de Atalho Hyprland", border_style="cyan"))
            if getattr(args, "notify", False):
                notifier = Notifier(learner=learner, pause_on_fullscreen=False)
                notifier.send_notification(shortcut=item)


    elif args.command == "notify":
        notifier = Notifier(learner=learner, pause_on_fullscreen=False)
        notifier.send_notification()

    elif args.command == "daemon":
        notifier = Notifier(learner=learner, pause_on_fullscreen=not args.no_pause)
        notifier.run_daemon(interval_minutes=args.interval)

    elif args.command == "stats":
        hud = HUD(shortcuts=shortcuts, learner=learner)
        hud.render_rich_table(use_pager=False)


    elif args.command == "parse":
        console.print(f"[bold green]Encontrados {len(shortcuts)} atalhos em binds.lua:[/bold green]\n")
        for s in shortcuts:
            console.print(f"• [bold cyan]{s.combo:<28}[/bold cyan] [white]{s.description}[/white] [dim]({s.category})[/dim]")


if __name__ == "__main__":
    main()
