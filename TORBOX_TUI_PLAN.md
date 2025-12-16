# TorBox TUI Browser - Implementation Plan

## Finalized API Approach

### Search Functionality

**Endpoint:** `GET https://api.torbox.app/v1/api/torrents/mylist`

**Parameters:**
- `limit=1000` - Fetch all torrents at once
- `offset=0` - Start from beginning
- `bypass_cache=true` - Get fresh data

**Authentication:**
- Base64-encoded API key stored in `.env.example`
- Python decodes base64 → uses real key
- Header: `Authorization: Bearer {decoded_key}`

**Search Logic:**
1. Fetch ALL torrents in one API call (55 total currently)
2. Filter locally by search term (case-insensitive)
3. Display only torrent names and file counts
4. Do NOT display individual files until user selects a torrent

**Performance:**
- Tested with "One Piece" (1509 files per torrent)
- API response: ~2-3 seconds
- Memory usage: Acceptable (few MB of JSON)
- Python handles 3000+ file objects without issues

**Display Format:**
```
1. Torrent Name Here
   ID: 1234567
   Files: 1509
```

---

## File Browser Functionality

### After selecting a torrent:

**Show 1 level of depth:**
- Display files and folders at current level only
- Example structure:
  ```
  1. Video.mkv (file, 65GB)
  2. Subtitles/ (folder)
  3. Extras/ (folder)
  ```

**Navigation:**
- User selects a folder → navigate into it, show its contents (1 level)
- User can go back to parent directory
- User selects a file → (action to be determined)

**File Path Parsing:**
- API returns: `TorrentName/Subfolder/File.mkv`
- Parse path and build tree structure
- Display current directory level only

---

## Next Steps
- Determine what happens when user selects a video file
