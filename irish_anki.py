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
from locale_manager import _


def respectful_delay():
    time.sleep(2)  # 2 seconds between requests to be respectful


def convert_to_mp3(input_dir, output_dir="mp3_files"):
    """Convert various audio formats to mp3 using ffmpeg, or copy existing MP3s if needed"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        print(_("cli.error.input_directory_not_exist", input_dir=input_dir))
        return False
    
    output_path.mkdir(exist_ok=True)
    
    # Check for existing MP3 files
    mp3_files = list(input_path.glob("*.mp3"))
    
    # Supported audio formats for conversion (excluding MP3)
    audio_extensions = ['.m4a', '.wav', '.flac', '.aac', '.ogg', '.mp4', '.webm']
    
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(input_path.rglob(f'*{ext}'))
    
    # If no files to convert and no MP3s, return error
    if not audio_files and not mp3_files:
        print(_("cli.error.no_audio_files", input_dir=input_dir))
        print(_("cli.info.supported_formats", extensions=', '.join(audio_extensions)))
        return False
    
    # If input and output are the same directory and we have MP3s, no work needed
    if input_path.resolve() == output_path.resolve() and mp3_files:
        print(_("cli.info.input_contains_mp3", count=len(mp3_files)))
        print(_("cli.info.no_conversion_needed"))
        return True
    
    # Check if ffmpeg is available (only if we have files to convert)
    if audio_files:
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(_("cli.error.ffmpeg_not_installed"))
            print(_("cli.error.ffmpeg_install_help"))
            if mp3_files:
                print(_("cli.info.note_mp3_files", count=len(mp3_files)))
            return False
    
    converted = 0
    copied = 0
    skipped = 0
    failed = 0
    total_operations = len(audio_files) + len(mp3_files)
    current_op = 0
    
    # Convert non-MP3 files
    if audio_files:
        print(f"Found {len(audio_files)} audio files to convert")
        
        for audio_file in audio_files:
            current_op += 1
            filename_no_ext = audio_file.stem
            output_file = output_path / f"{filename_no_ext}.mp3"
            
            if output_file.exists():
                print(f"[{current_op}/{total_operations}] Skipping (already exists): {audio_file.name}")
                skipped += 1
                continue
            
            print(f"[{current_op}/{total_operations}] Converting: {audio_file.name}")
            
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
    
    # Copy existing MP3 files if output directory is different
    if mp3_files:
        if audio_files:
            print(f"\nFound {len(mp3_files)} existing MP3 files to copy")
        else:
            print(f"Found {len(mp3_files)} MP3 files to copy to output directory")
        
        for mp3_file in mp3_files:
            current_op += 1
            output_file = output_path / mp3_file.name
            
            if output_file.exists():
                print(f"[{current_op}/{total_operations}] Skipping (already exists): {mp3_file.name}")
                skipped += 1
                continue
            
            print(f"[{current_op}/{total_operations}] Copying: {mp3_file.name}")
            
            try:
                shutil.copy2(str(mp3_file), str(output_file))
                print(f"  ✓ Copied: {mp3_file.name}")
                copied += 1
            except Exception as e:
                print(f"  ✗ Error copying {mp3_file.name}: {e}")
                failed += 1
    
    print(f"\n{_('cli.info.operation_complete')}")
    if converted > 0:
        print(_("cli.info.converted", count=converted))
    if copied > 0:
        print(_("cli.info.copied", count=copied))
    if skipped > 0:
        print(_("cli.info.skipped", count=skipped))
    if failed > 0:
        print(_("cli.info.failed", count=failed))
    print(_("cli.info.mp3_files_location", output_dir=output_dir))
    
    return (converted + copied) > 0


def search_tune_on_thesession(tune_name):
    """Search for a tune on thesession.org and return the first result URL"""
    # Try the exact name first
    search_url = f"https://thesession.org/tunes/search?type=&mode=&q={quote_plus(tune_name)}"
    
    try:
        response = requests.get(search_url, timeout=30)
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
            
            response = requests.get(search_url_with_the, timeout=30)
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
        response = requests.get(tune_url, timeout=30)
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
        print(_("cli.error.directory_not_exist", input_dir=input_dir))
        return False
    
    export_path = Path(export_dir)
    unknown_path = export_path / "unknown"
    
    export_path.mkdir(exist_ok=True)
    unknown_path.mkdir(exist_ok=True)
    
    mp3_files = list(input_path.glob("*.mp3"))
    if not mp3_files:
        print(_("cli.error.no_audio_files", input_dir=input_dir))
        return False
    
    print(_("cli.info.found_mp3_process", count=len(mp3_files)))
    print(_("cli.info.starting_processing"))
    
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



def generate_apkg(music_dir, output_file="irish_music.apkg", deck_name="Irish Traditional Music", randomize_cards=True, card_layout=None):
    music_path = Path(music_dir)
    
    if not music_path.exists():
        print(_("cli.error.music_directory_not_found", music_dir=music_dir))
        return False
    
    # Default layout if none provided
    if card_layout is None:
        card_layout = {
            'front': {'name': False, 'audio': True, 'key': False, 'rhythm': False},
            'back': {'name': True, 'audio': False, 'key': True, 'rhythm': True}
        }
    
    print(_("cli.info.processing_music_directory"))
    cards = process_music_directory(music_path)
    
    if not cards:
        print(_("cli.info.no_valid_music_files"))
        return False
    
    # Randomize the cards if requested
    if randomize_cards:
        random.shuffle(cards)
        print(f"Found {len(cards)} cards to generate (randomized order)")
    else:
        print(f"Found {len(cards)} cards to generate (original order)")
    
    # Build front and back content based on layout
    def build_card_content(side_layout, card_data, filename):
        content_parts = []
        
        if side_layout['name']:
            content_parts.append(f"<div class='field-name'><b>{card_data['title']}</b></div>")
        
        if side_layout['audio']:
            content_parts.append(f"<div class='field-audio'>[sound:{filename}]</div>")
            
        if side_layout['key']:
            content_parts.append(f"<div class='field-key'><b>Key:</b> {card_data['key']}</div>")
            
        if side_layout['rhythm']:
            content_parts.append(f"<div class='field-rhythm'><b>Rhythm:</b> {card_data['rhythm']}</div>")
        
        return '<br>'.join(content_parts) if content_parts else ''
    
    # Log the layout being used
    front_items = [k for k, v in card_layout['front'].items() if v]
    back_items = [k for k, v in card_layout['back'].items() if v]
    print(f"Card layout: Front: {', '.join(front_items) if front_items else 'empty'} | Back: {', '.join(back_items) if back_items else 'empty'}")
    
    # Create Anki model (card template) with dynamic content
    model = genanki.Model(
        1607392320,  # Different model ID for custom layout
        'Irish Traditional Music (Custom)',
        fields=[
            {'name': 'Front'},
            {'name': 'Back'},
        ],
        templates=[
            {
                'name': 'Irish Traditional Card',
                'qfmt': '''
                <div class="card-front">
                {{Front}}
                </div>
                <style>
                .card { font-family: arial; font-size: 20px; text-align: center; }
                .field-name { font-size: 24px; color: #2c5f2d; margin: 10px 0; }
                .field-audio { margin: 15px 0; }
                .field-key { color: #1f4788; margin: 5px 0; }
                .field-rhythm { color: #8b4513; margin: 5px 0; }
                </style>
                ''',
                'afmt': '''
                <div class="card-front">
                {{Front}}
                </div>
                <hr id="answer">
                <div class="card-back">
                {{Back}}
                </div>
                <style>
                .card { font-family: arial; font-size: 20px; text-align: center; }
                .field-name { font-size: 24px; color: #2c5f2d; margin: 10px 0; }
                .field-audio { margin: 15px 0; }
                .field-key { color: #1f4788; margin: 5px 0; }
                .field-rhythm { color: #8b4513; margin: 5px 0; }
                .card-back { margin-top: 20px; }
                </style>
                ''',
            },
        ])
    
    deck = genanki.Deck(
        random.randint(1000000000, 9999999999),  # Random deck ID
        deck_name)
    
    media_files = []
    
    for card in cards:
        original_filename = card['original_file'].name
        
        # Build front and back content based on user selection
        front_content = build_card_content(card_layout['front'], card, original_filename)
        back_content = build_card_content(card_layout['back'], card, original_filename)
        
        # Ensure we don't have completely empty cards
        if not front_content and not back_content:
            front_content = f"[sound:{original_filename}]"  # Fallback to audio
            back_content = f"<b>Title:</b> {card['title']}"  # Fallback to title
        
        note = genanki.Note(
            model=model,
            fields=[front_content, back_content]
        )
        
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


def generate_anki_cards(music_dir, output_file="irish_music.apkg", deck_name="Irish Traditional Music", randomize_cards=True, card_layout=None):
    """Generate Anki cards as .apkg file"""
    if card_layout is None:
        # Default layout: Audio on front, Name + Key + Rhythm on back
        card_layout = {
            'front': {'name': False, 'audio': True, 'key': False, 'rhythm': False},
            'back': {'name': True, 'audio': False, 'key': True, 'rhythm': True}
        }
    return generate_apkg(music_dir, output_file, deck_name, randomize_cards, card_layout)


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
    
    gui_parser = subparsers.add_parser('gui', help='Launch the graphical user interface')
    
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
    
    elif args.command == 'gui':
        try:
            from gui import IrishAnkiGUI
            app = IrishAnkiGUI()
            app.run()
        except ImportError:
            print("Error: GUI dependencies not installed. Please run: pip install dearpygui")
    
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