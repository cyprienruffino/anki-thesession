# Irish Traditional Music Anki Cards

This tool generates Anki flashcards from Irish traditional music files. It uses ffmpeg for audio conversion and [The Session](https://thesession.org/) to automatically find metadata (key, rhythm, proper title) for each tune. 

**Note**: This tool does not provide music files - you must bring your own legally obtained Irish traditional music collection, for example by ["ripping your own albums"](https://github.com/makuguren/Spotify-Playlist-Downloader) or ["recording yourself"](https://github.com/yt-dlp/yt-dlp).


![Irish Anki GUI](screenshot.jpg)

- **Audio conversion** from various formats (m4a, wav, flac, aac, ogg, mp4, webm) to mp3 using ffmpeg
- **Respectful web scraping** of thesession.org with appropriate delays
- **Smart tune matching** that handles "The " prefixes and variations
- **Automatic file organization** by rhythm (jigs, reels, polkas, etc.)
- **Customizable card layouts** - choose what appears on front/back (name, audio, key, rhythm)
- **Anki card generation** with audio files and metadata

## Usage

## 🚀 Quick Start

### Option 1: Use the GUI (Recommended)

**Windows Users**: Download the latest `IrishAnki.exe` from [Releases](../../releases) - no installation required

**Linux/Mac Users**: 
```bash
# Clone and setup
git clone <this-repository>
cd anki-irish
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run the GUI
python gui.py
```

### Using the GUI:

1. **📁 Select Input Directory**: Click "Browse" to navigate and visually confirm your audio files
2. **⚙️ Configure Options**: Set output paths and deck name (defaults work great!)
3. **🎴 Customize Card Layout**: Choose what appears on front/back of your Anki cards
4. **🎯 Click "Run All Steps"**: Sit back and watch the magic happen
5. **📱 Import to Anki**: Double-click the generated `.apkg` file

## 🎵 How It Works

The workflow transforms your raw audio files into organized Anki cards:

**Audio Files → MP3 → Organized by Rhythm → Anki Deck**

1. **🎵 PROCESS**: Converts audio formats (.m4a, .wav, .flac, etc.) to MP3 or copies existing MP3s
2. **🗂️ ORGANIZE**: Searches thesession.org for metadata and organizes by rhythm  
3. **🎴 GENERATE**: Creates Anki .apkg file with audio cards

## 🎯 Example Workflow

```
Input Directory:
├── Cooley's Reel.m4a
├── The Kesh Jig.wav
├── Bill Sullivan's Polka.mp3
└── Random Song.flac

After Processing:
export/
├── reel/
│   └── Cooley's (Edor).mp3
├── jig/
│   └── The Kesh (Gmaj).mp3
├── polka/
│   └── Bill Sullivan's (Amaj).mp3
├── unknown/
│   └── Random Song.mp3
└── irish_music.apkg  ← Ready to import!
```

## 📱 Anki Import

### Desktop Anki
1. Double-click the generated `.apkg` file, or
2. File → Import → select the `.apkg` file

### AnkiDroid (Android)
1. Install AnkiDroid from Google Play Store
2. Copy the `.apkg` file to your device
3. Open AnkiDroid → Menu (⋮) → Import
4. Select the `.apkg` file

### Card Format

**Default Layout**:
- **Front**: 🎵 Audio file of the tune (tap to play)  
- **Back**: 🏷️ Name + 🎼 Key + 🎭 Rhythm

**Customizable Options**:
- **🏷️ Name**: The tune's title (e.g., "Cooley's Reel")
- **🎵 Audio**: Playable audio file
- **🎼 Key**: Musical key (e.g., "Edor", "Gmaj")  
- **🎭 Rhythm**: Type of tune (e.g., "reel", "jig", "polka")

**Suggested Layouts**:
- **Audio-first** (default): 🎵 → 🏷️🎼🎭
- **Name-first**: 🏷️ → 🎵🎼🎭  
- **Key training**: 🎵 → 🎼

## ⚙️ Advanced Usage (Command Line)

For automation or advanced users, the command-line interface is still available:

### Complete Workflow
```bash
python irish_anki.py all <input_directory>
```

### Individual Steps
```bash
# 1. Convert audio files to mp3
python irish_anki.py convert <input_directory>

# 2. Organize files by rhythm
python irish_anki.py organize <mp3_directory>

# 3. Generate Anki cards
python irish_anki.py generate-cards <organized_music_directory>
```

### Custom Options
```bash
# Custom output locations and deck name
python irish_anki.py all tmp/music/ \
  --output my_collection.apkg \
  --deck-name "My Irish Collection" \
  --mp3-dir converted/ \
  --export-dir organized/
```

## 🛠️ Requirements

### For GUI Usage
- **Windows**: Download `IrishAnki.exe` (no requirements!)
- **Linux/Mac**: Python 3.8+ and packages below

### Python Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- `requests` - Web scraping thesession.org
- `beautifulsoup4` - HTML parsing  
- `genanki` - Anki deck generation

### External Dependencies
- **[ffmpeg](https://ffmpeg.org/download.html)** - Audio conversion
- **[Anki](https://apps.ankiweb.net/)** - For importing cards

## 🎼 File Organization Strategy

The tool intelligently organizes your music:

1. **🔍 Search**: Queries thesession.org using filename
2. **🎵 Extract**: Parses ABC notation for metadata
3. **📁 Organize**: Files become `rhythm/Title (Key).mp3`
4. **❓ Unknown**: Unmatched files go to `unknown/` for manual review

**Supported Formats**: m4a, wav, flac, aac, ogg, mp4, webm → mp3

## 🐛 Troubleshooting

**GUI won't start**: Ensure Python 3.8+ and run `pip install -r requirements.txt`

**Audio conversion fails**: Install [ffmpeg](https://ffmpeg.org/download.html) and ensure it's in PATH

**No tunes found**: Check your filenames match Irish traditional tune names

**Large .apkg files**: This is normal - audio files are embedded for offline use

Files that can't be matched are copied to the `unknown` directory for manual review.

Recognized rhythms are : 
- reel
- jig
- slide
- slipjig
- polka
- waltz
- hornpipe
- barndance
- marzuka
- strathspey
- march
