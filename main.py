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


# Constants
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
        "--industry", "--industry-code", "--naeringskode", "-i",
        type=str,
        default=DEFAULT_INDUSTRY_CODE,
        help=f"Industry code for companies to fetch (e.g. {DEFAULT_INDUSTRY_CODE} for advertising agency)"
    )
    parser.add_argument(
        "--output", "-o", 
        type=str, 
        help="Navn på output CSV-fil. Standard er [næringskode]_selskaper.csv"
    )
    parser.add_argument(
        "--fields", "-f",
        type=str,
        help=(
            "Kommaseparert liste over felter som skal inkluderes i CSV. "
            "Tilgjengelige felter: name, orgnr, incorporation_date, registration_date, "
            "email, phone, mobile, website, address, zipcode, state, street, in_liquidation, employees. "
            "Standard er alle felter."
        )
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=None,
        help="Maksimalt antall selskaper som skal lastes ned (standard: ingen grense)"
    )
    parser.add_argument(
        "--filter",
        type=str,
        default=None,
        help=(
            "Valgfritt: Filteruttrykk for å kun inkludere selskaper som matcher. "
            "Eksempel: 'email and not phone and employees and email == \"ok@test.com\"'. "
            "Tilgjengelige felter: name, orgnr, incorporation_date, registration_date, email, phone, mobile, website, address, zipcode, state, street, in_liquidation, employees."
        )
    )
    
    args = parser.parse_args()
    
    # Use default filename if not specified
    if not args.output:
        args.output = f"{args.naeringskode.replace('.', '_')}_selskaper.csv"

    # Define field mapping and default order (all English)
    field_map = {
        "name": "Name",
        "orgnr": "OrgNo",
        "incorporation_date": "IncorporationDate",
        "registration_date": "RegistrationDate",
        "email": "Email",
        "phone": "Phone",
        "mobile": "Mobile",
        "website": "Website",
        "address": "Address",
        "zipcode": "Zipcode",
        "state": "State",
        "street": "Street",
        "in_liquidation": "InLiquidation",
        "employees": "Employees"
    }
    default_fields = list(field_map.keys())

    # Handle --fields
    if args.fields:
        requested = [f.strip().lower() for f in args.fields.split(",") if f.strip()]
        # Filter out invalid fields
        selected_fields = [f for f in requested if f in field_map]
        if not selected_fields:
            print(f"Ingen gyldige felter valgt i --fields. Tilgjengelige: {', '.join(field_map.keys())}")
            sys.exit(1)
    else:
        selected_fields = default_fields

    args.selected_fields = selected_fields
    args.field_map = field_map
    return args


def fetch_companies_page(url, params=None, page_number=0):
    """
    Fetch a page of company data from the API.
    
    Args:
        url (str): API URL to fetch data from
        params (dict, optional): Request parameters (for first call)
        page_number (int): Page number being fetched
    
    Returns:
        tuple: (data, next_url) where data is the JSON response and next_url is the link to the next page
    """
    headers = {"Accept": "application/json"}
    
    try:
        print(f"Henter side {page_number}...", end="")
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Check if response contains companies
        companies = data.get("_embedded", {}).get("enheter", [])
        if not companies:
            print(" Ingen flere selskaper funnet.")
            return data, None
            
        print(f" Lastet ned {len(companies)} selskaper.")
        
        # Find link to next page
        next_url = data.get("_links", {}).get("next", {}).get("href")
        return data, next_url
        
    except requests.exceptions.RequestException as e:
        print(f"\nFeil ved nedlasting av side {page_number}: {e}")
        return None, None


