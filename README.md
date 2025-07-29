# Irish Traditional Music Anki Cards

This project helps you convert, organize Irish traditional music files and generate Anki flashcards from them. It uses ffmpeg for audio conversion and [The Session](https://thesession.org/) to automatically find metadata (key, rhythm, proper title) for each tune and organizes your collection accordingly. I do not provide tunes, you'll have to bring them yourself, for example by ["ripping albums"](https://github.com/yt-dlp/yt-dlp)

## Features

- **Audio conversion** from various formats (m4a, wav, flac, aac, ogg, mp4, webm) to mp3 using ffmpeg
- **Respectful web scraping** of thesession.org with appropriate delays
- **Smart tune matching** that handles "The " prefixes and variations
- **Automatic file organization** by rhythm (jigs, reels, polkas, etc.)
- **Anki card generation** with audio files and metadata

## Usage

The script has three main commands:

### 1. Convert audio files to mp3
```bash
python3 irish_anki.py convert <input_directory>
```

This will convert various audio formats (m4a, wav, flac, aac, ogg, mp4, webm) to mp3 using ffmpeg.

### 2. Organize files only
```bash
python3 irish_anki.py organize <mp3_directory>
```

This will:
- Search thesession.org for each mp3 file in the directory using the name of the file (ex. The Banshee.mp3)
- Extract title, rhythm, and key
- Copy files to `export/rhythm/Title (Key).mp3` format
- Move unmatched files to `export/unknown/`

### 3. Generate Anki cards only
```bash
python3 irish_anki.py generate-cards <organized_music_directory>
```

This creates a ready-to-import .apkg file from already organized music files.

### 4. Do everything in one go
```bash
python3 irish_anki.py all <input_directory>
```

This combines all steps: convert to mp3, organize the files, then generate a ready-to-import .apkg file.

## Example Workflow

```bash
# Process your raw audio files (m4a, wav, etc.)
python3 irish_anki.py all tmp/yt-dlp/

# This will:
# 1. Convert all audio files to mp3 in mp3_files/
# 2. Organize mp3s by rhythm in export/
# 3. Generate irish_music.apkg ready to import!

# Final structure:
# - mp3_files/Cooley's.mp3, Banshee.mp3, etc.
# - export/jig/The_Kesh (Gmaj).mp3
# - export/reel/Cooley's (Edor).mp3
# - export/polka/Bill_Sullivan's (Amaj).mp3
# - irish_music.apkg (ready to import!)
```

## Command Options

```bash
# Convert only
python3 irish_anki.py convert tmp/yt-dlp/ --output converted_mp3/

# Organize with custom output directory
python3 irish_anki.py organize mp3_files/ --output my_music

# Generate .apkg with custom name and deck
python3 irish_anki.py generate-cards export/ --output my_irish_music.apkg --deck-name "My Collection"

# Full workflow with custom .apkg name
python3 irish_anki.py all tmp/yt-dlp/ --output my_collection.apkg --deck-name "Traditional Irish"
```

## Import into Anki

Just double-click the generated `.apkg` file, or:

1. **Desktop Anki**: File > Import > select the `.apkg` file
2. **AnkiDroid**: Import the `.apkg` file directly

Everything is included - no manual setup needed!

The cards will have:
- **Front**: Audio file of the tune (click to play)  
- **Back**: Rhythm, key, and title


## AnkiDroid

To use these cards on your Android device:

1. Install AnkiDroid from the Google Play Store
2. Copy the generated `.apkg` file to your device
3. Open AnkiDroid and tap the three dots menu
4. Select "Import" and navigate to the `.apkg` file
5. The deck will be imported with all audio files included

## Requirements

- Python 3.6+
- Python packages:
  - `requests`
  - `beautifulsoup4` 
  - `genanki` (for .apkg generation)
- [ffmpeg](https://ffmpeg.org/download.html) for audio conversion
- [Anki](https://apps.ankiweb.net/) for importing cards

Install dependencies:
```bash
pip install -r requirements.txt
```

## File Organization

The script works with various audio formats (m4a, wav, flac, aac, ogg, mp4, webm) and will:

1. **Convert** audio files to mp3 format using ffmpeg
2. **Search** thesession.org for each tune
3. **Extract** metadata (title, rhythm, key) from ABC notation
4. **Organize** files as: `rhythm/Title (Key).mp3`
5. **Generate** Anki cards with clean filenames

Files that can't be matched are copied to the `unknown` directory for manual review.
