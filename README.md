# 🎵 Hitster Studio & Mobile App

Eine moderne, web-basierte Hitster-App im minimalistischen Apple-Design zur Generierung von Karten aus Spotify-Playlists, A4-Duplex-Druck und einem **vollwertigen, spoilerfreien mobilen Kamera-Scanner**.

👉 **Live auf GitHub Pages:** [kritiker-jack.github.io/hitster](https://kritiker-jack.github.io/hitster/)

---

## 📱 Mobile Scanner App (Wie die originale Hitster-App)

* **Direkt im Browser öffnen:** Rufe auf dem Smartphone einfach [kritiker-jack.github.io/hitster](https://kritiker-jack.github.io/hitster/) auf und tippe auf **„📱 Scanner“** (oder direkt `#scanner`).
* **Apple Dropdown-Menü:** Oben rechts über das moderne Klappmenü (**☰ Menü**) kann jederzeit schnell zwischen Scanner, Song-Editor, 3D-Karten und Druckbogen gewechselt werden.
* **Vollbild-App-Modus:** Der Rest der Webseite wird komplett ausgeblendet. Oben links gibt es einen dezenten Zurück-Pfeil (‹ Studio), um wieder zur Übersicht zu gelangen.
* **Laser-Scanner & Animationen:** 
  * Animierter Sucher-Rahmen mit Laser-Scanlinie und Apple-typischem Frosted-Glass-Design.
  * Beim Erkennen einer Karte ertönt ein angenehmer 2-Ton-Gong mit Haptik-Feedback (Vibration).
  * **Kamera schaltet sofort ab:** Sobald eine Karte erfasst ist, schaltet die Kamera-Hardware komplett ab (keine störende Kamera mehr im Hintergrund!).
* **100 % Spoilerfreier Blind-Player:**
  * Eine rotierende Vinyl-Schallplatte und Equalizer-Wellen visualisieren die Wiedergabe.
  * Robuster Client-Side Audio-Resolver (30s-Vorschau ohne Backend, direkt im Browser).
  * **Absolut spoilerfrei:** Kein Songname, kein Künstler, kein Albumcover während des Ratens!
  * 30-Sekunden-Countdown läuft herunter mit Pause/Play/Restart-Steuerung.
* **Lösung aufdecken:**
  * Erst wenn alle geraten haben, tippt man auf **„👁️ Lösung aufdecken“**.
  * Das **große HD-Albumcover (Titelbild)** wird eingeblendet, gemeinsam mit dem **Erscheinungsjahr** in riesiger goldener Typografie sowie Songtitel und Interpret.
  * Ein Tipp auf **„Nächste Karte scannen“** schließt die Ansicht und die Kamera ist sofort wieder bereit für die nächste Runde.

---

## ☁️ Karten & Decks direkt online erstellen (Ohne PC & ohne .bat)

Du musst **keine .bat-Datei** mehr am PC starten, um neue Decks zu erstellen! Es gibt 3 einfache Wege direkt im Browser:

### 1. 🚀 Über GitHub Actions (Automatisch aus Spotify-Playlist)
1. Öffne auf deinem Smartphone oder PC die [GitHub Actions in deinem Repo](https://github.com/kritiker-jack/hitster/actions/workflows/import_deck.yml).
2. Tippe rechts auf **„Run workflow“**.
3. Füge deinen **Spotify Playlist-Link** ein (optional einen Deck-Namen vergeben) und klicke auf den grünen Button.
4. GitHub lädt die Songs & Erscheinungsjahre in der Cloud herunter und speichert sie direkt im Repository.
5. Nach ca. 30–45 Sekunden erscheint dein neues Kartendeck auf der Website im Dropdown **„Decks aus dem Repository laden“**!

### 2. 📂 Fertige Decks direkt aus dem Git-Repository laden
* Auf [kritiker-jack.github.io/hitster](https://kritiker-jack.github.io/hitster/) findest du im Editor ganz oben das Menü **„Karten-Decks aus dem Repository laden“**.
* Wähle einfach ein vorkonfiguriertes Deck (z. B. *18 Welthits* oder *Deutsche Hits*) aus und tippe auf **Deck laden**.

### 3. 📝 Text-Massenimport (Direkt im Browser)
* Klappe im Editor **„📝 Songliste als Text einfügen“** auf.
* Kopiere einfach Songs zeilenweise hinein (`Songtitel - Interpret - Jahr`) und klicke auf **Importieren**.

---

## 🖨️ Karten drucken & überallhin mitnehmen

1. Öffne das Studio im Browser oder am PC.
2. Wähle dein gewünschtes Deck aus (oder importiere neue Songs).
3. Als QR-Code-Ziel ist standardmäßig **🌐 GitHub Pages** aktiv.
4. Drucke die Karten über den Tab **„🖨️ A4 Druck“** beidseitig aus (*„An langer Kante spiegeln“*).
5. **Der Vorteil:** Jeder QR-Code verlinkt direkt auf deine Online-App. Du kannst die Karten überallhin mitnehmen (zu Freunden, auf Partys, in den Urlaub) – **es ist kein PC und kein lokales WLAN nötig!**

---

## 🎨 Design & Features

* **Apple Minimalist UI:** Glassmorphism, Tiefenschärfe-Blur (`backdrop-filter`), geschmeidige Kurven und intuitive Segmented Controls.
* **Intelligente Titelbereinigung:** Entfernt störende Zusätze wie ` - 2011 Remaster`, ` - Radio Edit` oder `(Live)` aus den Titeln, damit keine Jahreszahlen verraten werden.
* **🃏 3D-Karten-Vorschau:** Interaktive Karten zum Umdrehen per Klick.
* **100 % Web-Standard:** Keine App-Installation aus dem App Store nötig – läuft direkt in Safari (iOS) und Chrome (Android).