def extract_company_data(company, selected_fields, field_map, all_fields=False):
    """
    Extract relevant company data for selected fields (all English keys). If all_fields=True, return all possible fields (Pythonic keys).
    """
    all_data = {
        "name": company.get("navn", ""),
        "orgnr": company.get("organisasjonsnummer", ""),
        "incorporation_date": company.get("stiftelsesdato", ""),
        "registration_date": company.get("registreringsdatoEnhetsregisteret", ""),
        "email": company.get("epostadresse", "").lower() if company.get("epostadresse") else "",
        "phone": company.get("telefon", ""),
        "mobile": company.get("mobil", ""),
        "website": company.get("hjemmeside", ""),
        "address": "",
        "zipcode": "",
        "state": "",
        "street": "",
        "in_liquidation": bool(company.get("underAvvikling", False)),
        "employees": company.get("antallAnsatte", "")
    }
    if company.get("forretningsadresse"):
        adresse_list = company.get("forretningsadresse", {}).get("adresse", [])
        postnr = company.get("forretningsadresse", {}).get("postnummer", "")
        poststed = company.get("forretningsadresse", {}).get("poststed", "")
        kommune = company.get("forretningsadresse", {}).get("kommune", "")
        if adresse_list:
            address = ", ".join(adresse_list)
            if postnr and poststed:
                address += f", {postnr} {poststed}"
            all_data["address"] = address
            all_data["street"] = ", ".join(adresse_list)
        all_data["zipcode"] = postnr
        all_data["state"] = kommune
    if all_fields:
        return all_data
    return {field_map[f]: all_data[f] for f in selected_fields}


def safe_eval_filter(filter_expr, company_dict):
    """
    Safely evaluate the filter expression for a single company.
    """
    allowed_names = {k: v for k, v in company_dict.items()}
    # Convert empty strings/None to False, everything else to True for boolean fields
    for k, v in allowed_names.items():
        if isinstance(v, str):
            allowed_names[k] = bool(v.strip())
        elif v is None:
            allowed_names[k] = False
    # But also keep the original values for comparison
    allowed_names.update({f"_{k}": v for k, v in company_dict.items()})
    # Now you can write e.g. email == "ok@test.com" (use _email for exact value)
    try:
        return eval(filter_expr, {"__builtins__": {}}, allowed_names)
    except Exception:
        return False


def save_to_csv(companies_data, output_file, selected_fields, field_map):
    """
    Save company data to CSV file (headers in English).
    """
    if not companies_data:
        print("\nNo companies to save.")
        return False
    try:
        fieldnames = [field_map[f] for f in selected_fields]
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for data in companies_data:
                writer.writerow(data)
        return True
    except IOError as e:
        print(f"\nError saving file: {e}")
        return False


def fetch_companies(naeringskode, output_file, selected_fields, field_map, limit=None, filter_expr=None):
    """
    Main function: Fetch all companies with the specified industry code and save to CSV (English headers).
    """
    print(f"Starting download of companies with industry code {naeringskode}..." + (f" (limit: {limit})" if limit else ""))
    params = {
        "naeringskode": naeringskode,
        "size": MAX_PAGE_SIZE,
        "page": 0,
    }
    companies_data = []
    total_seen = 0
    page_number = 0
    try:
        url = API_BASE_URL
        current_params = params
        while url:
            data, next_url = fetch_companies_page(url, current_params, page_number)
            if not data:
                break
            companies = data.get("_embedded", {}).get("enheter", [])
            for company in companies:
                total_seen += 1
                # For filter: always fetch all fields (python keys)
                company_dict = extract_company_data(company, selected_fields, field_map, all_fields=True)
                # For CSV: only selected fields (English)
                company_data = {field_map[f]: company_dict[f] for f in selected_fields}
                include = True
                if filter_expr:
                    include = safe_eval_filter(filter_expr, company_dict)
                if include:
                    companies_data.append(company_data)
                    if limit is not None and len(companies_data) >= limit:
                        print(f"\nLimit of {limit} companies reached.")
                        url = None
                        break
            url = next_url
            current_params = None
            page_number += 1
            if limit is not None and len(companies_data) >= limit:
                break
            time.sleep(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if save_to_csv(companies_data, output_file, selected_fields, field_map):
            print(f"\nFound {len(companies_data)} companies matching filter among {total_seen} entities with industry code {naeringskode}")
            print(f"Data saved to {output_file}")
        else:
            print("\nCould not save data to file.")


def main():
    """Main function that runs the program."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        # Run main function
        fetch_companies(
            args.naeringskode,
            args.output,
            args.selected_fields,
            args.field_map,
            limit=args.limit,
            filter_expr=args.filter
        )
        return 0
    except KeyboardInterrupt:
        print("\nProgrammet ble avbrutt av brukeren.")
        return 1
    except Exception as e:
        print(f"\nEn kritisk feil oppstod: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
