import asyncio
import subprocess
from rich.console import Console
from rich.table import Table
from rich import box
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from pynput import keyboard
import re
import os
import threading

console = Console()

DOWNLOAD_URL_TEMPLATE = "https://marketplace.visualstudio.com/_apis/public/gallery/publishers/{publisher}/vsextensions/{extension}/latest/vspackage"

DEBUG = False

def debug_log(message):
    if DEBUG:
        console.log(message)

async def vsce_search(query):
    debug_log("Running vsce search")
    process = await asyncio.create_subprocess_exec(
        'vsce', 'search', query,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"vsce search failed: {stderr.decode()}")

    debug_log("Parsing search results")
    lines = stdout.decode().splitlines()
    results = []
    seen = set()

    for line in lines:
        match = re.match(r'^([a-zA-Z0-9-_]+)\.([a-zA-Z0-9-_]+)', line)
        if match:
            extension_id = match.group(0)
            if extension_id not in seen:
                seen.add(extension_id)
                publisher, extension = extension_id.split('.', 1)
                results.append({
                    "name": extension_id,
                    "publisher": publisher,
                    "extension": extension,
                    "selected": False
                })
    debug_log(f"Found {len(results)} extensions")
    return results

async def download_vsix(ext):
    url = DOWNLOAD_URL_TEMPLATE.format(
        publisher=ext["publisher"],
        extension=ext["extension"]
    )
    filename = f"{ext['publisher']}.{ext['extension']}.vsix"
    debug_log(f"Downloading from {url} to {filename}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        transient=True,
        console=console,
    ) as progress:
        task = progress.add_task(f"Downloading {filename}...", start=False)
        progress.start_task(task)

        process = await asyncio.create_subprocess_exec(
            'curl', '-L', '-o', filename, url,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        await process.communicate()
        progress.update(task, completed=100)

    if process.returncode != 0:
        raise RuntimeError(f"Download failed")
    return filename

async def interactive_selection(results):
    index = 0
    max_index = len(results) - 1
    stop_event = threading.Event()

    def draw():
        os.system('cls' if os.name == 'nt' else 'clear')
        table = Table(title="VS Code Extensions (Use arrow keys to move, space to select, Enter to download)", box=box.SIMPLE)
        table.add_column("#", style="bold green", justify="right")
        table.add_column("Selected", justify="center")
        table.add_column("Extension ID", style="bold white")
        for i, res in enumerate(results):
            cursor = "→" if i == index else " "
            selected = "[bold green]✔[/]" if res["selected"] else ""
            table.add_row(str(i), selected, f"{cursor} {res['name']}")
        console.print(table)

    def on_press(key):
        nonlocal index
        try:
            if key == keyboard.Key.up:
                index = max(0, index - 1)
                draw()
            elif key == keyboard.Key.down:
                index = min(max_index, index + 1)
                draw()
            elif key == keyboard.Key.space:
                results[index]["selected"] = not results[index]["selected"]
                draw()
            elif key == keyboard.Key.enter:
                debug_log("Enter pressed, finalizing selection")
                stop_event.set()
                return False
        except Exception as e:
            debug_log(f"Key press error: {e}")

    draw()
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    # Wait in a separate thread to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, stop_event.wait)

    listener.stop()
    return [r for r in results if r["selected"]]

async def main():
    try:
        query = console.input("[bold cyan]Enter search term[/]: ")
        console.print(f"[yellow]Searching for '{query}'...[/]")
        results = await vsce_search(query)

        if not results:
            console.print("[red]No results found.[/]")
            return

        selected_extensions = await interactive_selection(results)
        debug_log(f"Selected extensions: {selected_extensions}")

        if not selected_extensions:
            console.print("[red]No extensions selected.[/]")
            return

        for ext in selected_extensions:
            console.print(f"[blue]Downloading [bold]{ext['name']}[/]...[/]")
            try:
                filename = await download_vsix(ext)
                console.print(f"[green]Downloaded as [bold]{filename}[/]")
            except Exception as e:
                console.print(f"[red]Download failed:[/] {e}")
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted by user.[/]")

if __name__ == "__main__":
    asyncio.run(main())
