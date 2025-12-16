#!/usr/bin/env python3
"""
Interactive test script for TorBox torrent browsing
Tests search and file navigation (1 level depth)
"""

import base64
import httpx
from dotenv import load_dotenv
import os
from collections import defaultdict
import subprocess

def load_api_key():
    """Load and decode API key from .env"""
    load_dotenv('.env')
    encoded_key = os.getenv('TORBOX_API_KEY')
    return base64.b64decode(encoded_key).decode('utf-8')

def fetch_torrents(api_key):
    """Fetch all torrents from TorBox"""
    url = "https://api.torbox.app/v1/api/torrents/mylist"
    headers = {"Authorization": f"Bearer {api_key}"}
    
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

def parse_files_by_depth(files, current_path="", torrent_root=""):
    """
    Parse files and show only 1 level of depth from current_path.
    Returns dict: {'files': [...], 'folders': [...]}
    """
    items = {'files': [], 'folders': set()}
    
    for file_obj in files:
        full_path = file_obj.get('name', '')
        
        # Remove torrent root name (first directory level)
        parts = full_path.split('/', 1)
        if len(parts) > 1:
            relative_to_root = parts[1]
        else:
            relative_to_root = parts[0]
        
        # Now check if this file is in current_path
        if current_path:
            # We're in a subdirectory
            if not relative_to_root.startswith(current_path + '/'):
                # Skip files not in this directory
                if relative_to_root != current_path:  # Unless it's the exact match
                    continue
            # Get path relative to current directory
            relative_path = relative_to_root[len(current_path):].lstrip('/')
        else:
            # We're at root level
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
        print(f"Error getting streaming URL: {e}")
        return None

def launch_mpv(url):
    """Launch MPV with the streaming URL"""
    mpv_path = os.path.join(os.getcwd(), "mpv.exe")
    
    if not os.path.exists(mpv_path):
        print(f"Error: MPV not found at {mpv_path}")
        return False
    
    try:
        subprocess.Popen([mpv_path, url])
        print("\n✓ MPV launched successfully!")
        return True
    except Exception as e:
        print(f"Error launching MPV: {e}")
        return False

def browse_torrent(torrent, api_key):
    """Interactive file browser for selected torrent"""
    files = torrent.get('files', [])
    torrent_id = torrent.get('id')
    current_path = ""
    
    while True:
        print("\n" + "=" * 60)
        print(f"Torrent: {torrent.get('name', 'Unknown')}")
        print(f"Current path: /{current_path}" if current_path else "Current path: / (root)")
        print("=" * 60)
        
        items = parse_files_by_depth(files, current_path)
        
        # Display folders first
        display_items = []
        for idx, folder in enumerate(sorted(items['folders']), 1):
            display_items.append(('folder', folder, None))
            print(f"{idx}. 📁 {folder}/")
        
        # Then files
        offset = len(items['folders'])
        for idx, file_info in enumerate(sorted(items['files'], key=lambda x: x['name']), 1):
            display_items.append(('file', file_info['name'], file_info))
            size_str = format_size(file_info['size'])
            print(f"{offset + idx}. 📄 {file_info['name']} ({size_str})")
        
        print(f"\n0. Go back" if current_path else f"\n0. Return to search")
        
        # Get user input
        try:
            choice = input("\nSelect item number: ").strip()
            
            if choice == '0':
                if current_path:
                    # Go up one level
                    current_path = '/'.join(current_path.split('/')[:-1])
                else:
                    # Exit browser
                    break
            else:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(display_items):
                    item_type, item_name, item_data = display_items[choice_idx]
                    
                    if item_type == 'folder':
                        # Navigate into folder
                        current_path = f"{current_path}/{item_name}" if current_path else item_name
                    else:
                        # File selected - get streaming URL
                        print(f"\n✓ Selected: {item_name}")
                        print(f"  Size: {format_size(item_data['size'])}")
                        print(f"\nGetting streaming URL...")
                        
                        file_id = item_data['file_obj']['id']
                        streaming_url = get_streaming_url(api_key, torrent_id, file_id)
                        
                        if streaming_url:
                            # Mask API key in displayed URL
                            masked_url = streaming_url.replace(api_key, "***API_KEY***")
                            print(f"\nStreaming URL: {masked_url}")
                            
                            # Ask for confirmation
                            confirm = input("\nLaunch MPV? (y/n): ").strip().lower()
                            if confirm == 'y':
                                launch_mpv(streaming_url)
                            else:
                                print("Cancelled.")
                        else:
                            print("Failed to get streaming URL.")
                        
                        input("\nPress Enter to continue...")
                else:
                    print("Invalid selection!")
        except ValueError:
            print("Please enter a number!")
        except KeyboardInterrupt:
            print("\nExiting browser...")
            break

def main():
    api_key = load_api_key()
    
    # Search
    search_term = input("Enter search term: ").strip()
    
    print(f"\nSearching for: '{search_term}'")
    print("-" * 60)
    
    try:
        torrents = fetch_torrents(api_key)
        matches = search_torrents(torrents, search_term)
        
        print(f"Total torrents: {len(torrents)}")
        print(f"Matches found: {len(matches)}\n")
        
        if not matches:
            print("No matches found.")
            return
        
        # Display search results
        for i, torrent in enumerate(matches, 1):
            files_count = len(torrent.get('files', []))
            print(f"{i}. {torrent.get('name', 'Unknown')}")
            print(f"   ID: {torrent.get('id', 'N/A')}")
            print(f"   Files: {files_count}")
            print()
        
        # Select torrent
        choice = input("Select torrent number (or 0 to exit): ").strip()
        if choice == '0':
            return
        
        torrent_idx = int(choice) - 1
        if 0 <= torrent_idx < len(matches):
            selected_torrent = matches[torrent_idx]
            browse_torrent(selected_torrent, api_key)
        else:
            print("Invalid selection!")
            
    except httpx.HTTPError as e:
        print(f"HTTP Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
