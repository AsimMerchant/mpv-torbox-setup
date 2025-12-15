# MPV + TorBox Setup - Complete Guide

**System:** AMD Ryzen AI 7 350 w/ Radeon 860M | 32GB RAM | 2560x1600 Display  
**Purpose:** Stream 4K content from TorBox with optimized battery life  
**Setup Date:** December 15, 2025

---

## 🎯 Quick Start - Stream from TorBox

### 1. Get Your TorBox Media Link
1. Go to your TorBox dashboard
2. Find the file you want to stream
3. Click the file → Click "Download"
4. Find the specific media file → Click download icon
5. Choose **"Copy Link"** to copy the streaming URL

### 2. Open MPV and Paste
1. Double-click `mpv.exe` in `C:\Development\repos\MPV_setup\`
2. Press **Ctrl+V** to paste the TorBox link
3. Video starts playing!

**That's it!** The SmartCopyPaste script handles everything automatically.

---

## 📁 Folder Structure

```
C:\Development\repos\MPV_setup\
├── mpv.exe                          ← Main player executable
├── portable_config\
│   ├── mpv.conf                     ← Main configuration (battery optimized)
│   ├── input.conf                   ← Keyboard shortcuts
│   ├── scripts\
│   │   └── SmartCopyPaste.lua       ← Paste URL script
│   └── script-opts\
│       └── SmartCopyPaste.conf      ← Paste script settings
└── [Other MPV files and DLLs]
```

---

## ⌨️ Essential Keyboard Shortcuts

### Basic Playback
| Key | Action |
|-----|--------|
| **Ctrl+V** | **Paste TorBox URL to start streaming** |
| **Space** | Play / Pause |
| **→** | Forward 5 seconds |
| **←** | Backward 5 seconds |
| **↑** | Forward 30 seconds |
| **↓** | Backward 30 seconds |
| **f** | Toggle fullscreen |
| **ESC** | Exit fullscreen |
| **m** | Mute/Unmute |
| **q** | Quit (save position) |

### Monitoring & Stats
| Key | Action |
|-----|--------|
| **i** | Show stats (basic) |
| **I** | Toggle persistent stats |
| **Ctrl+I** | **Show VRAM usage** (Page 4) |
| **?** | Show help overlay |

### Performance Testing
| Key | Action |
|-----|--------|
| **F1** | DirectX 11 mode (Default - Best stability) |
| **F2** | DirectX 12 mode (Test for battery comparison) |
| **F3** | Vulkan mode (Backup option) |
| **F4** | Low Power mode (Extreme battery saving) |

### Screenshots
| Key | Action |
|-----|--------|
| **S** | Screenshot with subtitles |
| **Ctrl+S** | Screenshot video only |

[See input.conf for complete list]

---

## 🔋 Battery Optimization Features

### What's Enabled Automatically:
✅ **Hardware Acceleration** - GPU decodes video (60-70% less CPU power)  
✅ **D3D11 Rendering** - Native DirectX, efficient for AMD  
✅ **Smart Caching** - 200MB buffer reduces network/disk access  
✅ **No Post-Processing** - Skips unnecessary filters for 4K sources  
✅ **Multi-Threading** - Efficient use of your 8-core CPU  

### Monitoring Battery Impact:
1. Press **Ctrl+I** to show detailed stats (Page 4)
2. Look for:
   - **hwdec:** Should show `d3d11va` or `d3d11va-copy` (GPU decoding active)
   - **GPU Memory:** Shows VRAM usage
   - **Dropped frames:** Should be 0 or very low

### Testing Different Modes:
1. Start playback with your TorBox link
2. Press **F1** (D3D11 - default)
3. Watch for ~5 minutes, check battery drain
4. Press **F2** (D3D12) - compare battery usage
5. Use whichever gives better battery life

---

## 🎬 Power Modes for Playback

### Recommended Settings:

**On Battery (4K Playback):**
- Windows Power Mode: **Balanced** or **Best Performance**
- MPV Profile: **Default (F1 - D3D11)**
- Why: Hardware decoding handles 4K efficiently even in balanced mode

**On Battery (Extreme Saving):**
- Windows Power Mode: **Efficiency**
- MPV Profile: **F4 (Low Power)**
- Why: Reduces quality slightly but extends battery significantly

**Plugged In:**
- Windows Power Mode: **Best Performance**
- MPV Profile: **Default (F1)**
- Why: No restrictions, full quality

---

## 📊 Understanding Stats Overlay

Press **i** or **Ctrl+I** to see stats. Here's what matters:

```
Hardware Decoding
└── hwdec: d3d11va          ← GPU is decoding ✅
    hwdec: no               ← CPU is decoding ❌ (bad for battery!)

