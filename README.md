# Bedriftsdata fra Brønnøysundregisteret

Dette skriptet lar deg hente data om norske selskaper fra Brønnøysundregisteret basert på næringskoder. Du kan enkelt få ut kontaktinformasjon, stiftelsesdato, adresse og andre nyttige data for selskaper innen en bestemt næringskategori.

## Egenskaper

- Henter selskapsinformasjon basert på næringskode
- Lagrer data i CSV-format som lett kan åpnes i Excel eller andre regnearkprogrammer
- Inkluderer:
  - Selskapsnavn
  - Organisasjonsnummer
  - Stiftelsesdato
  - Registreringsdato i Enhetsregisteret
  - E-postadresse
  - Telefonnummer
  - Mobilnummer
  - Hjemmeside
  - Forretningsadresse
  - Antall ansatte

## Installasjon

### Forutsetninger: Installere Python

Skriptet krever Python 3.6 eller nyere. Hvis du ikke har Python installert, følg instruksjonene nedenfor:

#### Windows

1. Besøk [Python.org](https://www.python.org/downloads/windows/)
2. Last ned nyeste Python 3-versjon (f.eks. Python 3.11)
3. Kjør installasjonsfilen
4. **Viktig:** Huk av for "Add Python to PATH" under installasjonen
5. Velg "Install Now"

For å verifisere installasjonen, åpne Command Prompt og skriv:
```
python --version
```

#### macOS

**Alternativ 1: Homebrew (anbefalt)**
1. Installer [Homebrew](https://brew.sh/) hvis du ikke har det:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. Installer Python med Homebrew:
   ```bash
   brew install python
   ```

**Alternativ 2: Installer direkte**
1. Besøk [Python.org](https://www.python.org/downloads/macos/)
2. Last ned nyeste Python 3-versjon
3. Kjør installasjonsfilen

For å verifisere installasjonen, åpne Terminal og skriv:
```bash
python3 --version
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip
```

### Verifisere pip-installasjon

Pip er Python sin pakkebehandler og burde være installert sammen med Python.

**Windows:**
```bash
pip --version
```

**macOS/Linux:**
```bash
pip3 --version
```

Om pip ikke er installert eller trenger oppdatering:

**Windows:**
```bash
python -m ensurepip --upgrade
```

**macOS/Linux:**
```bash
python3 -m ensurepip --upgrade
```

### Installere prosjektet

#### Alternativ 1: Bruk requirements.txt (anbefalt)

1. Klon eller last ned dette repository til din maskin
2. Åpne terminalen/Command Prompt og naviger til mappen der du lastet ned filene
3. Kjør følgende kommando for å installere alle nødvendige pakker:

**Windows:**
```bash
pip install -r requirements.txt
```

**macOS/Linux:**
```bash
pip3 install -r requirements.txt
```

#### Alternativ 2: Manuell installasjon

Hvis du foretrekker å installere pakkene manuelt:

**Windows:**
```bash
pip install requests
```

**macOS/Linux:**
```bash
pip3 install requests
```

#### Anbefalt: Bruk et virtuelt miljø

Det er god praksis å bruke et virtuelt miljø for Python-prosjekter:

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## Bruk

Du kan kjøre skriptet fra kommandolinjen med ulike parametere:

**Windows:**
```bash
python main.py --naeringskode 73.11 --output reklamebyraaer.csv
```

**macOS/Linux:**
```bash
python3 main.py --naeringskode 73.11 --output reklamebyraaer.csv
```

### Parametere

- `--naeringskode` eller `-n`: Næringskode for selskaper som skal hentes (f.eks. 73.11 for reklamebyrå)
- `--output` eller `-o`: Navn på output CSV-fil. Standard er [næringskode]_selskaper.csv

### Eksempler

Hente reklamebyrå (standard):
```bash
python3 main.py
```

Hente regnskapskontor (næringskode 69.201):
```bash
python3 main.py --naeringskode 69.201 --output regnskapsbyra.csv
```

Hente dataprogrammering (næringskode 62.01):
```bash
python3 main.py -n 62.01 -o itselskaper.csv
```

## Vanlige næringskoder

Her er noen populære næringskoder du kan bruke:

| Kode | Beskrivelse |
|------|-------------|
| 73.11 | Reklamebyrå |
| 62.01 | Programmeringstjenester |
| 70.22 | Bedriftsrådgivning |
| 69.201 | Regnskap og bokføring |
| 56.101 | Restaurantvirksomhet |
| 86.221 | Spesialisert legetjeneste |
| 43.221 | Rørleggerarbeid |
| 71.112 | Arkitekttjenester |
| 85.601 | Pedagogisk rådgivning |
| 96.02 | Frisering og skjønnhetspleie |

Du kan finne flere næringskoder på [Brønnøysundregisteret](https://www.brreg.no) eller [SSB](https://www.ssb.no/klass/klassifikasjoner/6).

## Tips for bruk av dataene

1. Åpne CSV-filen i Excel eller et annet regnearkprogram
2. Du kan sortere dataene etter stiftelsesdato for å finne nye selskaper
3. For å finne selskaper i et bestemt område kan du filtrere på postnummer i adressefeltet
4. Bruk "Datafiltrering" i Excel for å enkelt filtrere etter selskaper med e-post, telefon eller hjemmeside

## Feilsøking

- Hvis du får feilmeldinger knyttet til API-et, sjekk om formatet på næringskoden er riktig (bruk punktum, f.eks. "62.01" ikke "6201")
- Hvis skriptet kjører men ingen resultater returneres, sjekk at næringskoden eksisterer
- Ved problemer med installasjon, sørg for at du har Python 3.6 eller nyere installert og at pip er oppdatert
- På Mac kan det hende du må bruke `python3` og `pip3` i stedet for `python` og `pip`
- Hvis du får "command not found" for python/pip, må du sørge for at Python er lagt til i PATH-miljøvariabelen

### Vanlige installasjonsutfordringer

**Windows:**
- "Python er ikke gjenkjent som en intern kommando": Reinstaller Python og sørg for å krysse av for "Add Python to PATH"
- Problemer med administratorrettigheter: Kjør Command Prompt som administrator

**macOS:**
- "Command not found: pip": Bruk `pip3` i stedet for `pip`
- Problemer med rettigheter: Prøv å legge til `sudo` foran pip-kommandoer

## Teknisk informasjon

- API-et som benyttes er Brønnøysundregisterets åpne API for Enhetsregisteret
- Skriptet respekterer API-ets begrensninger ved å gjøre maksimalt 60 kall per minutt
- Det hentes 1000 enheter per side (maksimalt tillatt av API-et)

## Lisens

Dette prosjektet er fritt tilgjengelig under MIT-lisensen. Du kan bruke det fritt, men det kommer uten garantier.

## Ansvarsfraskrivelse

Dette skriptet er laget for å forenkle tilgang til offentlig tilgjengelige data. Bruken av data du henter må følge GDPR og annen relevant lovgivning om personvern. 