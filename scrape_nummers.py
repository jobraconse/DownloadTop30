import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://www.hitnoteringen.be/hitlijsten/vrt-radio-2-top-30/"

begin_jaar = int(input("Voer het beginjaar in: "))
eind_jaar = int(input("Voer het eindjaar in: "))

nummers_bestand = "nummers.txt"

bestaande_nummers = set()
try:
    with open(nummers_bestand, "r", encoding="utf-8") as f:
        for regel in f:
            regel = regel.strip()
            if regel:
                bestaande_nummers.add(regel)
except FileNotFoundError:
    pass

for jaar in range(begin_jaar, eind_jaar + 1):
    start_week = 18 if jaar == 1970 else 1

    for week in range(start_week, 54):
        week_str = f"{week:02d}"
        url = f"{BASE_URL}{jaar}-{week_str}"

        try:
            response = requests.get(url)
            if response.status_code != 200:
                if week == 53:
                    print(f"Jaar {jaar} heeft maar {week - 1} weken.")
                break

            soup = BeautifulSoup(response.text, "html.parser")
            entries = soup.find_all("div", class_="chartentry")

            if not entries and week == 53:
                print(f"Jaar {jaar} heeft maar {week - 1} weken.")
                break

            for entry in entries:
                artiest_span = entry.find("span", class_="artiest")
                titel_span = entry.find("span", class_="titel")

                if artiest_span and titel_span:
                    artiest = artiest_span.get_text(strip=True)
                    titel = titel_span.get_text(strip=True)
                    nummer = f"{artiest} - {titel}"

                    if nummer not in bestaande_nummers:
                        bestaande_nummers.add(nummer)
                        with open(nummers_bestand, "a", encoding="utf-8") as f:
                            f.write(nummer + "\n")
                        print(f"Toegevoegd: {nummer}")

        except requests.RequestException as e:
            print(f"Fout bij ophalen {url}: {e}")
            break

        time.sleep(1)

print(f"\nTotaal aantal unieke nummers in {nummers_bestand}: {len(bestaande_nummers)}")
