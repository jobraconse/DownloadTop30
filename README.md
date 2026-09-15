# top30_download.py

Script dat automatisch de VRT Radio 2 Top 30 hits per week van hitnoteringen.be scrape, de bijhorende muziek van YouTube downloadt, en omzet naar MP3 met correcte metadata.

## Hoe het werkt

1. **Scrapen** — Haalt per jaar/week de hitlijst op van `hitnoteringen.be`
2. **Downloaden** — Zoekt elk nummer op YouTube via `ytsearch1` en downloadt de audio
3. **Converteren** — Zet de audio om naar MP3 (192k) en voegt metadata toe (artiest, titel, album, genre)

## Vereisten

### Systeem

- **Python 3.9+**
- **ffmpeg** (voor audioconversie via pydub en yt-dlp)
- Een browser waarin je **ingelogd bent op YouTube** (zie stap 5)
- **Deno** (JS-runtime, nodig om YouTube's bot-bescherming te omzeilen)

Werkt op **Windows**, **macOS** en **Linux**.

### Pakketten installeren

#### 1. ffmpeg

<details>
<summary><b>Windows</b></summary>

```powershell
winget install ffmpeg
```

Of via [Chocolatey](https://chocolatey.org/):

```powershell
choco install ffmpeg
```

Na installatie het juiste `.exe`-pad toevoegen aan `PATH`, óf het script
uitvoeren met het volledige pad. Controleer of ffmpeg gevonden wordt:

```powershell
ffmpeg -version
```

Als dit een fout geeft, is ffmpeg nog niet aan PATH toegevoegd — herstart
dan eerst je terminal (of herstart je pc na installatie).
</details>

<details>
<summary><b>macOS</b></summary>

Je hebt hiervoor [Homebrew](https://brew.sh/) nodig:

```bash
brew install ffmpeg
```
</details>

<details>
<summary><b>Linux</b></summary>

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# Fedora
sudo dnf install ffmpeg

# Arch
sudo pacman -S ffmpeg
```

Controleer altijd of ffmpeg gevonden wordt: `ffmpeg -version`
</details>

#### 2. Python-virtual environment aanmaken

<details>
<summary><b>Windows</b></summary>

Installeer eerst Python van [python.org](https://www.python.org/downloads/)
(≥ 3.9 en vink **"Add Python to PATH"** aan tijdens de installatie).

```powershell
cd C:\pad\naar\dit\script
python -m venv .venv
.venv\Scripts\activate
```
</details>

<details>
<summary><b>macOS</b></summary>

Installeer Python via Homebrew (of gebruik de installatie van python.org):

```bash
brew install python
cd /pad/naar/dit/script
python3 -m venv .venv
source .venv/bin/activate
```
</details>

<details>
<summary><b>Linux</b></summary>

```bash
cd /pad/naar/dit/script
python3 -m venv .venv
source .venv/bin/activate
```
</details>

#### 3. Python-pakketten

```bash
pip install requests beautifulsoup4 pydub yt-dlp
```

> Alleen op **Linux** voeg je ook `secretstorage` toe:
> `pip install secretstorage`
>
> Dat pakket is nodig om de versleutelde Chromium-cookies uit te lezen via libsecret.
> Op **Windows en macOS** is het niet nodig (daar kan yt-dlp de browser-sleutels
> rechtstreeks ontsleutelen).

#### 4. Deno (JS-runtime voor yt-dlp)

<details>
<summary><b>Windows</b></summary>

Installeer via PowerShell:

```powershell
irm https://deno.land/install.ps1 | iex
```

Deno wordt geïnstalleerd naar `%USERPROFILE%\.deno\bin\deno.exe`.
Herstart je terminal zodat dit aan `PATH` toegevoegd wordt.
</details>

<details>
<summary><b>macOS</b></summary>

```bash
brew install deno
```

of via het officiële installatiescript:

```bash
curl -fsSL https://deno.land/install.sh | sh
```
</details>

<details>
<summary><b>Linux</b></summary>

```bash
curl -fsSL https://deno.land/install.sh | sh
```

Na installatie staat `deno` in `~/.deno/bin/deno`. Het script voegt deze map
automatisch toe aan `PATH`, dus verdere configuratie is niet nodig.
</details>

#### 5. Browser met YouTube-sessie

yt-dlp haalt cookies rechtstreeks uit je browser om YouTube's bot-bescherming
te omzeilen. Je moet dus **ingelogd zijn op YouTube** in die browser.

Open de browser, ga naar [youtube.com](https://www.youtube.com) en log in met
je Google-account.

> **Belangrijk:** de browser moet **volledig gesloten** zijn op het moment dat
> het script draait, anders kan yt-dlp het cookiebestand niet uitlezen.

## Gebruik

<details>
<summary><b>Windows</b></summary>

```powershell
cd C:\pad\naar\dit\script
.venv\Scripts\activate
python top30_download.py
```
</details>

<details>
<summary><b>macOS / Linux</b></summary>

```bash
cd /pad/naar/dit/script
source .venv/bin/activate
python3 top30_download.py
```
</details>

Het script vraagt om een **begin- en eindjaar**, bijvoorbeeld `1995` en `1995`
voor één jaar, of `1990` en `2000` voor een bereik.

## Bestandsstructuur na uitvoering

Alle bestanden komen in `~/Muziek/temp/` (dat is op Windows
`C:\Users\{gebruikersnaam}\Muziek\temp`):

```
Muziek/temp/
├── mp4/                          # Tussenliggende downloads (webm/m4a)
│   └── Artiest - Titel.webm
├── mp3_{begin_jaar}/             # Geconverteerde MP3's met metadata
│   ├── Artiest - Titel.mp3
│   └── ...
├── {jaar}/                       # Hitlijsten per jaar
│   └── hitsongs.txt
├── hits_jaren_{van}_tm_{tot}.txt # Unieke hits over alle jaren
└── cookies.txt                   # Cookies (indien handmatig geëxporteerd)
```

## Probleemoplossing

### "The page needs to be reloaded"

YouTube blokkeert de download. Controleer:
- Is **deno** geïnstalleerd? (`deno --version`)
- Is de browser **gesloten**?
- Zit je **ingelogd** op YouTube in de browser?

### "Requested format is not available"

Het script herhaalt automatisch mislukte downloads (max. 3 pogingen met 3
seconden vertraging). Meestal verdwijnt deze fout bij een tweede poging.

### Cookie-fout / "Sign in to confirm you're not a bot"

- Open de browser en log (opnieuw) in op YouTube
- Sluit de browser volledig
- Start het script opnieuw

### Fout: `secretstorage not available` (alleen Linux)

Op Linux is het pakket `secretstorage` nodig om de versleutelde Chromium-cookies
uit te lezen:

```bash
pip install secretstorage
```

### Andere browser dan Chromium

In het script staat `'cookiesfrombrowser': ('chromium',)`. Als je een andere
browser gebruikt, wijzig dit naar een van:
- `('firefox',)`
- `('chrome',)` (Google Chrome)
- `('brave',)`
- `('edge',)` (Microsoft Edge)

> Tip: op macOS kun je ook `('safari',)` gebruiken. Op Windows is `('edge',)`
> een prima keuze omdat Edge standaard geïnstalleerd is.

### `mp3_dir` is hardcoded naar `Muziek/temp`

Wil je een andere map, wijzig regel 83 in het script:

```python
base_path = Path.home() / "Muziek" / "temp"  # hier aanpassen
```