Performance
├── Dropped Frames: 0       ← Should be 0 or very low
├── GPU Memory: 450 MB      ← VRAM usage (monitor this)
└── Cache: 180/200 MB       ← Buffer status

Video Info
├── Resolution: 3840x2160   ← Your 4K source
└── FPS: 23.976             ← Frame rate
```

**If you see issues:**
- **hwdec shows "no"** → Press **Ctrl+H** to toggle hardware decoding
- **Dropped frames** → Check network speed or lower quality
- **GPU Memory very high** → Normal for 4K, but monitor if system slows

---

## 🔧 Troubleshooting

### Video Won't Play / Stutters
1. Check internet connection (4K needs ~25-50 Mbps)
2. Press **Ctrl+I** - verify hwdec is active
3. Wait for cache to fill (see cache % in stats)
4. Try **F4** (Low Power mode) if still stuttering

### High Battery Drain
1. Press **Ctrl+I** - verify **hwdec: d3d11va** is showing
2. If shows "hwdec: no":
   - Press **Ctrl+H** to re-enable hardware decoding
   - If still doesn't work, GPU drivers may need update
3. Switch Windows to **Balanced** or **Best Performance** mode
4. Close other applications

### Black Screen / No Video
1. Press **Ctrl+H** to toggle hardware decoding
2. If fixed → AMD driver issue, try updating
3. Try **F3** (Vulkan mode)

### Audio Out of Sync
1. Press **z** to delay audio -100ms
2. Press **x** to delay audio +100ms
3. Repeat until synchronized

### TorBox Link Expired
- TorBox links expire after ~1 hour of pause
- Copy a new link from TorBox dashboard
- Press **Ctrl+V** to resume

---

## 🎛️ Advanced Configuration

### Changing Settings

Edit `portable_config\mpv.conf`:
- Use any text editor (Notepad, VS Code, etc.)
- Lines starting with `#` are comments
- Save and restart MPV

### Common Tweaks:

**Reduce cache (save RAM):**
```
demuxer-max-bytes=100M          # Change from 200M to 100M
```

**Always start fullscreen:**
```
fullscreen=yes                  # Add this line
```

**Change volume step:**
```
# In input.conf, change:
UP add volume 5                 # Instead of 2
```

---

## 📝 Configuration Profiles

You can create custom profiles in `mpv.conf`:

```conf
[my-profile-name]
profile-desc="Description"
setting1=value1
setting2=value2
```

Activate with: `mpv --profile=my-profile-name [file]`

---

## 🆘 Support & Resources

### Official MPV Documentation
- Website: https://mpv.io/
- Manual: https://mpv.io/manual/stable/
- Wiki: https://github.com/mpv-player/mpv/wiki

### TorBox Support
- Dashboard: https://torbox.app/
- Support: https://support.torbox.app/
- Discord: https://join-discord.torbox.app/

### This Setup
- Configuration: See `portable_config\mpv.conf` (heavily commented)
- Keybindings: See `portable_config\input.conf` (all shortcuts listed)

---

## ✅ Setup Complete Checklist

- [x] MPV portable extracted
- [x] Hardware acceleration configured (D3D11)
- [x] SmartCopyPaste script installed (Ctrl+V support)
- [x] Battery optimizations enabled
- [x] Cache configured for streaming (200MB)
- [x] Keyboard shortcuts set up
- [x] VRAM monitoring available (Ctrl+I)
- [x] Multiple rendering profiles (F1-F4)

---

## 🚀 Next Steps

1. **Test with TorBox:**
   - Get a media link from TorBox
   - Open MPV
   - Press Ctrl+V
   - Verify playback works

2. **Monitor Performance:**
   - Press **Ctrl+I** during playback
   - Check hwdec status
   - Note VRAM usage
   - Watch battery drain rate

3. **Optimize if Needed:**
   - Test F1/F2/F3 profiles
   - Adjust cache in mpv.conf
   - Fine-tune based on your usage

**Enjoy your 4K content! 🎬**
