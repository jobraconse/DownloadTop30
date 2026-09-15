import difflib
import os
import re
import unicodedata
import time
from pathlib import Path
from typing import Set, List, Optional, Tuple
import requests
from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL
from pydub import AudioSegment

# deno staat niet standaard in PATH — toevoegen voor yt-dlp EJS-challenge
_deno_bin = str(Path.home() / ".deno" / "bin")
if os.path.isdir(_deno_bin) and _deno_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _deno_bin + os.pathsep + os.environ.get("PATH", "")

def get_input(prompt: str) -> str:
    """Get user input from the console."""
    return input(prompt).strip()


def safe_filename(name: str) -> str:
    """Maak een naam veilig voor gebruik als bestandsnaam."""
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()


# YouTube-titelsuffixen die geen deel zijn van de songnaam
YT_NOISE_PATTERNS = [
    r'\s*\(official\s*(?:hd\s*)?(?:music\s*)?video\)$',
    r'\s*\(official\s*audio\)$',
    r'\s*\(official\s*(?:hd|4k|remaster(?:ed)?)?\s*video\)$',
    r'\s*\(official(?:ly)?\)$',
    r'\s*\((?:hd|hq|4k|audio|audio only|video|videoclip|radio edit|short mix|club mix|dance mix|extended mix|original)\)$',
    r'\s*\[(?:official\s*(?:music\s*)?video|audio|hd|hq)\]$',
    r'\s*official\s*(?:music\s*)?video$',
    r'\s*\|\s*.*$',
]

def strip_yt_noise(name: str) -> str:
    """Verwijder bekende YouTube-titelsuffixen uit een bestandsnaam."""
    for pat in YT_NOISE_PATTERNS:
        name = re.sub(pat, '', name, flags=re.IGNORECASE)
    return name.strip()


def normalize(s: str) -> str:
    """Normaliseer tekst: accenten eraf, enkel letters/cijfers, lowercase."""
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]', '', s.lower())


def best_hit_match(filename: str, hits: Set[str]) -> Optional[Tuple[str, float]]:
    """Vind de beste hit-matching voor een (gedownloade) bestandsnaam.

    Verwijder eerst YouTube-suffixen, dan fuzzy-matching
    (difflib ratio + bonus voor langste gedeelde substring).
    """
    base = normalize(strip_yt_noise(filename))
    if not base:
        return None
    best_hit: Optional[str] = None
    best_score = 0.0
    for hit in hits:
        hn = normalize(hit)
        if not hn:
            continue
        ratio = difflib.SequenceMatcher(None, base, hn).ratio()
        match = difflib.SequenceMatcher(None, base, hn).find_longest_match(
            0, len(base), 0, len(hn))
        score = ratio + (match.size / 100.0)
        if score > best_score:
            best_hit, best_score = hit, score
    if best_hit and best_score >= 0.55:
        return best_hit, best_score
    return None

# --- CONFIGURATION & INPUT ---
begin_jaar = int(get_input("Voer het beginjaar in: "))
eind_jaar = int(get_input("Voer het eindjaar in: "))

base_path = Path.home() / "Muziek" / "temp"
mp4_dir = base_path / "mp4"
# Using a cleaner directory naming convention
mp3_dir = base_path / f"mp3_{begin_jaar}"

# Create directories
mp4_dir.mkdir(parents=True, exist_ok=True)
mp3_dir.mkdir(parents=True, exist_ok=True)

all_hits: Set[str] = set()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# --- STEP 1: SCRAPING THE HIT LISTS ---
for jaar in range(begin_jaar, eind_jaar + 1):
    print(f"--- Verwerken van jaar {jaar} ---")
    year_dir = base_path / str(jaar)
    year_dir.mkdir(parents=True, exist_ok=True)
    hits_file_path = year_dir / "hitsongs.txt"

    # Adjust start week for older years (e.g., VRT Radio 2 logic)
    start_week = 18 if jaar < 1980 else 1
    
    for week in range(start_week, 53):
        week_str = f"{week:02d}"
        url = f"https://www.hitnoteringen.be/hitlijsten/vrt-radio-2-top-30/{jaar}-{week_str}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # We look for the list items that contain track info
                items = soup.find_all('li', class_='entry')
                
                current_year_hits: List[str] = []
                for item in items:
                    # Use the specific classes from your source code
                    artiest_span = item.find('span', class_='artiest')
                    titel_span = item.find('span', class_='titel')
                    
                    if artiest_span and titel_span:
                        artist = artiest_span.get_text(strip=True)
                        title = titel_span.get_text(strip=True)
                        
                        # Create the combined string for your hit list
                        entry = f"{artist} - {title}"
                        current_year_hits.append(entry)
                        all_hits.add(entry)
                
                # Save these hits to the weekly file (append mode)
                with open(hits_file_path, "a", encoding="utf-8") as f:
                    for entry in current_year_hits:
                        f.write(entry + "\n")
            else:
                print(f"Kon pagina niet laden voor {url} (Status: {response.status_code})")
        except Exception as e:
            print(f"Fout bij verwerken van {url}: {e}")

        
        time.sleep(1)


