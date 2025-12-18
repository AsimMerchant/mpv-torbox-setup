#!/usr/bin/env python3
"""
TorBox TUI Browser
Browse and stream TorBox content with MPV, with watch tracking and JDownloader2 integration
"""

import base64
import httpx
from dotenv import load_dotenv
import os
import json
import subprocess
import time
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
import myjdapi

console = Console()

SESSION_FILE = ".torbox_session.json"

# Global JD API instance
jd_api = None
jd_device = None

def load_api_key():
    """Load and decode API key from .env"""
    load_dotenv('.env')
    encoded_key = os.getenv('TORBOX_API_KEY')
    return base64.b64decode(encoded_key).decode('utf-8')

def load_jd_credentials():
    """Load My.JDownloader credentials from .env"""
    load_dotenv('.env')
    email = os.getenv('MYJD_EMAIL')
    encoded_password = os.getenv('MYJD_PASSWORD')
    device_name = os.getenv('MYJD_DEVICE_NAME')
    
    if not all([email, encoded_password, device_name]):
        return None, None, None
    
    password = base64.b64decode(encoded_password).decode('utf-8')
    return email, password, device_name

def ensure_jd2_running():
    """Check if JDownloader2 is running, launch it if not"""
    jd2_path = r"C:\Users\asrie\AppData\Local\JDownloader 2"
    jd2_exe = os.path.join(jd2_path, "JDownloader2.exe")
    
    # Check if JDownloader2 process is running
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-Process -Name 'JDownloader2' -ErrorAction SilentlyContinue"],
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            # JD2 is already running
            return True
        
        # JD2 not running, launch it
        if not os.path.exists(jd2_exe):
            console.print(f"[red]JDownloader2.exe not found at: {jd2_exe}[/red]")
            return False
        
        console.print("[cyan]Starting JDownloader2...[/cyan]")
        subprocess.Popen([jd2_exe], cwd=jd2_path)
        
        # Wait a bit for JD2 to start
        console.print("[cyan]Waiting for JDownloader2 to initialize (10 seconds)...[/cyan]")
        time.sleep(10)
        
        return True
    except Exception as e:
        console.print(f"[red]Error checking/starting JDownloader2: {e}[/red]")
        return False

def connect_to_jd():
    """Connect to My.JDownloader and get device"""
    global jd_api, jd_device
    
    if jd_device:
        return jd_device
    
    # Ensure JD2 is running first
    if not ensure_jd2_running():
        console.print("[red]Cannot start JDownloader2[/red]")
        return None
    
    email, password, device_name = load_jd_credentials()
    if not email:
        console.print("[yellow]My.JDownloader credentials not configured in .env[/yellow]")
        return None
    
    try:
        jd_api = myjdapi.Myjdapi()
        jd_api.set_app_key("TORBOX_BROWSER")
        jd_api.connect(email, password)
        jd_api.update_devices()
        jd_device = jd_api.get_device(device_name)
        
        if not jd_device:
            console.print(f"[red]Device '{device_name}' not found[/red]")
            return None
        
        return jd_device
    except Exception as e:
        console.print(f"[red]Failed to connect to My.JDownloader: {e}[/red]")
        return None

def load_watch_folder():
    """Load JDownloader2 watch folder from .env"""
    load_dotenv('.env')
    watch_folder = os.getenv('JDOWNLOADER_WATCH_FOLDER')
    if not watch_folder:
        console.print("[yellow]JDOWNLOADER_WATCH_FOLDER not found in .env[/yellow]")
        return None
    if not os.path.exists(watch_folder):
        console.print(f"[red]Watch folder does not exist: {watch_folder}[/red]")
        return None
    return watch_folder

def load_session():
    """Load previous session data"""
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

def save_session(data):
    """Save session data"""
    with open(SESSION_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, indent=2, fp=f)

def clear_session():
    """Clear watch history"""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
        console.print("[green]✓ Watch history cleared![/green]")
    else:
        console.print("[yellow]No watch history to clear.[/yellow]")

