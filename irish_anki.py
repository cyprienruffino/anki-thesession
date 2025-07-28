#!/usr/bin/env python3

import random
import time
import re
import shutil
import argparse
import subprocess
from pathlib import Path
from urllib.parse import quote_plus
from typing import List, Tuple
import requests
from bs4 import BeautifulSoup
import genanki


def respectful_delay():
    time.sleep(2)  # 2 seconds between requests to be respectful


def convert_to_mp3(input_dir, output_dir="mp3_files"):
    """Convert various audio formats to mp3 using ffmpeg"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist")
        return False
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: ffmpeg is not installed or not in PATH")
        print("Please install ffmpeg: https://ffmpeg.org/download.html")
        return False
    
    output_path.mkdir(exist_ok=True)
    
    # Supported audio formats
    audio_extensions = ['.m4a', '.wav', '.flac', '.aac', '.ogg', '.mp4', '.webm']
    
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(input_path.rglob(f'*{ext}'))
    
    if not audio_files:
        print(f"No audio files found in '{input_dir}'")
        return False
    
    print(f"Found {len(audio_files)} audio files to convert")
    print(f"Converting to mp3 format in '{output_dir}'...")
    
    converted = 0
    skipped = 0
    failed = 0
    
    for i, audio_file in enumerate(audio_files, 1):
        filename_no_ext = audio_file.stem
        output_file = output_path / f"{filename_no_ext}.mp3"
        
        if output_file.exists():
            print(f"[{i}/{len(audio_files)}] Skipping (already exists): {audio_file.name}")
            skipped += 1
            continue
        
        print(f"[{i}/{len(audio_files)}] Converting: {audio_file.name}")
        
        try:
            # Convert to mp3 with good quality settings
            result = subprocess.run([
                'ffmpeg', '-i', str(audio_file),
                '-codec:a', 'libmp3lame',
                '-b:a', '192k',
                '-y', str(output_file)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  ✓ Success: {filename_no_ext}.mp3")
                converted += 1
            else:
                print(f"  ✗ Failed: {audio_file.name}")
                failed += 1
                
        except Exception as e:
            print(f"  ✗ Error converting {audio_file.name}: {e}")
            failed += 1
    
    print(f"\nConversion complete!")
    print(f"  Converted: {converted}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed: {failed}")
    print(f"MP3 files are in: {output_dir}")
    
    return converted > 0


def search_tune_on_thesession(tune_name):
    """Search for a tune on thesession.org and return the first result URL"""
    # Try the exact name first
    search_url = f"https://thesession.org/tunes/search?type=&mode=&q={quote_plus(tune_name)}"
    
    try:
        response = requests.get(search_url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for the first tune result link
        tune_links = soup.find_all('a', href=re.compile(r'/tunes/\d+'))
        if tune_links:
            first_tune_url = "https://thesession.org" + tune_links[0]['href']
            return first_tune_url
        
        # If no results found and tune doesn't start with "The ", try adding "The "
        if not tune_name.lower().startswith('the '):
            print(f"  No results for '{tune_name}', trying 'The {tune_name}'")
            search_url_with_the = f"https://thesession.org/tunes/search?type=&mode=&q={quote_plus('The ' + tune_name)}"
            
            response = requests.get(search_url_with_the, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            tune_links = soup.find_all('a', href=re.compile(r'/tunes/\d+'))
            if tune_links:
                first_tune_url = "https://thesession.org" + tune_links[0]['href']
                return first_tune_url
        
        return None
        
    except Exception as e:
        print(f"Error searching for '{tune_name}': {e}")
        return None


def extract_abc_metadata(tune_url):
    """Extract T:, R:, K: metadata from the ABC notation on a tune page"""
    try:
        response = requests.get(tune_url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        abc_text = None

        if not abc_text:
            all_text = soup.get_text()
            lines = all_text.split('\n')
            abc_lines = []
            in_abc_section = False
            
            for line in lines:
                line = line.strip()
                if line.startswith('X:'):
                    in_abc_section = True
                    abc_lines = [line]
                elif in_abc_section:
                    abc_lines.append(line)
                    # Stop when we hit musical notation or next section
                    if line.startswith('|') or (line and not any(line.startswith(prefix) for prefix in ['T:', 'R:', 'M:', 'L:', 'K:', 'X:', 'C:', 'O:', 'A:', 'N:', 'Z:', 'H:', 'S:', 'B:', 'F:', 'I:', 'P:'])):
                        break
                    # If we have enough ABC headers, we can stop looking
                    if any(l.startswith('K:') for l in abc_lines):
                        break
            
            if abc_lines and any(l.startswith('T:') for l in abc_lines) and any(l.startswith('K:') for l in abc_lines):
                abc_text = '\n'.join(abc_lines)
        
        if not abc_text:
            print(f"  Could not find ABC notation section")
            return None, None, None
        
        title_match = re.search(r'^T:\s*(.+)$', abc_text, re.MULTILINE)
        rhythm_match = re.search(r'^R:\s*(.+)$', abc_text, re.MULTILINE)
        key_match = re.search(r'^K:\s*(.+)$', abc_text, re.MULTILINE)
        
        title = title_match.group(1).strip() if title_match else None
        rhythm = rhythm_match.group(1).strip() if rhythm_match else None
        key = key_match.group(1).strip() if key_match else None
        
        if not all([title, rhythm, key]):
            print(f"  Debug - ABC text found: {abc_text[:300]}...")
            print(f"  Debug - T: {title}, R: {rhythm}, K: {key}")
        
        return title, rhythm, key
        
    except Exception as e:
        print(f"Error extracting ABC metadata from {tune_url}: {e}")
        return None, None, None


def sanitize_filename(filename):
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = filename.strip(' .')
    return filename


def organize_music_files(input_dir, export_dir="export"):
    """Organize mp3 files by crawling thesession.org for metadata"""
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"Error: Directory '{input_dir}' does not exist")
        return False
    
    export_path = Path(export_dir)
    unknown_path = export_path / "unknown"
    
    export_path.mkdir(exist_ok=True)
    unknown_path.mkdir(exist_ok=True)
    
    mp3_files = list(input_path.glob("*.mp3"))
    if not mp3_files:
        print(f"No mp3 files found in '{input_dir}'")
        return False
    
    print(f"Found {len(mp3_files)} mp3 files to process")
    print("Starting processing with respectful delays...")
    
    processed = []
    unknown_files = []
    errors = []
    
    for i, mp3_file in enumerate(mp3_files, 1):
        tune_name = mp3_file.stem
        print(f"\n[{i}/{len(mp3_files)}] Processing: {tune_name}")
        
        tune_url = search_tune_on_thesession(tune_name)
        if not tune_url:
            print(f"  No results found, copying to unknown")
            try:
                shutil.copy2(str(mp3_file), str(unknown_path / mp3_file.name))
                unknown_files.append(tune_name)
            except Exception as e:
                errors.append(f"Failed to copy {tune_name}: {e}")
            respectful_delay()
            continue
        
        print(f"  Found: {tune_url}")
        respectful_delay()
        
        title, rhythm, key = extract_abc_metadata(tune_url)
        if not all([title, rhythm, key]):
            print(f"  Could not extract complete metadata (T:{title}, R:{rhythm}, K:{key}), copying to unknown")
            try:
                shutil.copy2(str(mp3_file), str(unknown_path / mp3_file.name))
                unknown_files.append(tune_name)
            except Exception as e:
                errors.append(f"Failed to copy {tune_name}: {e}")
            respectful_delay()
            continue
        
        print(f"  Metadata - Title: {title}, Rhythm: {rhythm}, Key: {key}")
        
        rhythm_dir = export_path / sanitize_filename(rhythm)
        rhythm_dir.mkdir(exist_ok=True)
        
        safe_title = sanitize_filename(title)
        safe_key = sanitize_filename(key)
        new_filename = f"{safe_title} ({safe_key}).mp3"
        target_path = rhythm_dir / new_filename
        
        try:
            shutil.copy2(str(mp3_file), str(target_path))
            processed.append({
                'original': tune_name,
                'title': title,
                'rhythm': rhythm,
                'key': key,
                'new_path': str(target_path)
            })
            print(f"  Copied to: {target_path}")
        except Exception as e:
            errors.append(f"Failed to copy {tune_name}: {e}")
        
        respectful_delay()
    
    print(f"\n{'='*60}")
    print("ORGANIZATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total files processed: {len(mp3_files)}")
    print(f"Successfully organized: {len(processed)}")
    print(f"Moved to unknown: {len(unknown_files)}")
    print(f"Errors: {len(errors)}")
    
    if processed:
        print(f"\nSuccessfully organized files:")
        for item in processed:
            print(f"  {item['original']} -> {item['rhythm']}/{item['title']} ({item['key']}).mp3")
    
    if unknown_files:
        print(f"\nFiles moved to unknown (not found or incomplete metadata):")
        for filename in unknown_files:
            print(f"  {filename}")
    
    if errors:
        print(f"\nErrors encountered:")
        for error in errors:
            print(f"  {error}")
    
    return len(processed) > 0


def clean_filename(text: str) -> str:
    clean = re.sub(r'[^\w\s-]', '', text.lower())
    clean = re.sub(r'\s+', '_', clean)
    clean = re.sub(r'-+', '_', clean)
    return clean


def parse_filename(filename: str) -> List[Tuple[str, str]]:
    """Parse a filename to extract title(s) and key(s). Returns list of (title, key) tuples."""
    name = filename.replace('.mp3', '')
    match = re.match(r'^(.+?)\s*\(([^)]+)\)$', name)
    if match:
        title, key = match.groups()
        return [(title.strip(), key.strip())]
    return []


def format_key(key: str) -> str:
    """Format the key for display (e.g., 'Dmaj' -> 'D major')."""
    key_mapping = {
        'maj': ' major',
        'min': ' minor',
        'dor': ' dorian',
        'mix': ' mixolydian',
        'aeo': ' aeolian',
        'ion': ' ionian',
        'phr': ' phrygian',
        'loc': ' locrian',
        'lyd': ' lydian'
    }
    
    for abbrev, full in key_mapping.items():
        if key.lower().endswith(abbrev):
            root = key[:-len(abbrev)]
            return root + full
    
    return key


def process_music_directory(music_dir: Path) -> List[dict]:
    cards = []
    
    for rhythm_dir in music_dir.iterdir():
        if not rhythm_dir.is_dir():
            continue
            
        rhythm = rhythm_dir.name
        
        for audio_file in rhythm_dir.glob('*.mp3'):
            tune_info = parse_filename(audio_file.name)
            
            if not tune_info:
                print(f"Warning: Could not parse filename: {audio_file.name}")
                continue
            
            title, key = tune_info[0]
            formatted_key = format_key(key)
            clean_name = clean_filename(f"{rhythm}_{title}")
            
            cards.append({
                'original_file': audio_file,
                'clean_filename': f"{clean_name}.mp3",
                'rhythm': rhythm,
                'title': title,
                'key': formatted_key
            })

    return cards



def generate_apkg(music_dir, output_file="irish_music.apkg", deck_name="Irish Traditional Music", randomize_cards=True):
    music_path = Path(music_dir)
    
    if not music_path.exists():
        print(f"Error: Music directory '{music_dir}' not found!")
        return False
    
    print("Processing music directory for .apkg generation...")
    cards = process_music_directory(music_path)
    
    if not cards:
        print("No valid music files found!")
        return False
    
    # Randomize the cards if requested
    if randomize_cards:
        random.shuffle(cards)
        print(f"Found {len(cards)} cards to generate (randomized order)")
    else:
        print(f"Found {len(cards)} cards to generate (original order)")
    
    # Create Anki model (card template)
    model = genanki.Model(
        1607392319,  # Random model ID
        'Irish Traditional Music',
        fields=[
            {'name': 'Audio'},
            {'name': 'Info'},
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '{{Audio}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Info}}',
            },
        ])
    
    deck = genanki.Deck(
        random.randint(1000000000, 9999999999),  # Random deck ID
        deck_name)
    
    media_files = []
    
    for card in cards:
        original_filename = card['original_file'].name
        
        note = genanki.Note(
            model=model,
            fields=[
                f"[sound:{original_filename}]",
                f"<b>Rhythm:</b> {card['rhythm']}<br><b>Key:</b> {card['key']}<br><b>Title:</b> {card['title']}"
            ])
        
        deck.add_note(note)
        media_files.append(str(card['original_file']))
    
    output_path = Path(output_file)
    print(f"\nGenerating .apkg file: {output_path}")
    
    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(str(output_path))
    
    print(f"Generated {output_path} with {len(cards)} cards!")
    if randomize_cards:
        print("Cards have been randomized for varied study sessions!")
    print(f"Ready to import: Just double-click the .apkg file or import in Anki/AnkiDroid")
    
    return True


def generate_anki_cards(music_dir, output_file="irish_music.apkg", deck_name="Irish Traditional Music", randomize_cards=True):
    """Generate Anki cards as .apkg file"""
    return generate_apkg(music_dir, output_file, deck_name, randomize_cards)


def main():
    parser = argparse.ArgumentParser(description='Convert, organize and process Irish traditional music files with thesession.org and generate Anki cards')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    convert_parser = subparsers.add_parser('convert', help='Convert audio files to mp3 format using ffmpeg')
    convert_parser.add_argument('input_dir', help='Directory containing audio files to convert')
    convert_parser.add_argument('--output', default='mp3_files', help='Output directory for mp3 files (default: mp3_files)')

    organize_parser = subparsers.add_parser('organize', help='Organize music files using thesession.org metadata')
    organize_parser.add_argument('input_dir', help='Directory containing mp3 files to organize')
    organize_parser.add_argument('--output', default='export', help='Output directory (default: export)')
    
    generate_parser = subparsers.add_parser('generate-cards', help='Generate Anki .apkg file from organized music files')
    generate_parser.add_argument('music_dir', help='Directory containing organized music files')
    generate_parser.add_argument('--output', default='irish_music.apkg', help='Output .apkg file (default: irish_music.apkg)')
    generate_parser.add_argument('--deck-name', default='Irish Traditional Music', help='Deck name (default: Irish Traditional Music)')
    generate_parser.add_argument('--no-randomize', action='store_true', help='Keep cards in original order instead of randomizing')
    
    all_parser = subparsers.add_parser('all', help='Convert to mp3, organize files and generate Anki .apkg')
    all_parser.add_argument('input_dir', help='Directory containing audio files to process')
    all_parser.add_argument('--mp3-dir', default='mp3_files', help='Intermediate directory for mp3 files (default: mp3_files)')
    all_parser.add_argument('--export-dir', default='export', help='Intermediate directory for organized files (default: export)')
    all_parser.add_argument('--output', default='irish_music.apkg', help='Output .apkg file (default: irish_music.apkg)')
    all_parser.add_argument('--deck-name', default='Irish Traditional Music', help='Deck name (default: Irish Traditional Music)')
    all_parser.add_argument('--no-randomize', action='store_true', help='Keep cards in original order instead of randomizing')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'convert':
        convert_to_mp3(args.input_dir, args.output)
    
    elif args.command == 'organize':
        organize_music_files(args.input_dir, args.output)
    
    elif args.command == 'generate-cards':
        generate_anki_cards(args.music_dir, args.output, args.deck_name, not args.no_randomize)
    
    elif args.command == 'all':
        print("Step 1: Converting audio files to mp3...")
        if convert_to_mp3(args.input_dir, args.mp3_dir):
            print(f"\nStep 2: Organizing music files...")
            if organize_music_files(args.mp3_dir, args.export_dir):
                print(f"\nStep 3: Generating Anki .apkg file...")
                generate_anki_cards(args.export_dir, args.output, args.deck_name, not args.no_randomize)
            else:
                print("Organization failed, skipping Anki card generation")
        else:
            print("Conversion failed, skipping remaining steps")


if __name__ == "__main__":
    main() 