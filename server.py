import os
import sys
import json
import re
import socket
import urllib.request
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor

try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

PORT = 5055
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
    'Sec-Ch-Ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1'
}

def get_lan_ip():
    """Finds the local network IP of the machine (e.g. 192.168.x.x or 172.16.x.x)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def clean_song_title(title):
    if not title:
        return ""
    cleaned = re.sub(r'\s*-\s*(?:[0-9]{4}\s*)?Remaster(?:ed)?(?:\s*[0-9]{4})?.*$', '', title, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*\((?:[0-9]{4}\s*)?Remaster(?:ed)?(?:\s*[0-9]{4})?\)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*-\s*Radio Edit.*$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*-\s*Live.*$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*-\s*Single Version.*$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*-\s*Original Mix.*$', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

def extract_playlist_id(url_or_uri):
    m = re.search(r'(?:playlist[/:]|embed/playlist/)([a-zA-Z0-9]+)', url_or_uri)
    if m:
        return m.group(1)
    return None

def normalize_for_match(s):
    if not s:
        return ''
    s = s.lower()
    s = re.sub(r'\(.*?\)|\[.*?\]', '', s)
    s = re.sub(r'\s*-\s*.*$', '', s)
    s = re.sub(r'\s+(?:feat|ft)\.?\s+.*$', '', s, flags=re.IGNORECASE)
    s = re.sub(r'[^a-z0-9äöüß]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def score_match(cand_t, cand_a, targ_t, targ_a):
    ct = normalize_for_match(cand_t)
    ca = normalize_for_match(cand_a)
    tt = normalize_for_match(targ_t)
    ta = normalize_for_match(targ_a)
    if not ct or not tt:
        return 0
    
    t_score = 0
    if ct == tt:
        t_score = 60
    elif ct in tt or tt in ct:
        t_score = 40
    else:
        words_t = [w for w in tt.split() if len(w) > 2]
        words_c = [w for w in ct.split() if len(w) > 2]
        matched = [w for w in words_t if w in words_c]
        if words_t and len(matched) / len(words_t) >= 0.5:
            t_score = 30
    if t_score == 0:
        return 0

    a_score = 0
    if ca == ta:
        a_score = 40
    elif ca in ta or ta in ca:
        a_score = 30
    else:
        words_a = [w for w in ta.split() if len(w) > 2]
        words_c = [w for w in ca.split() if len(w) > 2]
        matched = [w for w in words_a if w in words_c]
        if matched:
            a_score = 20
    if a_score == 0:
        return 0

    return t_score + a_score

def fetch_itunes_preview(artist, title):
    """Fetches a free 30s audio preview URL (.mp3/.m4a) from Deezer or Apple Music with strict validation."""
    clean_t = normalize_for_match(title)
    clean_a = normalize_for_match(artist)
    q = f"{clean_a} {clean_t}".strip()

    # 1. Deezer
    try:
        url = f"https://api.deezer.com/search?q={urllib.parse.quote(q)}&limit=10"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for item in data.get('data', []):
                prev = item.get('preview')
                if not prev:
                    continue
                score = score_match(item.get('title', ''), item.get('artist', {}).get('name', ''), title, artist)
                if score >= 50:
                    return prev
    except Exception:
        pass

    # 2. iTunes DE
    try:
        url = f"https://itunes.apple.com/search?term={urllib.parse.quote(q)}&entity=song&limit=10&country=DE"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for item in data.get('results', []):
                prev = item.get('previewUrl')
                if not prev:
                    continue
                score = score_match(item.get('trackName', ''), item.get('artistName', ''), title, artist)
                if score >= 50:
                    return prev
    except Exception:
        pass

    return None

def fetch_single_track_year(track_item, clean_titles=True):
    uri = track_item.get('uri', '')
    track_id = uri.split(':')[-1] if ':' in uri else uri
    track_url = f"https://open.spotify.com/track/{track_id}"
    raw_title = track_item.get('title', 'Unbekannter Song')
    artist = track_item.get('subtitle', 'Unbekannter Künstler')

    title = clean_song_title(raw_title) if clean_titles else raw_title
    year = 2000
    preview_url = None
    cover_url = None

    if track_id:
        embed_track_url = f"https://open.spotify.com/embed/track/{track_id}"
        req = urllib.request.Request(embed_track_url, headers=BROWSER_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
                if m:
                    data = json.loads(m.group(1))
                    entity = data.get('props', {}).get('pageProps', {}).get('state', {}).get('data', {}).get('entity', {})
                    rdate = entity.get('releaseDate', {}).get('isoString', '')
                    if rdate and len(rdate) >= 4:
                        try:
                            year = int(rdate[:4])
                        except ValueError:
                            pass
                    
                    # Direct Spotify audio preview
                    sp_audio = entity.get('audioPreview', {}).get('url')
                    if sp_audio:
                        preview_url = sp_audio

                    # Direct Spotify cover art
                    images = entity.get('visualIdentity', {}).get('image', [])
                    if images:
                        cover_url = images[-1].get('url')
        except Exception:
            pass

    # Fetch 30-sec preview URL if not already found in Spotify embed
    if not preview_url:
        preview_url = fetch_itunes_preview(artist, title)

    return {
        "id": track_id,
        "title": title,
        "artist": artist,
        "year": year,
        "url": track_url,
        "previewUrl": preview_url,
        "coverUrl": cover_url
    }

def fetch_spotify_playlist(playlist_id, clean_titles=True, require_preview=True):
    embed_url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
    req = urllib.request.Request(embed_url, headers=BROWSER_HEADERS)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        raise RuntimeError(f"Konnte Spotify Playlist nicht abrufen: {e}")

    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
    if not m:
        raise RuntimeError("Konnte Spotify Daten nicht parsen. Bitte prüfe den Link.")

    data = json.loads(m.group(1))
    entity = data.get('props', {}).get('pageProps', {}).get('state', {}).get('data', {}).get('entity', {})
    
    playlist_name = entity.get('name') or entity.get('title') or "Spotify Playlist"
    raw_tracks = entity.get('trackList', [])

    if not raw_tracks:
        raise RuntimeError("Die Playlist enthält keine Songs oder ist privat.")

    results = []
    skipped_count = 0
    # Moderate concurrency to prevent rate limits
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(fetch_single_track_year, t, clean_titles) for t in raw_tracks]
        for f in futures:
            try:
                res = f.result()
                if not res:
                    continue
                # FILTER: Only keep songs that have a verified working 30-sec audio preview!
                if require_preview and not res.get('previewUrl'):
                    skipped_count += 1
                    print(f"⚠️ Übersprungen (keine Audio-Vorschau): {res.get('artist')} - {res.get('title')}")
                    continue
                results.append(res)
            except Exception:
                pass

    return {
        "playlistName": playlist_name,
        "count": len(results),
        "skippedCount": skipped_count,
        "songs": results
    }

class HitsterHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. System Info (IP, Port, URL)
        if path == '/api/system-info':
            lan_ip = get_lan_ip()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({
                "lanIp": lan_ip,
                "port": PORT,
                "hostUrl": f"http://{lan_ip}:{PORT}"
            }).encode('utf-8'))
            return

        # 2. Track Info for single song
        if path == '/api/track-info':
            track_id = query.get('id', [''])[0]
            if not track_id:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Missing id parameter"}).encode('utf-8'))
                return

            try:
                item = {"uri": f"spotify:track:{track_id}", "title": "Unbekannt", "subtitle": "Unbekannt"}
                embed_track_url = f"https://open.spotify.com/embed/track/{track_id}"
                req = urllib.request.Request(embed_track_url, headers=BROWSER_HEADERS)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    html = resp.read().decode('utf-8', errors='ignore')
                    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
                    if m:
                        data = json.loads(m.group(1))
                        entity = data.get('props', {}).get('pageProps', {}).get('state', {}).get('data', {}).get('entity', {})
                        item["title"] = entity.get('name', 'Unbekannt')
                        artists = [a.get('name', '') for a in entity.get('artists', []) if a.get('name')]
                        item["subtitle"] = ', '.join(artists) if artists else 'Unbekannt'

                info = fetch_single_track_year(item, clean_titles=True)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, **info}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
            return

        # 3. Audio Preview Lookup
        if path == '/api/preview':
            artist = query.get('artist', [''])[0]
            title = query.get('title', [''])[0]
            preview = fetch_itunes_preview(artist, title)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "previewUrl": preview}).encode('utf-8'))
            return

        # 4. Mobile Blind Player Page
        if path == '/play':
            player_file = os.path.join(BASE_DIR, 'player.html')
            if os.path.exists(player_file):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                with open(player_file, 'rb') as f:
                    self.wfile.write(f.read())
                return

        # Default static file handler
        return super().do_GET()

    def do_POST(self):
        if self.path == '/api/playlist':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')

            try:
                payload = json.loads(post_data)
                url = payload.get('url', '').strip()
                clean = payload.get('cleanTitles', True)

                playlist_id = extract_playlist_id(url)
                if not playlist_id:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": "Ungültiger Spotify-Playlist-Link. Bitte einen Link wie https://open.spotify.com/playlist/... eingeben."
                    }, ensure_ascii=False).encode('utf-8'))
                    return

                data = fetch_spotify_playlist(playlist_id, clean_titles=clean)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    **data
                }, ensure_ascii=False).encode('utf-8'))

            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": str(e)
                }, ensure_ascii=False).encode('utf-8'))
            return

        if self.path == '/api/delete-deck':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            try:
                payload = json.loads(post_data)
                deck_id = str(payload.get('deckId', '')).strip().lower()
                idx_path = os.path.join(BASE_DIR, 'decks', 'index.json')
                if not os.path.exists(idx_path):
                    self.send_response(404)
                    self.end_headers()
                    return
                with open(idx_path, 'r', encoding='utf-8') as f:
                    idx = json.load(f)
                new_idx = []
                deleted_file = None
                for d in idx:
                    did = str(d.get('id', '')).lower()
                    dslug = str(d.get('slug', '')).lower()
                    dname = str(d.get('name', '')).lower()
                    if deck_id in [did, dslug, dname]:
                        fpath = os.path.join(BASE_DIR, d.get('file', ''))
                        if os.path.exists(fpath):
                            try:
                                os.remove(fpath)
                                deleted_file = fpath
                            except Exception:
                                pass
                    else:
                        new_idx.append(d)
                with open(idx_path, 'w', encoding='utf-8') as f:
                    json.dump(new_idx, f, ensure_ascii=False, indent=2)

                try:
                    import subprocess
                    subprocess.run(['git', 'add', '-A', 'decks/'], cwd=BASE_DIR, capture_output=True, timeout=10)
                    subprocess.run(['git', 'commit', '-m', f'Delete deck {deck_id}'], cwd=BASE_DIR, capture_output=True, timeout=10)
                    subprocess.run(['git', 'push', 'origin', 'main'], cwd=BASE_DIR, capture_output=True, timeout=15)
                except Exception:
                    pass

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "deleted": deleted_file, "remaining": len(new_idx)}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()

def run_server():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, HitsterHandler)
    lan_ip = get_lan_ip()
    local_url = f"http://localhost:{PORT}"
    network_url = f"http://{lan_ip}:{PORT}"
    print("======================================================")
    print("🎵 HITSTER STUDIO & BLIND-PLAYER")
    print(f"🖥️  Am PC öffnen:       {local_url}")
    print(f"📱 Am Smartphone öffnen: {network_url}")
    print("======================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer beendet.")

if __name__ == '__main__':
    run_server()
