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

Skriptet krever Python 3.6 eller nyere, og det eneste eksterne biblioteket som benyttes er `requests`.

### Alternativ 1: Bruk requirements.txt (anbefalt)

1. Klon eller last ned dette repository til din maskin
2. Åpne terminalen og naviger til mappen der du lastet ned filene
3. Kjør følgende kommando for å installere alle nødvendige pakker:

**Windows:**
```bash
pip install -r requirements.txt
```

**macOS/Linux:**
```bash
pip3 install -r requirements.txt
```

### Alternativ 2: Manuell installasjon

Hvis du foretrekker å installere pakkene manuelt:

**Windows:**
```bash
pip install requests
```

**macOS/Linux:**
```bash
pip3 install requests
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

## Teknisk informasjon

- API-et som benyttes er Brønnøysundregisterets åpne API for Enhetsregisteret
- Skriptet respekterer API-ets begrensninger ved å gjøre maksimalt 60 kall per minutt
- Det hentes 1000 enheter per side (maksimalt tillatt av API-et)

## Lisens

Dette prosjektet er fritt tilgjengelig under MIT-lisensen. Du kan bruke det fritt, men det kommer uten garantier.

## Ansvarsfraskrivelse

Dette skriptet er laget for å forenkle tilgang til offentlig tilgjengelige data. Bruken av data du henter må følge GDPR og annen relevant lovgivning om personvern. 