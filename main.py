import sys
import time
import asyncio
import argparse
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from config import config
from tracker import OmniTracker
from snapchat import SnapchatDispatcher
from gmail import GmailNotifier
from notifier import NotificationManager

console = Console()

def print_banner():
    console.print(Panel.fit(
        "[bold cyan]OmniTrack 24/7[/bold cyan] - [bold white]AI Multi-Carrier Package Tracker[/bold white]\n[dim]Continuous 24/7 Monitoring - USPS & FedEx - Google Messages SMS & Voice Alerts[/dim]",
        border_style="cyan"
    ))

def cmd_add(args):
    tracker = OmniTracker()
    item = tracker.store.add(
        tracking_number=args.tracking_number,
        nickname=args.nickname or "",
        carrier=args.carrier or "Auto",
        snap_group=args.group,
        friend_mention=args.mention
    )
    console.print(f"[bold green]? Added package:[/bold green] [yellow]{item.tracking_number}[/yellow] ({item.nickname}) [dim][Carrier: {item.carrier}][/dim]")

def cmd_remove(args):
    tracker = OmniTracker()
    if tracker.store.remove(args.tracking_number):
        console.print(f"[bold green]? Removed package:[/bold green] [yellow]{args.tracking_number}[/yellow]")
    else:
        console.print(f"[bold red]? Package {args.tracking_number} not found.[/bold red]")

def cmd_list(args):
    tracker = OmniTracker()
    packages = tracker.store.list_all()
    if not packages:
        console.print("[yellow]No packages currently tracked. Use 'python main.py add <tracking_number>' to add one.[/yellow]")
        return

    table = Table(title="Tracked Packages", box=box.ROUNDED, header_style="bold cyan")
    table.add_column("Nickname", style="bold white")
    table.add_column("Tracking Number", style="yellow")
    table.add_column("Carrier", style="magenta")
    table.add_column("Status", style="bold")
    table.add_column("Latest Event", style="dim")
    table.add_column("Location", style="cyan")
    table.add_column("Delivered", justify="center")
    table.add_column("Last Checked", style="dim")

    for p in packages:
        deliv_str = "[bold green]YES[/bold green]" if p.is_delivered else "[dim]No[/dim]"
        status_style = "green" if p.is_delivered else ("yellow" if "transit" in p.last_status.lower() else "white")
        table.add_row(
            p.nickname,
            p.tracking_number,
            p.carrier,
            f"[{status_style}]{p.last_status}[/{status_style}]",
            p.last_description[:40] + ("..." if len(p.last_description) > 40 else ""),
            p.last_location or "-",
            deliv_str,
            p.last_checked.split("T")[0] if p.last_checked else "Never"
        )
    console.print(table)

async def run_check_cycle(notify: bool = True):
    tracker = OmniTracker()
    notifier = NotificationManager()
    packages = tracker.store.list_all()
    
    if not packages:
        console.print("[dim]No packages in tracker list.[/dim]")
        return

    now_str = datetime.now().strftime("%I:%M:%S %p")
    console.print(f"[cyan][{now_str}] Checking {len(packages)} packages (FedEx & USPS)...[/cyan]")
    for p in packages:
        carrier = p.carrier.upper() if p.carrier else "CARRIER"
        last4 = p.tracking_number[-4:]
        nick = p.nickname or f"{carrier} Package"
        
        console.print(f" [*] Checking [{carrier} #{last4}] ({p.tracking_number})...", end=" ")
        has_changed, updated_item, raw = await tracker.check_package(p.tracking_number, p.carrier)
        
        if has_changed:
            console.print(f"[bold green][NEW UPDATE DETECTED][/bold green] [yellow]{updated_item.last_status}[/yellow] - {updated_item.last_description}")
            if notify:
                await notifier.notify_package_update(updated_item)
        else:
            console.print(f"[dim]No new update on {carrier} (Status: {updated_item.last_status} - {updated_item.last_description[:45]})[/dim]")

def cmd_check(args):
    asyncio.run(run_check_cycle(notify=True))

def cmd_watch(args):
    interval = args.interval or config.check_interval_minutes
    console.print(f"[bold green]Starting OmniTrack 24/7 Daemon[/bold green] (Checking every {interval} mins). Press Ctrl+C to stop.\n")
    
    cycle_count = 1
    while True:
        try:
            console.print(f"[bold blue]--- Cycle #{cycle_count} ---[/bold blue]")
            asyncio.run(run_check_cycle(notify=True))
            next_time = (datetime.now().timestamp() + (interval * 60))
            next_str = datetime.fromtimestamp(next_time).strftime('%I:%M %p')
            console.print(f"[dim]Next scan in {interval} minutes (around {next_str})...\n[/dim]")
            cycle_count += 1
            time.sleep(interval * 60)
        except KeyboardInterrupt:
            console.print("\n[yellow]OmniTrack 24/7 daemon stopped by user.[/yellow]")
            break
        except Exception as e:
            console.print(f"[bold red]Unexpected daemon error:[/bold red] {e}. Retrying in 60 seconds...")
            time.sleep(60)

def cmd_test_notify(args):
    notifier = NotificationManager()
    packages = OmniTracker().store.list_all()
    if not packages:
        console.print("[red]No packages found in tracker.[/red]")
        return
    
    console.print(f"[cyan]Sending clean ASCII test notifications for ALL {len(packages)} packages (FedEx & USPS)...[/cyan]")
    for p in packages:
        console.print(f" ?? Posting update for [yellow]{p.nickname}[/yellow] ({p.carrier})...")
        asyncio.run(notifier.notify_package_update(p, force=True))
        time.sleep(2)

def main():
    print_banner()
    parser = argparse.ArgumentParser(description="OmniTrack Package Tracking CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    p_add = subparsers.add_parser("add", help="Add a package to track")
    p_add.add_argument("tracking_number", help="Package tracking number")
    p_add.add_argument("--nickname", "-n", help="Nickname for package")
    p_add.add_argument("--carrier", "-c", default="Auto", help="Carrier (FedEx, USPS, UPS, Auto)")
    p_add.add_argument("--group", "-g", help="Override Snapchat group chat name")
    p_add.add_argument("--mention", "-m", help="Override friend username to @mention on delivery")

    p_rem = subparsers.add_parser("remove", help="Remove a package from tracking")
    p_rem.add_argument("tracking_number", help="Package tracking number to remove")

    subparsers.add_parser("list", help="List all tracked packages and statuses")
    subparsers.add_parser("check", help="Run a one-time check and send alerts for updates")

    p_watch = subparsers.add_parser("watch", help="Run in continuous 24/7 daemon mode")
    p_watch.add_argument("--interval", "-i", type=int, help="Check interval in minutes (default 60)")

    subparsers.add_parser("test-notify", help="Send test notifications for ALL packages (FedEx & USPS)")

    args = parser.parse_args()

    if args.command == "add":
        cmd_add(args)
    elif args.command == "remove":
        cmd_remove(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "check":
        cmd_check(args)
    elif args.command == "watch":
        cmd_watch(args)
    elif args.command == "test-notify":
        cmd_test_notify(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
