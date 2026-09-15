import time
from pathlib import Path
from yt_dlp import YoutubeDL

nummers_bestand = Path("nummers.txt")
urls_bestand = Path("yt-urls.txt")

nummers = [regel.strip() for regel in nummers_bestand.read_text(encoding="utf-8").splitlines() if regel.strip()]

bestaand = set()
if urls_bestand.exists():
    for regel in urls_bestand.read_text(encoding="utf-8").splitlines():
        if " | " in regel:
            bestaand.add(regel.split(" | ")[0].strip())

opts = {
    "quiet": True,
    "skip_download": True,
    "noplaylist": True,
    "extract_flat": True,
}

with YoutubeDL(opts) as ydl:
    for nummer in nummers:
        if nummer in bestaand:
            continue

        try:
            info = ydl.extract_info(f"ytsearch1:{nummer}", download=False)
            video = info["entries"][0]
            url = video.get("url") or f"https://www.youtube.com/watch?v={video['id']}"
        except Exception as e:
            print(f"Geen URL gevonden voor: {nummer} ({e})")
            time.sleep(1)
            continue

        regel = f"{nummer} | {url}"
        bestaand.add(nummer)
        with open(urls_bestand, "a", encoding="utf-8") as f:
            f.write(regel + "\n")
        print(f"Toegevoegd: {regel}")

        time.sleep(0.5)

print(f"\nTotaal aantal URLs in {urls_bestand}: {len(bestaand)}")