def check_if_exists_in_jd2(device, url):
    """Check if URL already exists in JDownloader2 (linkgrabber or downloads)"""
    try:
        # Check linkgrabber
        linkgrabber_links = device.linkgrabber.query_links([{
            "url": True,
            "bytesTotal": False,
            "enabled": False,
            "maxResults": -1,
            "startAt": 0
        }])
        
        for link in linkgrabber_links:
            if link.get('url') == url:
                return True, "linkgrabber"
        
        # Check downloads
        download_links = device.downloads.query_links([{
            "url": True,
            "bytesTotal": False,
            "enabled": False,
            "maxResults": -1,
            "startAt": 0
        }])
        
        for link in download_links:
            if link.get('url') == url:
                return True, "downloads"
        
        return False, None
    except Exception as e:
        # If check fails, assume it doesn't exist and continue
        console.print(f"[yellow]Warning: Could not check for duplicates: {e}[/yellow]")
        return False, None

def send_file_to_jd2(api_key, torrent_id, file_id, file_name, device=None):
    """Send a single file to JDownloader2 via API"""
    if not device:
        device = connect_to_jd()
        if not device:
            console.print("[red]JDownloader2 not connected[/red]")
            return False
    
    # Get the CDN download URL
    cdn_url = get_streaming_url(api_key, torrent_id, file_id)
    if not cdn_url:
        console.print(f"[red]Failed to get URL for: {file_name}[/red]")
        return False
    
    # Check if already in JD2
    exists, location = check_if_exists_in_jd2(device, cdn_url)
    if exists:
        console.print(f"[yellow]⊘ Already in {location}: {file_name}[/yellow]")
        return False
    
    try:
        # Add to linkgrabber with autostart enabled
        device.linkgrabber.add_links([{
            "autostart": True,
            "links": cdn_url,
            "packageName": "TorBox Downloads",
            "destinationFolder": None,
            "extractPassword": None,
            "priority": "DEFAULT",
            "downloadPassword": None,
            "overwritePackagizerRules": False
        }])
        console.print(f"[green]✓ Added & started: {file_name}[/green]")
        return True
    except Exception as e:
        console.print(f"[red]Failed to send to JD2: {e}[/red]")
        return False

def send_folder_to_jd2(api_key, torrent_id, files_list):
    """Send all files in a folder to JDownloader2 via API"""
    if not files_list:
        console.print("[yellow]No files in this folder[/yellow]")
        return
    
    device = connect_to_jd()
    if not device:
        return
    
    console.print(f"\n[cyan]Sending {len(files_list)} files to JDownloader2...[/cyan]")
    success_count = 0
    
    for file_info in files_list:
        file_id = file_info['file_obj']['id']
        file_name = file_info['name']
        if send_file_to_jd2(api_key, torrent_id, file_id, file_name, device):
            success_count += 1
        time.sleep(0.1)  # Small delay to avoid overwhelming JD2
    
    console.print(f"\n[green]✓ Successfully sent {success_count}/{len(files_list)} files to JDownloader2[/green]")

def send_torrent_to_jd2(api_key, torrent_id, all_files):
    """Send all files in a torrent to JDownloader2 via API"""
    if not all_files:
        console.print("[yellow]No files in this torrent[/yellow]")
        return
    
    device = connect_to_jd()
    if not device:
        return
    
    console.print(f"\n[cyan]Sending entire torrent ({len(all_files)} files) to JDownloader2...[/cyan]")
    success_count = 0
    
    for file_obj in all_files:
        file_id = file_obj.get('id')
        file_name = file_obj.get('short_name', 'unknown')
        if send_file_to_jd2(api_key, torrent_id, file_id, file_name, device):
            success_count += 1
        time.sleep(0.1)  # Small delay to avoid overwhelming JD2
    
    console.print(f"\n[green]✓ Successfully sent {success_count}/{len(all_files)} files to JDownloader2[/green]")

