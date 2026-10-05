# 🎵 Hitster Studio & Spoilerfreier Blind-Player

Ein web-basiertes Tool zur automatischen Generierung von Hitster-Karten aus Spotify-Playlists mit QR-Codes, Erscheinungsjahr, Songtitel, Künstler, A4 Duplex-Druck und einem **100% spoilerfreien Blind-Player**.

---

## 🚀 Schnellstart

1. Starte die Datei **`start.bat`** per Doppelklick (oder führe `python server.py` aus).
2. Der Browser öffnet sich automatisch unter: `http://localhost:5055`
3. Füge den Link deiner Spotify-Playlist ein und klicke auf **„⚡ Playlist importieren“**!

---

## 🛡️ Wie das Problem mit dem Spotify-Spoiler gelöst wird

Wenn du einen normalen Spotify-Link mit dem Smartphone scannst, öffnet sich sofort die offizielle Spotify-App und zeigt Songtitel, Interpret und Albumcover groß auf dem Display an. Das ruiniert das Spiel, bevor der Song überhaupt angespielt wurde.

**Hitster Studio bietet dir zwei geniale Lösungen, um das zu umgehen:**

### Lösung 1: Der spoilerfreie Web-Player (Für die normale Handy-Kamera)
* In Hitster Studio ist standardmäßig **„Hitster Blind-Player (Empfohlen)“** als QR-Code-Ziel aktiviert.
* Wenn deine Mitspieler den gedruckten QR-Code mit ihrer **normalen Smartphone-Kamera** scannen, öffnet sich **nicht Spotify**, sondern direkt die neutrale Hitster-Player-Webseite im Safari/Chrome-Browser!
* **Auf dem Display:** Eine coole, rotierende Vinyl-Schallplatte und ein großer Play-Button. **Kein Songname, kein Künstler, kein Cover!**
* Die 30-Sekunden-Vorschau wird sofort abgespielt und ein Timer läuft herunter.
* Erst wenn alle geraten haben, tippt man auf **„👁️ Lösung aufdecken“**, und das Jahr, der Titel und der Interpret werden animiert enthüllt!

### Lösung 2: Der integrierte Live-Scanner & Buzzer (Web-App)
* Klicke oben rechts auf **„📲 Am Handy öffnen“** und scanne den Verbindungs-QR-Code einmalig mit deinem Smartphone.
* Auf dem Handy öffnet sich das Hitster Studio.
* Gehe auf den Tab **„📱 Spiel-Scanner & Buzzer“**:
  * Die Kamera deines Handys aktiviert sich.
  * Halte eine beliebige Hitster-Karte vor die Kamera.
  * Bei Erkennung ertönt ein Signal-Ton (*Beep!*), die Musik startet sofort spoilerfrei, und der Countdown läuft!
  * Nach der Runde tippt man auf *„Lösung aufdecken“* und anschließend auf *„Nächste Karte scannen“* – perfekt für einen flüssigen Spielabend!

---

## ✨ Features im Überblick

1. **Kein Login & keine API-Schlüssel nötig:**
   * Einfach den öffentlichen Spotify-Playlist-Link reinkopieren.
   * Titel, Künstler, Spotify-Link, Erscheinungsjahr und 30s-Audio-Previews werden vollautomatisch ermittelt.

2. **100% Spoilerfrei:**
   * Wähle zwischen dem lokalen Blind-Player (kein Öffnen von Spotify) und Spotify-Direktlinks.

3. **Intelligente Titelbereinigung:**
   * Entfernt automatisch störende Zusätze wie ` - 2011 Remaster`, ` - Radio Edit` oder `(Live)` aus den Songtiteln, damit Jahreszahlen und Spoiler nicht vorab verraten werden.

4. **🃏 3D Karten-Vorschau:**
   * Interaktive 3D-Karten, die sich per Klick umdrehen lassen (Vorderseite: QR-Code; Rückseite: Jahr im Großformat, Titel & Künstler).

5. **🖨️ Perfekter A4 Duplex-Druck (Beidseitig):**
   * 9 Karten pro A4-Bogen (3x3 Raster, ca. 60 x 86 mm).
   * Automatische horizontale Spiegelung der Rückseite, damit beim doppelseitigen Druck (*„An langer Kante spiegeln“*) Vorderseite (QR-Code) und Rückseite (Auflösung) passgenau aufeinanderliegen.