# Save all unique hits to final file (after all years are processed)
final_file = base_path / f"hits_jaren_{begin_jaar}_tm_{eind_jaar}.txt"
with open(final_file, "w", encoding="utf-8") as f:
    for hit in sorted(list(all_hits)):
        f.write(hit + "\n")

print(f"Unieke hits opgeslagen in {final_file}")


# --- STEP 2: DOWNLOAD FROM YOUTUBE ---
print("\nStarten met downloaden van YouTube...")
# YouTube vereist cookies + JS-runtime (deno) om niet geblokkeerd te worden.

for song in all_hits:
    if " - " not in song:
        continue
    artist_part, title_part = song.split(" - ", 1)
    search_query = f"{artist_part} {title_part}"

    # Eigen bestandsnaam (niet de YouTube-titel) zodat stap 3 altijd matcht
    safe_artist = safe_filename(artist_part)
    safe_title = safe_filename(title_part)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(mp4_dir / f"{safe_artist} - {safe_title}.%(ext)s"),
        'quiet': True,
        'no_warnings': True,
        # Haal cookies rechtstreeks uit Chromium (vers elke run)
        'cookiesfrombrowser': ('chromium',),
        # EJS challenge-solver downloaden van npm via deno
        'remote_components': ['ejs:npm'],
    }
    tel = 1
    # Retry voor wisselende YouTube-fouten (bv. "format not available")
    for attempt in range(3):
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"ytsearch1:{search_query}"])
            print(f"Downloaden van: {tel}. {artist_part} - {title_part}")
            tel += 1
            break
        except Exception as e:
            if attempt < 2:
                print(f"Poging {attempt + 1} mislukt voor '{song}', opnieuw proberen...")
                time.sleep(3)
            else:
                print(f"Download mislukt voor '{song}': {e}")
                break


# --- STEP 3: CONVERSION TO MP3 AND METADATA ---
print("\nStarten met conversie naar MP3...")

# Laad álle hits-jaargangen zodat ook oudere downloads gematcht worden
all_hit_sets: Set[str] = set(all_hits)
for hits_file in base_path.glob("hits_jaren_*.txt"):
    with open(hits_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if " - " in line:
                all_hit_sets.add(line)

audio_files = [p for ext in ("*.mp4", "*.webm", "*.m4a", "*.opus", "*.ogg", "*.flac")
               for p in mp4_dir.glob(ext)]

for audio_path in sorted(audio_files):
    try:
        match = best_hit_match(audio_path.stem, all_hit_sets)
        selected_hit = match[0] if match else None

        if selected_hit and " - " in selected_hit:
            artist_tag, title_tag = selected_hit.split(" - ", 1)
            # Clean filename for file system safety
            safe_title = safe_filename(title_tag)
            final_mp3_path = mp3_dir / f"{safe_filename(artist_tag)} - {safe_title}.mp3"

            # Convert and inject metadata (requires ffmpeg)
            audio = AudioSegment.from_file(str(audio_path))

            # Export to mp3 with metadata tags (pydub >0.24.0)
            audio.export(
                str(final_mp3_path),
                format="mp3",
                bitrate="192k",
                tags={
                    "title": title_tag,
                    "artist": artist_tag,
                    "album": f"Oldies {begin_jaar}",
                    "genre": "Pop",
                },
            )
            print(f"Succesvol geconverteerd: {final_mp3_path.name}")
            
            # Remove original file
            if audio_path.exists():
                os.remove(audio_path)
        else:
            print(f"Geen metadata gevonden voor {audio_path.name}, overgeslagen.")
    except Exception as e:
        print(f"Fout bij converteren van {audio_path}: {e}")

print("\n--- Proces voltooid! ---")
