#!/usr/bin/env python3
"""
Brønnøysundregisteret Datasøker

Dette skriptet henter selskapsdata fra Brønnøysundregisteret basert på næringskoder.
Det henter kontaktinformasjon, stiftelsesdato, adresse og annen nyttig informasjon.
"""

import requests
import time
import csv
import argparse
import sys
from urllib.parse import urljoin, urlparse, parse_qs


# Konstanter
API_BASE_URL = "https://data.brreg.no/enhetsregisteret/api/enheter"
DEFAULT_INDUSTRY_CODE = "73.11"  # Reklamebyrå som standard
MAX_PAGE_SIZE = 1000  # Maksimalt antall selskaper per API-kall


def parse_arguments():
    """
    Behandler kommandolinjeargumenter.
    
    Returns:
        argparse.Namespace: Objekt med behandlede argumenter
    """
    parser = argparse.ArgumentParser(
        description="Hent selskapsdata fra Brønnøysundregisteret basert på næringskode"
    )
    parser.add_argument(
        "--naeringskode", "-n", 
        type=str, 
        default=DEFAULT_INDUSTRY_CODE, 
        help=f"Næringskode for selskaper som skal hentes (f.eks. {DEFAULT_INDUSTRY_CODE} for reklamebyrå)"
    )
    parser.add_argument(
        "--output", "-o", 
        type=str, 
        help="Navn på output CSV-fil. Standard er [næringskode]_selskaper.csv"
    )
    
    args = parser.parse_args()
    
    # Bruk standard filnavn hvis ikke spesifisert
    if not args.output:
        args.output = f"{args.naeringskode.replace('.', '_')}_selskaper.csv"
    
    return args


def fetch_companies_page(url, params=None, page_number=0):
    """
    Henter en side med selskapsdata fra API-et.
    
    Args:
        url (str): API-URL som skal hentes data fra
        params (dict, optional): Forespørselsparametere (for første kall)
        page_number (int): Sidenummer som hentes
    
    Returns:
        tuple: (data, next_url) der data er JSON-responsen og next_url er lenken til neste side
    """
    headers = {"Accept": "application/json"}
    
    try:
        print(f"Henter side {page_number}...", end="")
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Sjekk om responsen inneholder enheter
        companies = data.get("_embedded", {}).get("enheter", [])
        if not companies:
            print(" Ingen flere selskaper funnet.")
            return data, None
            
        print(f" Lastet ned {len(companies)} selskaper.")
        
        # Finn lenke til neste side
        next_url = data.get("_links", {}).get("next", {}).get("href")
        return data, next_url
        
    except requests.exceptions.RequestException as e:
        print(f"\nFeil ved nedlasting av side {page_number}: {e}")
        return None, None


def extract_company_data(company):
    """
    Trekker ut relevant data fra et selskaps JSON-objekt.
    
    Args:
        company (dict): JSON-data for ett selskap
    
    Returns:
        dict: Renset og formatert selskapsdata
    """
    # Grunnleggende selskapsinformasjon
    company_name = company.get("navn", "")
    email = company.get("epostadresse", "")
    telefon = company.get("telefon", "")
    mobil = company.get("mobil", "")
    hjemmeside = company.get("hjemmeside", "")
    orgnr = company.get("organisasjonsnummer", "")
    antall_ansatte = company.get("antallAnsatte", "")
    
    # Datoer
    stiftelsesdato = company.get("stiftelsesdato", "")
    registreringsdato = company.get("registreringsdatoEnhetsregisteret", "")
    
    # Adressehåndtering
    adresse = ""
    if company.get("forretningsadresse"):
        adresse_list = company.get("forretningsadresse", {}).get("adresse", [])
        postnr = company.get("forretningsadresse", {}).get("postnummer", "")
        poststed = company.get("forretningsadresse", {}).get("poststed", "")
        
        if adresse_list:
            adresse = ", ".join(adresse_list)
            if postnr and poststed:
                adresse += f", {postnr} {poststed}"
    
    # Returner formatert data
    return {
        "Company Name": company_name,
        "Org.nr": orgnr,
        "Stiftelsesdato": stiftelsesdato,
        "Registreringsdato": registreringsdato,
        "Email": email.lower() if email else "",
        "Telefon": telefon,
        "Mobil": mobil,
        "Hjemmeside": hjemmeside,
        "Adresse": adresse,
        "Ansatte": antall_ansatte
    }


