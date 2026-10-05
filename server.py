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

def fetch_itunes_preview(artist, title):
    """Fetches a free 30s audio preview URL (.m4a) from Apple Music/iTunes search API."""
    try:
        clean_t = re.sub(r'\(.*?\)|\[.*?\]', '', title).strip()
        main_artist = artist.split(',')[0].split('&')[0].strip()
        query = urllib.parse.quote(f"{main_artist} {clean_t}".strip())
        url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            results = data.get('results', [])
            if results:
                return results[0].get('previewUrl')
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
        except Exception:
            pass

    # Fetch 30-sec preview URL
    preview_url = fetch_itunes_preview(artist, title)

    return {
        "id": track_id,
        "title": title,
        "artist": artist,
        "year": year,
        "url": track_url,
        "previewUrl": preview_url
    }

def fetch_spotify_playlist(playlist_id, clean_titles=True):
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
    # Moderate concurrency to prevent rate limits
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(fetch_single_track_year, t, clean_titles) for t in raw_tracks]
        for f in futures:
            try:
                results.append(f.result())
            except Exception:
                pass

    return {
        "playlistName": playlist_name,
        "count": len(results),
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