def fetch_torrents(api_key):
    """Fetch all torrents from TorBox"""
    url = "https://api.torbox.app/v1/api/torrents/mylist"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    with console.status("[bold blue]Fetching torrents..."):
        response = httpx.get(
            url,
            headers=headers,
            params={"limit": 1000, "offset": 0, "bypass_cache": True},
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()['data']

def search_torrents(torrents, search_term):
    """Filter torrents by search term (case-insensitive)"""
    return [t for t in torrents if search_term.lower() in t.get('name', '').lower()]

def parse_files_by_depth(files, current_path=""):
    """Parse files and show only 1 level of depth from current_path"""
    items = {'files': [], 'folders': set()}
    
    for file_obj in files:
        full_path = file_obj.get('name', '')
        
        # Remove torrent root name (first directory level)
        parts = full_path.split('/', 1)
        if len(parts) > 1:
            relative_to_root = parts[1]
        else:
            relative_to_root = parts[0]
        
        # Check if this file is in current_path
        if current_path:
            if not relative_to_root.startswith(current_path + '/'):
                if relative_to_root != current_path:
                    continue
            relative_path = relative_to_root[len(current_path):].lstrip('/')
        else:
            relative_path = relative_to_root
        
        # Split by '/' to get depth
        path_parts = relative_path.split('/')
        
        if len(path_parts) == 1 and path_parts[0]:
            # It's a file at current level
            items['files'].append({
                'name': path_parts[0],
                'size': file_obj.get('size', 0),
                'full_path': full_path,
                'file_obj': file_obj
            })
        elif len(path_parts) > 1:
            # It's inside a folder
            items['folders'].add(path_parts[0])
    
    return items

def format_size(bytes_size):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"

def get_streaming_url(api_key, torrent_id, file_id):
    """Get streaming URL for a specific file"""
    url = "https://api.torbox.app/v1/api/torrents/requestdl"
    
    try:
        with console.status("[bold blue]Getting streaming URL..."):
            response = httpx.get(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                params={"token": api_key, "torrent_id": torrent_id, "file_id": file_id},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('success') and 'data' in data:
                return data['data']
            else:
                return None
    except Exception as e:
        console.print(f"[red]Error getting streaming URL: {e}[/red]")
        return None

def launch_mpv(url):
    """Launch MPV with the streaming URL"""
    mpv_path = os.path.join(os.getcwd(), "mpv.exe")
    
    if not os.path.exists(mpv_path):
        console.print(f"[red]Error: MPV not found at {mpv_path}[/red]")
        return False
    
    try:
        # Launch with resume playback support
        console.print(f"[dim]Launching: {mpv_path}[/dim]")
        console.print(f"[dim]Arguments: --save-position-on-quit --resume-playback[/dim]")
        
        process = subprocess.Popen([
            mpv_path,
            "--save-position-on-quit",
            "--resume-playback",
            "--demuxer-max-bytes=1000M",
            "--demuxer-readahead-secs=60",
            "--cache=yes",
            "--stream-buffer-size=16M",
            url
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait longer to check if MPV actually started
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            # Process is running
            console.print("[green]✓ MPV process started (PID: {})![/green]".format(process.pid))
            return True
        else:
            # Process exited immediately (error)
            console.print(f"[red]Error: MPV exited with code {process.returncode}[/red]")
            
            # Show error output if available
            stderr = process.stderr.read().decode('utf-8', errors='ignore')
            if stderr:
                console.print(f"[red]Error output: {stderr[:500]}[/red]")
            
            return False
            
    except Exception as e:
        console.print(f"[red]Error launching MPV: {e}[/red]")
        return False

def get_file_status(session_data, file_path):
    """Get watch status for a file"""
    if not session_data or 'watch_status' not in session_data:
        return None
    return session_data['watch_status'].get(file_path)

def update_watch_status(session_data, file_path, status):
    """Update watch status for a file"""
    if 'watch_status' not in session_data:
        session_data['watch_status'] = {}
    session_data['watch_status'][file_path] = status

def browse_torrent(torrent, api_key, session_data):
    """Interactive file browser for selected torrent"""
    files = torrent.get('files', [])
    torrent_id = torrent.get('id')
    current_path = session_data.get('current_path', '') if session_data else ''
    
    while True:
        console.clear()
        
        # Header
        title = Text(torrent.get('name', 'Unknown'), style="bold cyan")
        subtitle = f"Path: /{current_path}" if current_path else "Path: / (root)"
        console.print(Panel(f"{title}\n{subtitle}", border_style="blue"))
        
        items = parse_files_by_depth(files, current_path)
        
        # Display folders first
        display_items = []
        for idx, folder in enumerate(sorted(items['folders']), 1):
            display_items.append(('folder', folder, None))
            console.print(f"{idx}. 📁 [cyan]{folder}/[/cyan]")
        
        # Then files with status
        offset = len(items['folders'])
        for idx, file_info in enumerate(sorted(items['files'], key=lambda x: x['name']), 1):
            display_items.append(('file', file_info['name'], file_info))
            size_str = format_size(file_info['size'])
            
            # Check watch status
            status = get_file_status(session_data, file_info['full_path'])
            if status == 'in-progress':
                console.print(f"{offset + idx}. 📄 [yellow]{file_info['name']}[/yellow] [dim]({size_str})[/dim] 🟡")
            elif status == 'completed':
                console.print(f"{offset + idx}. 📄 [green]{file_info['name']}[/green] [dim]({size_str})[/dim] ✅")
            else:
                console.print(f"{offset + idx}. 📄 {file_info['name']} [dim]({size_str})[/dim]")
        
        console.print(f"\n0. {'[yellow]Go back[/yellow]' if current_path else '[red]Exit[/red]'}")
        console.print("c. [cyan]Clear watch history[/cyan]")
        console.print("d. [magenta]Download (JDownloader2)[/magenta]")
        
        # Get user input
        choice = Prompt.ask("\n[bold]Select item").strip().lower()
        
        if choice == '0':
            if current_path:
                # Go up one level
                current_path = '/'.join(current_path.split('/')[:-1])
            else:
                # Exit browser
                break
        elif choice == 'c':
            clear_session()
            session_data = {'watch_status': {}}
            input("\nPress Enter to continue...")
        elif choice == 'd':
            # Download with JDownloader2
            # If at root, ask to download entire torrent
            if not current_path:
                confirm = Prompt.ask(f"\n[yellow]Download entire torrent ({len(files)} files)?[/yellow]", choices=["y", "n"], default="n")
                if confirm == 'y':
                    send_torrent_to_jd2(api_key, torrent_id, files)
                    input("\nPress Enter to continue...")
            else:
                # Download current folder's files
                if items['files']:
                    confirm = Prompt.ask(f"\n[yellow]Download all files in this folder ({len(items['files'])} files)?[/yellow]", choices=["y", "n"], default="n")
                    if confirm == 'y':
                        send_folder_to_jd2(api_key, torrent_id, items['files'])
                        input("\nPress Enter to continue...")
                else:
                    console.print("[yellow]No files to download in this folder[/yellow]")
                    input("\nPress Enter to continue...")
        else:
            try:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(display_items):
                    item_type, item_name, item_data = display_items[choice_idx]
                    
                    if item_type == 'folder':
                        # Navigate into folder
                        current_path = f"{current_path}/{item_name}" if current_path else item_name
                    else:
                        # File selected - show action menu
                        console.print(f"\n[bold]Selected:[/bold] {item_name}")
                        console.print(f"Size: {format_size(item_data['size'])}")
                        
                        action = Prompt.ask("\n[bold]Action[/bold]", 
                                          choices=["p", "c", "d", "b"],
                                          default="p",
                                          show_choices=True,
                                          show_default=True)
                        
                        if action == 'p':
                            # Play - mark in-progress, launch MPV, exit
                            file_id = item_data['file_obj']['id']
                            streaming_url = get_streaming_url(api_key, torrent_id, file_id)
                            
                            if streaming_url:
                                # Launch MPV first to verify it works
                                if launch_mpv(streaming_url):
                                    # Only save session and exit if MPV launched successfully
                                    update_watch_status(session_data, item_data['full_path'], 'in-progress')
                                    session_data['current_path'] = current_path
                                    session_data['torrent_id'] = torrent_id
                                    session_data['torrent_name'] = torrent.get('name')
                                    session_data['last_file'] = item_data['full_path']
                                    save_session(session_data)
                                    
                                    console.print("\n[dim]Exiting TUI...[/dim]")
                                    return True  # Signal to exit
                                else:
                                    console.print("[red]MPV failed to launch. Not exiting.[/red]")
                                    input("\nPress Enter to continue...")
                            else:
                                console.print("[red]Failed to get streaming URL.[/red]")
                                input("\nPress Enter to continue...")
                        
                        elif action == 'c':
                            # Mark completed
                            update_watch_status(session_data, item_data['full_path'], 'completed')
                            session_data['current_path'] = current_path
                            session_data['torrent_id'] = torrent_id
                            session_data['torrent_name'] = torrent.get('name')
                            save_session(session_data)
                            console.print("[green]✓ Marked as completed![/green]")
                        
                        elif action == 'd':
                            # Download with JDownloader2
                            file_id = item_data['file_obj']['id']
                            send_file_to_jd2(api_key, torrent_id, file_id, item_name)
                            input("\nPress Enter to continue...")
                        
                        # action == 'b' just continues the loop
                else:
                    console.print("[red]Invalid selection![/red]")
                    input("\nPress Enter to continue...")
            except ValueError:
                console.print("[red]Please enter a number![/red]")
                input("\nPress Enter to continue...")
    
    return False  # Normal exit

def main():
    """Main application loop"""
    console.clear()
    console.print(Panel.fit("🎬 [bold cyan]TorBox TUI Browser[/bold cyan] 🎬", border_style="cyan"))
    
    api_key = load_api_key()
    session_data = load_session()
    
    # Check for previous session
    if session_data and session_data.get('torrent_id'):
        console.print(f"\n[yellow]Previous session found:[/yellow]")
        console.print(f"  Torrent: {session_data.get('torrent_name', 'Unknown')}")
        console.print(f"  Path: /{session_data.get('current_path', '')}")
        
        resume = Prompt.ask("\nResume last session?", choices=["y", "n"], default="y")
        
        if resume == 'y':
            # Fetch torrents and find the one from session
            try:
                torrents = fetch_torrents(api_key)
                torrent = next((t for t in torrents if t['id'] == session_data['torrent_id']), None)
                
                if torrent:
                    should_exit = browse_torrent(torrent, api_key, session_data)
                    if should_exit:
                        return
                else:
                    console.print("[red]Previous torrent not found. Starting new search...[/red]")
                    input("\nPress Enter to continue...")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                input("\nPress Enter to continue...")
        else:
            session_data = {'watch_status': session_data.get('watch_status', {})}
    else:
        session_data = {'watch_status': {}}
    
    # New search
    while True:
        console.clear()
        console.print(Panel.fit("🔍 [bold]Search TorBox Torrents[/bold] 🔍", border_style="cyan"))
        
        search_term = Prompt.ask("\n[bold]Enter search term (or 'exit' to quit)[/bold]").strip()
        
        if search_term.lower() == 'exit':
            break
        
        if not search_term:
            continue
        
        try:
            torrents = fetch_torrents(api_key)
            matches = search_torrents(torrents, search_term)
            
            if not matches:
                console.print(f"\n[yellow]No torrents found matching '{search_term}'[/yellow]")
                input("\nPress Enter to continue...")
                continue
            
            # Display results
            console.clear()
            console.print(Panel.fit(f"🔍 Search Results: '{search_term}'", border_style="green"))
            console.print(f"\n[dim]Total torrents: {len(torrents)} | Matches: {len(matches)}[/dim]\n")
            
            for i, torrent in enumerate(matches, 1):
                files_count = len(torrent.get('files', []))
                console.print(f"{i}. [cyan]{torrent.get('name', 'Unknown')}[/cyan]")
                console.print(f"   [dim]ID: {torrent.get('id')} | Files: {files_count}[/dim]\n")
            
            console.print("\n[dim]Actions:[/dim]")
            console.print("  [dim]• Enter number to browse torrent[/dim]")
            console.print("  [dim]• Enter 'd' followed by number (e.g., 'd1') to download entire torrent[/dim]")
            
            choice = Prompt.ask("\n[bold]Select torrent (or 0 to search again)[/bold]").strip()
            
            if choice == '0':
                continue
            
            # Check for download command (e.g., 'd1', 'd2')
            if choice.lower().startswith('d'):
                try:
                    torrent_idx = int(choice[1:]) - 1
                    if 0 <= torrent_idx < len(matches):
                        selected_torrent = matches[torrent_idx]
                        files = selected_torrent.get('files', [])
                        confirm = Prompt.ask(f"\n[yellow]Download entire torrent '{selected_torrent.get('name')}' ({len(files)} files)?[/yellow]", choices=["y", "n"], default="n")
                        if confirm == 'y':
                            send_torrent_to_jd2(api_key, selected_torrent.get('id'), files)
                            input("\nPress Enter to continue...")
                    else:
                        console.print("[red]Invalid selection![/red]")
                        input("\nPress Enter to continue...")
                except (ValueError, IndexError):
                    console.print("[red]Invalid download command! Use 'd' followed by torrent number (e.g., 'd1')[/red]")
                    input("\nPress Enter to continue...")
                continue
            
            try:
                torrent_idx = int(choice) - 1
                if 0 <= torrent_idx < len(matches):
                    selected_torrent = matches[torrent_idx]
                    should_exit = browse_torrent(selected_torrent, api_key, session_data)
                    if should_exit:
                        break
                else:
                    console.print("[red]Invalid selection![/red]")
                    input("\nPress Enter to continue...")
            except ValueError:
                console.print("[red]Please enter a number![/red]")
                input("\nPress Enter to continue...")
                
        except httpx.HTTPError as e:
            console.print(f"[red]HTTP Error: {e}[/red]")
            input("\nPress Enter to continue...")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            input("\nPress Enter to continue...")
    
    console.print("\n[cyan]Goodbye! 👋[/cyan]")

if __name__ == "__main__":
    main()