def save_to_csv(companies_data, output_file):
    """
    Lagrer selskapsdata til CSV-fil.
    
    Args:
        companies_data (list): Liste med ordbøker som inneholder selskapsdata
        output_file (str): Filnavn for CSV-filen
    
    Returns:
        bool: True hvis vellykket, False ved feil
    """
    if not companies_data:
        print("\nIngen selskaper å lagre.")
        return False
        
    try:
        fieldnames = [
            "Company Name", "Org.nr", "Stiftelsesdato", "Registreringsdato",
            "Email", "Telefon", "Mobil", "Hjemmeside", "Adresse", "Ansatte"
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for data in companies_data:
                writer.writerow(data)
        
        return True
    except IOError as e:
        print(f"\nFeil ved lagring av fil: {e}")
        return False


def fetch_companies(naeringskode, output_file):
    """
    Hovedfunksjon: Henter alle selskaper med spesifisert næringskode og lagrer til CSV.
    
    Args:
        naeringskode (str): Næringskode for selskaper som skal hentes
        output_file (str): Filnavn for output CSV
    """
    print(f"Starter nedlasting av selskaper med næringskode {naeringskode}...")
    
    # Initialiser parametere for API-kall
    params = {
        "naeringskode": naeringskode,
        "size": MAX_PAGE_SIZE,
        "page": 0,
    }
    
    companies_data = []  # For å samle alle selskaper med kontaktinfo
    total_seen = 0       # Teller for totalt antall selskapsobjekter
    page_number = 0      # For å holde styr på sidenummer
    
    try:
        # Start med base URL og API-parametere
        url = API_BASE_URL
        current_params = params
        
        # Hent data side for side
        while url:
            data, next_url = fetch_companies_page(url, current_params, page_number)
            
            if not data:  # Hvis API-kallet feilet
                break
                
            # Behandle selskaper fra denne siden
            companies = data.get("_embedded", {}).get("enheter", [])
            for company in companies:
                total_seen += 1
                
                # Ekstraher og behandle selskapsdata
                company_data = extract_company_data(company)
                
                # Lagre bare selskaper med kontaktinformasjon
                if (company_data["Email"] or company_data["Telefon"] or 
                    company_data["Mobil"] or company_data["Hjemmeside"]):
                    companies_data.append(company_data)
            
            # Forbered neste side
            url = next_url
            current_params = None  # Parametere er innebygd i neste URL
            page_number += 1
            
            # Pause for å respektere API-begrensninger
            time.sleep(1)
            
    except Exception as e:
        print(f"\nEn uventet feil oppstod: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Lagre dataene som er samlet inn så langt
        if save_to_csv(companies_data, output_file):
            print(f"\nFant {len(companies_data)} selskaper med kontaktinformasjon blant {total_seen} enheter med næringskode {naeringskode}")
            print(f"Data lagret til {output_file}")
        else:
            print("\nKunne ikke lagre data til fil.")


def main():
    """Hovedfunksjon som kjører programmet."""
    try:
        # Parse kommandolinjeargumenter
        args = parse_arguments()
        
        # Kjør hovedfunksjonen
        fetch_companies(args.naeringskode, args.output)
        
        return 0
    except KeyboardInterrupt:
        print("\nProgrammet ble avbrutt av brukeren.")
        return 1
    except Exception as e:
        print(f"\nEn kritisk feil oppstod: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
