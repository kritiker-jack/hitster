#!/usr/bin/env python3
"""
Hitster Deck CLI Importer for GitHub Actions and Local Use
Usage:
  python cli_import.py --url "https://open.spotify.com/playlist/..." [--name "Custom Name"]
"""

import os
import sys
import json
import re
import argparse
from server import fetch_spotify_playlist, extract_playlist_id

DECKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'decks')
INDEX_FILE = os.path.join(DECKS_DIR, 'index.json')

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text).strip('_')
    return text[:40] or "playlist"

def ensure_decks_dir():
    if not os.path.exists(DECKS_DIR):
        os.makedirs(DECKS_DIR)

def load_deck_index():
    ensure_decks_dir()
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_deck_index(index_data):
    ensure_decks_dir()
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

def import_playlist_to_deck(playlist_url, custom_name=None, clean_titles=True, require_preview=True):
    ensure_decks_dir()
    playlist_id = extract_playlist_id(playlist_url)
    if not playlist_id:
        print(f"❌ Ungültiger Spotify Playlist-Link: {playlist_url}")
        sys.exit(1)

    print(f"⏳ Lade Playlist {playlist_id} von Spotify und prüfe jede Audio-Vorschau...")
    data = fetch_spotify_playlist(playlist_id, clean_titles=clean_titles, require_preview=require_preview)
    
    playlist_name = custom_name or data.get('playlistName', 'Hitster Playlist')
    songs = data.get('songs', [])
    skipped = data.get('skippedCount', 0)
    
    if not songs:
        print("❌ Keine spielbaren Songs mit Audio-Vorschau gefunden!")
        sys.exit(1)

    print(f"🎯 {len(songs)} spielbare Songs mit 100% verifizierter Audio-Vorschau übernommen ({skipped} ohne Vorschau aussortiert).")

    slug = slugify(playlist_name)
    deck_filename = f"{slug}.json"
    deck_path = os.path.join(DECKS_DIR, deck_filename)

    with open(deck_path, 'w', encoding='utf-8') as f:
        json.dump(songs, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(songs)} Songs gespeichert in {deck_filename}")

    # Update decks/index.json
    index_data = load_deck_index()
    # Remove existing entry if slug matches
    index_data = [d for d in index_data if d.get('slug') != slug]

    index_data.append({
        "id": slug,
        "slug": slug,
        "name": playlist_name,
        "count": len(songs),
        "file": f"decks/{deck_filename}"
    })

    save_deck_index(index_data)
    print(f"✅ Deck-Index aktualisiert ({len(index_data)} Decks im Verzeichnis)")
    return playlist_name, len(songs)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Spotify Playlist in Hitster Deck umwandeln")
    parser.add_argument('--url', required=True, help="Spotify Playlist URL")
    parser.add_argument('--name', required=False, help="Optionaler Name für das Deck")
    parser.add_argument('--no-clean', action='store_true', help="Titel nicht bereinigen")

    args = parser.parse_args()
    name, count = import_playlist_to_deck(args.url, custom_name=args.name, clean_titles=not args.no_clean)
    print(f"🎉 Fertig! '{name}' ({count} Karten) ist einsatzbereit.")
