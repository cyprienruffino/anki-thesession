#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


class LocaleManager:
    """Manages localization for the Irish Anki application."""
    
    def __init__(self, locale_dir: str = "locales", default_locale: str = "en"):
        self.locale_dir = Path(resource_path(locale_dir))
        self.default_locale = default_locale
        self.current_locale = default_locale
        self.strings: Dict[str, str] = {}
        self.available_locales = self._discover_locales()
        self.load_locale(default_locale)
    
    def _discover_locales(self) -> Dict[str, str]:
        """Discover available locale files and return locale code -> display name mapping."""
        locales = {}
        if not self.locale_dir.exists():
            return {"en": "English"}
        
        locale_names = {
            "en": "English",
            "fr": "Français", 
            "ga": "Gaeilge"
        }
        
        for locale_file in self.locale_dir.glob("*.json"):
            locale_code = locale_file.stem
            display_name = locale_names.get(locale_code, locale_code.upper())
            locales[locale_code] = display_name
        
        # Always ensure English is available as fallback
        if "en" not in locales:
            locales["en"] = "English"
        
        return locales
    
    def load_locale(self, locale_code: str) -> bool:
        """Load strings for the specified locale."""
        locale_file = self.locale_dir / f"{locale_code}.json"
        
        # Try to load the requested locale
        if locale_file.exists():
            try:
                with open(locale_file, 'r', encoding='utf-8') as f:
                    self.strings = json.load(f)
                self.current_locale = locale_code
                return True
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load locale {locale_code}: {e}")
        
        # Fallback to default locale if requested locale fails
        if locale_code != self.default_locale:
            return self.load_locale(self.default_locale)
        
        # If even default locale fails, use hardcoded English strings
        self.strings = self._get_fallback_strings()
        self.current_locale = "en"
        return False
    
    def get(self, key: str, **kwargs) -> str:
        """Get a localized string by key, with optional string formatting."""
        # Handle nested keys with dot notation
        keys = key.split('.')
        value = self.strings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # Fallback to key itself if not found
                return key
        
        if isinstance(value, str):
            # Apply string formatting if kwargs provided
            if kwargs:
                try:
                    return value.format(**kwargs)
                except (KeyError, ValueError):
                    return value
            return value
        
        # Return key if value is not a string
        return key
    
    def set_locale(self, locale_code: str) -> bool:
        """Change the current locale."""
        if locale_code in self.available_locales:
            return self.load_locale(locale_code)
        return False
    
    def get_current_locale(self) -> str:
        """Get the current locale code."""
        return self.current_locale
    
    def get_available_locales(self) -> Dict[str, str]:
        """Get available locales as code -> display name mapping."""
        return self.available_locales.copy()
    
    def _get_fallback_strings(self) -> Dict:
        """Hardcoded English strings as last resort fallback."""
        return {
            "gui": {
                "title": "Irish Traditional Music to Anki Cards Generator",
                "button": {
                    "browse": "Browse",
                    "process_audio": "Process Audio",
                    "organize_files": "Organize Files", 
                    "generate_cards": "Generate Cards",
                    "run_all": "🎯 Run All Steps",
                    "clear_console": "Clear Console",
                    "up": "Up",
                    "refresh": "Refresh",
                    "cancel": "Cancel",
                    "choose_directory": "Choose This Directory"
                },
                "label": {
                    "input_directory": "Input Directory:",
                    "mp3_directory": "MP3 Directory:",
                    "export_directory": "Export Directory:",
                    "output_file": "Output .apkg File:",
                    "deck_name": "Deck Name:",
                    "language": "Language:",
                    "current_directory": "Current Directory:",
                    "name": "Name",
                    "type": "Type", 
                    "size": "Size"
                },
                "section": {
                    "directories_files": "📁 Directories and Files",
                    "options": "⚙️ Options",
                    "card_layout": "🎴 Card Layout",
                    "actions": "🚀 Actions",
                    "status": "📊 Status",
                    "console_output": "Console Output",
                    "front_side": "Front Side",
                    "back_side": "Back Side"
                },
                "checkbox": {
                    "randomize_cards": "Randomize Cards",
                    "name": "🏷️ Name",
                    "audio": "🎵 Audio", 
                    "key": "🎼 Key",
                    "rhythm": "🎭 Rhythm"
                },
                "status": {
                    "ready": "Ready",
                    "processing": "Processing...",
                    "completed": "Completed!",
                    "failed": "Failed",
                    "error": "Error occurred"
                },
                "console": {
                    "help_text": "Console output will appear here...\n\n💡 Quick Start:\n1. Select your Input Directory with audio files\n2. Click 'Run All Steps' for the complete workflow\n3. Import the generated .apkg file into Anki\n"
                },
                "workflow": {
                    "title": "📖 How it works (click to expand)",
                    "title_collapsed": "📖 How it works (click to collapse)",
                    "description": "Workflow: Audio Files → MP3 → Organized by Rhythm → Anki Deck\n\n1. 🎵 PROCESS: Converts audio formats (.m4a, .wav, .flac, etc.) to MP3 or copies existing MP3s\n2. 🗂️  ORGANIZE: Searches thesession.org for metadata and organizes by rhythm  \n3. 🎴 GENERATE: Creates Anki .apkg file with audio cards\n\n💡 You can run steps individually or use 'Run All Steps' for the complete workflow"
                },
                "card_layout": {
                    "instruction": "Choose what appears on the front and back of your Anki cards:",
                    "preview": "💡 Default: 🎵 Audio on front, 🏷️ Name + 🎼 Key + 🎭 Rhythm on back"
                },
                "dialog": {
                    "select_directory": "Select Directory",
                    "select_input_directory": "Select Input Directory with Audio Files",
                    "save_anki_deck": "Save Anki Deck As"
                },
                "file_types": {
                    "folder": "📁 Folder",
                    "audio": "🎵 Audio",
                    "file": "📄 File",
                    "error": "Error",
                    "permission_denied": "[Permission Denied]"
                }
            },
            "cli": {
                "error": {
                    "directory_not_found": "Error: Directory '{path}' does not exist",
                    "no_audio_files": "No audio files found in '{path}'",
                    "ffmpeg_missing": "Error: ffmpeg is not installed or not in PATH"
                },
                "info": {
                    "processing_files": "Found {count} audio files to convert",
                    "operation_complete": "Operation complete!",
                    "converted": "Converted: {count}",
                    "copied": "Copied: {count}",
                    "skipped": "Skipped: {count}",
                    "failed": "Failed: {count}"
                }
            }
        }


# Global locale manager instance
_locale_manager = None

def get_locale_manager() -> LocaleManager:
    """Get the global locale manager instance."""
    global _locale_manager
    if _locale_manager is None:
        _locale_manager = LocaleManager()
    return _locale_manager

def _(key: str, **kwargs) -> str:
    """Shorthand function for getting localized strings."""
    return get_locale_manager().get(key, **kwargs)

def set_language(locale_code: str) -> bool:
    """Set the application language."""
    return get_locale_manager().set_locale(locale_code)

def get_current_language() -> str:
    """Get current language code."""
    return get_locale_manager().get_current_locale()

def get_available_languages() -> Dict[str, str]:
    """Get available languages."""
    return get_locale_manager().get_available_locales()
