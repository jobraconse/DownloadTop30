import os
import re
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from yt_dlp import YoutubeDL
from pydub import AudioSegment

def get_input(prompt):
    return input(prompt)

# Gebruikersinput
begin_jaar = int(get_input("Voer het beginjaar in: "))
eind_jaar = int(get_input("Voer het eindjaar in: "))

base_path = Path.home() / "Muziek"
mp4_dir = base_path / "mp4"
mp3_dir = base_path / f"mp3_{begin_jaar}"

# Maak mappen aan
mp4_dir.mkdir(parents=True, exist_ok=True)
mp3_dir.mkdir(parents=True, exist_ok=True)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install))

all_hits = set() # Gebruik een set om dubbelen direct te voorkomen

for jaar in range(begin_jaar,eind_jaar + 1):
    print(f"--- Verwerken van jaar {jaar} ---")
    year_dir = base_path / str(jaar)
    year_dir.mkdir(parents=True, exist_ok=True)
    hits_file_path = year_dir / "hitsongs.txt"
    
    # Bepaal start week
    start_week = 18 if jaar == 1970 else 1
    
    for week in range(start_week, 53):
        # Formatteer week naar 2 cijven (bijv. 01)
        week_str = f"{week:02d}"
        url = f"https://www.hitnoteringen.be/hitlijsten/vrt-radio-2-top-30/{jaar}-week{week_str}"
        
        driver.get(url)
        time.sleep(3) # Wacht even op laden
        
        # Zoek de hits (selecteer elementen onder 'Volledige lijst')
        # Let op: De exacte selector hangt af van de HTML structuur van de site
        elements = driver.find_elements(By.CSS_SELECTOR, "div.hit-list-item") # Voorbeeld selector
        
        current_year_hits = []
        for el in elements:
            try:
                # Bijv. artist is vetgedrukt (strong) en titel staat daaronder
                artist = el.find_element(By.TAG_NAME, "strong").text.strip()
                title = el.find_element(By.XPATH, "./following-sibling::div").text.strip() # Voorbeeld
                song_entry = f"{artist} - {title}"
                current_year_hits.append(song_entry)
            except:
                continue

        # Sla op in de map van het jaar
        with open(hits_file_path, "w", encoding="utf-8") as f:
            for entry in current_year_hits:
                f.write(entry + "\n")
                all_hits.add(entry) # Voeg toe aan globale set (geen dubbelen)

    driver.quit()

# Combineer alle unieke hits naar één bestand
final_file = base_path / f"hits_jaren_{begin_jaar}.txt"
with open(final_file, "w", encoding="utf-8") as f:
    for hit in sorted(list(all_hits)):
        f.write(hit + "\n")

print(f"Alle unieke hits opgeslagen in {final_file}")

# YouTube Downloads en Conversie naar MP3
print("Starten met downloaden van YouTube (mp4)...")
for song in all_hits:
    artist_part, title_part = song.split(" - ", 1)
    search_query = f"{artist_part} {title_part}"
    
    # Gebruik yt-dlp voor de download (minder bot-detectie dan pure selenium voor video)
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[m4a]/best[ext=mp4]/best',
        'outtmpl': str(mp4_dir / '%(title)s.%(ext)s'),
    }
    
    with YoutubeDL(ydl_opts) as ydl:
        # Zoek en download (vereist een zoekquery logica of directe URL)
        # Voor eenvoud aanpassing naar simpele search via yt-dlp:
        ydl.download([f"ytsearch1:{search_query}"])

    # Conversie naar MP3 met ID3 tags
    # Zoek het bestand in de mp4 map (omdat namen kunnen variëren)
    mp4_files = list(mp4_dir.glob("*.mp4"))
    for mp4_path in mp4_files:
        # Sla mp3 op in mp3_folder met juiste naam en tags
        target_name = f"{artist_part} - {title_part}".replace("/", "-") # Vervang slashes voor bestandnaam
        final_mp3_path = mp3_dir / f"{target_name}.mp3"
        
        # Conversie proces
        audio = AudioSegment.from_file(str(mp4_path))
        audio.metadata.title = f"{artist_part} - {title_part}"
        audio.metadata.artist = artist_part
        audio.metadata.album = f"Oldies but goldies + {begin_jaar}"
        audio.metadata.genre = "pop"
        
        audio.export(str(final_mp3_path), format="mp3")
        
        # Verwijder het originele mp4 bestand na conversie
        os.remove(mp4_path)

print("Klaar!")

