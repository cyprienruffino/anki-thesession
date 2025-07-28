# Irish Traditional Music Anki Cards

This project helps you convert, organize Irish traditional music files and generate Anki flashcards from them. It uses ffmpeg for audio conversion and [The Session](https://thesession.org/) to automatically find metadata (key, rhythm, proper title) for each tune and organizes your collection accordingly. I do not provide tunes, you'll have to bring them yourself.

## Features

- **Audio conversion** from various formats (m4a, wav, flac, aac, ogg, mp4, webm) to mp3 using ffmpeg
- **Respectful web scraping** of thesession.org with appropriate delays
- **Smart tune matching** that handles "The " prefixes and variations
- **Automatic file organization** by rhythm (jigs, reels, polkas, etc.)
- **Anki card generation** with audio files and metadata
- **Unified workflow** in a single script

## Usage

The script has four main commands:

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

This will create Anki cards from already organized music files.

### 4. Do everything in one go
```bash
python3 irish_anki.py all <input_directory>
```

This combines all steps: convert to mp3, organize the files, then generate Anki cards.

## Example Workflow

```bash
# Process your raw audio files (m4a, wav, etc.)
python3 irish_anki.py all tmp/yt-dlp/

# This will:
# 1. Convert all audio files to mp3 in mp3_files/
# 2. Organize mp3s by rhythm in export/
# 3. Generate Anki cards in anki_import/

# Final structure:
# - mp3_files/Cooley's.mp3, Banshee.mp3, etc.
# - export/jig/The_Kesh (Gmaj).mp3
# - export/reel/Cooley's (Edor).mp3
# - export/polka/Bill_Sullivan's (Amaj).mp3
# - anki_import/anki_cards.csv
# - anki_import/media/jig_the_kesh.mp3
```

## Command Options

```bash
# Convert only
python3 irish_anki.py convert tmp/yt-dlp/ --output converted_mp3/

# Organize with custom output directory
python3 irish_anki.py organize mp3_files/ --output my_music

# Generate cards with custom output
python3 irish_anki.py generate-cards export/ --output my_anki_cards

# Full workflow with custom directories
python3 irish_anki.py all tmp/yt-dlp/ --mp3-dir converted --export-dir organized --anki-dir flashcards
```

## Import into Anki

1. Open Anki on your computer
2. Click "File" > "Import"
3. Select the generated CSV file (`anki_import/anki_cards.csv`)
4. In the import dialog:
   - Set "Type" to "Basic"
   - Set "Deck" to your desired deck name
   - Ensure "Fields separated by: comma" is selected
   - Check that "Allow HTML in fields" is enabled
5. Click "Import"

The cards will have:
- **Front**: Audio file of the tune
- **Back**: Rhythm, key, and title

## AnkiDroid

To use these cards on your Android device:

1. Install AnkiDroid from the Google Play Store
2. On your computer, export your deck:
   - Open Anki Desktop
   - Select your deck
   - Click "File" > "Export"
   - Choose "Anki Deck Package (.apkg)" as format
   - Save the file
3. On your Android device:
   - Copy the .apkg file to your device
   - Open AnkiDroid
   - Tap the three dots menu
   - Select "Import"
   - Navigate to and select the .apkg file
   - The deck will be imported

## Requirements

- Python 3.6+
- Python packages:
  - `requests`
  - `beautifulsoup4`
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
