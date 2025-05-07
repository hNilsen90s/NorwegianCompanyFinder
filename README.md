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
  - Postnummer (zipcode)
  - Kommune (state)
  - Gateadresse (street)
  - Under avvikling (in_liquidation)
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
- `--fields` eller `-f`: Kommaseparert liste (på engelsk) over felter som skal inkluderes i CSV-filen. Tilgjengelige felter: `name`, `orgnr`, `incorporation_date`, `registration_date`, `email`, `phone`, `mobile`, `website`, `address`, `zipcode`, `state`, `street`, `in_liquidation`, `employees`. Standard er alle felter.
- `--limit` eller `-l`: Maksimalt antall selskaper som skal lastes ned (standard: ingen grense)
- `--filter`: **Avansert:** Filteruttrykk for å kun inkludere selskaper som matcher bestemte kriterier. Se eksempler og forklaring under.

### Fleksibelt filter med --filter

Med flagget `--filter` kan du velge nøyaktig hvilke selskaper som skal inkluderes i CSV-filen basert på feltverdier. Du kan bruke logiske uttrykk (and, or, not), sammenligninger og parenteser.

**Tilgjengelige feltnavn:**
- name
- orgnr
- incorporation_date
- registration_date
- email
- phone
- mobile
- website
- address
- zipcode
- state
- street
- in_liquidation
- employees

**Slik fungerer det:**
- Feltnavn uten sammenligning (f.eks. `email`) betyr "feltet er ikke tomt".
- Du kan bruke `and`, `or`, `not` og parenteser.
- For å sjekke eksakt verdi, bruk `==` eller `!=` (f.eks. `email == "ok@test.com"`).
- For å sjekke tall, kan du bruke `>`, `<`, `>=`, `<=` på f.eks. `employees`.
- For å sjekke om et felt er tomt, bruk `not` foran feltnavnet (f.eks. `not phone`).
- For å sammenligne eksakt verdi, bruk understrek: `_email == "ok@test.com"` (avansert, se under).
- **For dato-feltene `incorporation_date` og `registration_date` kan du bruke sammenligningsoperatorer mot dato-strenger på formatet `yyyy-mm-dd` (f.eks. `registration_date > '2012-12-12'`).**

**Eksempler på bruk:**

- Kun selskaper med e-post og telefonnummer:
  ```bash
  python3 main.py --filter "email and phone"
  ```
- Kun selskaper med nettside:
  ```bash
  python3 main.py --filter "website"
  ```
- Kun selskaper med mobilnummer:
  ```bash
  python3 main.py --filter "mobile"
  ```
- Kun selskaper med e-post, men ikke telefon:
  ```bash
  python3 main.py --filter "email and not phone"
  ```
- Kun selskaper med ansatte (ansatte-feltet ikke tomt eller null):
  ```bash
  python3 main.py --filter "employees"
  ```
- Kun selskaper hvor e-post er nøyaktig "ok@test.com":
  ```bash
  python3 main.py --filter "email == 'ok@test.com'"
  ```
- Kun selskaper stiftet etter 2004:
  ```bash
  python3 main.py --filter "incorporation_date > '2004-01-01'"
  ```
- Kun selskaper registrert etter 2012-12-12:
  ```bash
  python3 main.py --filter "registration_date > '2012-12-12'"
  ```
- Kombinere dato med andre filter:
  ```bash
  python3 main.py --filter "email and incorporation_date > '2012-12-12'"
  ```
- Kombinere flere dato-krav:
  ```bash
  python3 main.py --filter "incorporation_date > '2004-01-01' and registration_date > '2012-12-12'"
  ```

**Tips:**
- Du kan kombinere flere kriterier med `and`, `or` og parenteser.
- Alle feltnavn må skrives på engelsk (se listen over).
- For eksakt sammenligning av tekst, bruk `==` eller `!=`.
- For å sammenligne tall (f.eks. ansatte): `employees > 10`
- For å sammenligne eksakt verdi på et felt, bruk understrek: `_email == 'ok@test.com'` (avansert, gir tilgang til råverdien uten boolsk tolkning).

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

Hente kun 100 selskaper med alle felter:
```bash
python3 main.py --naeringskode 73.11 --limit 100 --output reklamebyra.csv
```

Hente kun navn, organisasjonsnummer, e-post og nettside for reklamebyrå:
```bash
python3 main.py --fields "name,orgnr,email,website" --naeringskode 73.11 --output test_companies.csv
```

**Filtrere selskaper med filter:**

- Kun selskaper med e-post og telefonnummer:
  ```bash
  python3 main.py --filter "email and phone"
  ```
- Kun selskaper med nettside:
  ```bash
  python3 main.py --filter "website"
  ```
- Kun selskaper med e-post, men ikke telefon, og ansatte, og e-post er "ok@test.com":
  ```bash
  python3 main.py --filter "email and not phone and employees and email == 'ok@test.com'"
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

## Endringslogg

- Lagt til `--fields`/`-f` flagg slik at brukere kan velge hvilke kolonner som skal inkluderes i CSV-filen.
- Alle feltnavn og kolonneoverskrifter i CSV er nå kun på engelsk (ingen norske spesialtegn i output eller argumenter).
- Lagt til nye felter: `zipcode`, `state`, `street`, `in_liquidation` (hentes fra API).
- Lagt til `--limit`/`-l` flagg for å begrense antall selskaper som lastes ned.
- Lagt til `--filter` flagg for fleksibelt og avansert filtrering av selskaper direkte fra kommandolinjen. 