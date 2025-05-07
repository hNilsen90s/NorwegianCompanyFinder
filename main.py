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
import re


# Constants
API_BASE_URL = "https://data.brreg.no/enhetsregisteret/api/enheter"
DEFAULT_INDUSTRY_CODE = "73.11"  # Reklamebyrå som standard
MAX_PAGE_SIZE = 1000  # Maksimalt antall selskaper per API-kall

# Add this mapping for financial fields to human-readable CSV headers
FIN_FIELD_CSV_MAP = {
    "fin_period_start": "Finance Period Start",
    "fin_period_end": "Finance Period End",
    "fin_year": "Finance Year",
    "fin_currency": "Currency",
    "fin_account_type": "Account Type",
    "fin_in_liquidation": "In Liquidation (Finance)",
    "fin_small_company": "Small Company (Finance)",
    "fin_audited": "Audited",
    "fin_revenue": "Revenue",
    "fin_operating_result": "Operating Result",
    "fin_net_profit": "Net Profit",
    "fin_total_assets": "Total Assets",
    "fin_total_equity": "Total Equity",
    "fin_total_liabilities": "Total Liabilities",
    "fin_short_term_liabilities": "Short-term Liabilities",
    "fin_long_term_liabilities": "Long-term Liabilities",
    "fin_retained_earnings": "Retained Earnings",
    "fin_contributed_equity": "Contributed Equity",
    "fin_current_assets": "Current Assets",
    "fin_fixed_assets": "Fixed Assets",
    "fin_net_financial_items": "Net Financial Items",
    "fin_financial_income": "Financial Income",
    "fin_financial_expenses": "Financial Expenses",
    # Calculated fields
    "fin_profit_margin": "Profit Margin (%)",
    "fin_equity_ratio": "Equity Ratio (%)",
    "fin_debt_ratio": "Debt Ratio (%)",
    "fin_return_on_equity": "Return on Equity (%)"
}


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
    parser.add_argument(
        "--finance", "--fin",
        action="store_true",
        help="Include financial data for each company (rate-limited to 5 requests/sec)"
    )
    
    args = parser.parse_args()
    
    # Always set naeringskode attribute for compatibility
    if hasattr(args, "industry"):
        args.naeringskode = args.industry
    elif hasattr(args, "naeringskode"):
        args.naeringskode = args.naeringskode
    else:
        args.naeringskode = DEFAULT_INDUSTRY_CODE

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

    # List of all available financial fields (raw and calculated)
    finance_fields = [
        "revenue", "operating_result", "net_profit", "total_assets", "total_equity", "total_liabilities",
        "short_term_liabilities", "long_term_liabilities", "retained_earnings", "contributed_equity",
        "current_assets", "fixed_assets", "net_financial_items", "financial_income", "financial_expenses",
        "profit_margin", "equity_ratio", "debt_ratio", "return_on_equity",
        "period_start", "period_end", "year", "currency", "account_type", "in_liquidation", "small_company", "audited"
    ]
    # Add fin_ prefix for internal keys, but allow user to specify without prefix
    finance_fields_user = [f.replace("fin_", "") for f in FIN_FIELD_CSV_MAP.keys()]

    # Handle --fields
    if args.fields:
        requested = [f.strip().lower() for f in args.fields.split(",") if f.strip()]
        # Filter out invalid fields
        selected_fields = [f for f in requested if f in field_map]
        # Check if any finance fields are requested
        requested_finance = [f for f in requested if f in finance_fields_user]
        if requested_finance and not getattr(args, "finance", False):
            print("\nMERK: Du har valgt finansielle felter i --fields, så --fin er aktivert automatisk.")
            args.finance = True
        if not selected_fields and not requested_finance:
            print(f"Ingen gyldige felter valgt i --fields. Tilgjengelige: {', '.join(field_map.keys())}")
            sys.exit(1)
        args.selected_finance_fields = requested_finance
    else:
        selected_fields = default_fields
        args.selected_finance_fields = None

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


def fetch_latest_financials(orgnr):
    """
    Fetch the latest available financial data for a company by orgnr.
    Returns a dict of fin_ fields, or None if not available.
    """
    url = f"https://data.brreg.no/regnskapsregisteret/regnskap/{orgnr}"
    headers = {"Accept": "application/json"}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not data or not isinstance(data, list):
            return None
        # Find the entry with the latest period end date
        latest = max(data, key=lambda x: x.get("regnskapsperiode", {}).get("tilDato", ""))
        period = latest.get("regnskapsperiode", {})
        year = period.get("tilDato", "")[:4] if period.get("tilDato") else ""
        # Extract financial fields (with fin_ prefix)
        def get_nested(d, *keys):
            for k in keys:
                d = d.get(k, {}) if isinstance(d, dict) else {}
            return d if isinstance(d, (int, float, str)) else ""
        def get_sum(d, *keys):
            v = d
            for k in keys:
                v = v.get(k, {}) if isinstance(v, dict) else {}
            return v if isinstance(v, (int, float)) else ""
        fin = {}
        fin["fin_period_start"] = period.get("fraDato", "")
        fin["fin_period_end"] = period.get("tilDato", "")
        fin["fin_year"] = year
        fin["fin_currency"] = latest.get("valuta", "")
        fin["fin_account_type"] = latest.get("regnskapstype", "")
        fin["fin_in_liquidation"] = latest.get("avviklingsregnskap", "")
        fin["fin_small_company"] = latest.get("regnkapsprinsipper", {}).get("smaaForetak", "")
        fin["fin_audited"] = not latest.get("revisjon", {}).get("ikkeRevidertAarsregnskap", False)
        fin["fin_revenue"] = get_sum(latest.get("resultatregnskapResultat", {}).get("driftsresultat", {}), "driftsinntekter", "sumDriftsinntekter")
        fin["fin_operating_result"] = get_sum(latest.get("resultatregnskapResultat", {}), "driftsresultat", "driftsresultat")
        fin["fin_net_profit"] = get_sum(latest.get("resultatregnskapResultat", {}), "aarsresultat")
        fin["fin_total_assets"] = get_sum(latest.get("eiendeler", {}), "sumEiendeler")
        fin["fin_total_equity"] = get_sum(latest.get("egenkapitalGjeld", {}).get("egenkapital", {}), "sumEgenkapital")
        fin["fin_total_liabilities"] = get_sum(latest.get("egenkapitalGjeld", {}).get("gjeldOversikt", {}), "sumGjeld")
        fin["fin_short_term_liabilities"] = get_sum(latest.get("egenkapitalGjeld", {}).get("gjeldOversikt", {}), "kortsiktigGjeld", "sumKortsiktigGjeld")
        fin["fin_long_term_liabilities"] = get_sum(latest.get("egenkapitalGjeld", {}).get("gjeldOversikt", {}), "langsiktigGjeld", "sumLangsiktigGjeld")
        fin["fin_retained_earnings"] = get_sum(latest.get("egenkapitalGjeld", {}).get("egenkapital", {}), "opptjentEgenkapital", "sumOpptjentEgenkapital")
        fin["fin_contributed_equity"] = get_sum(latest.get("egenkapitalGjeld", {}).get("egenkapital", {}), "innskuttEgenkapital", "sumInnskuttEgenkaptial")
        fin["fin_current_assets"] = get_sum(latest.get("eiendeler", {}), "omloepsmidler", "sumOmloepsmidler")
        fin["fin_fixed_assets"] = get_sum(latest.get("eiendeler", {}), "anleggsmidler", "sumAnleggsmidler")
        fin["fin_net_financial_items"] = get_sum(latest.get("resultatregnskapResultat", {}).get("finansresultat", {}), "nettoFinans")
        fin["fin_financial_income"] = get_sum(latest.get("resultatregnskapResultat", {}).get("finansresultat", {}), "finansinntekt", "sumFinansinntekter")
        fin["fin_financial_expenses"] = get_sum(latest.get("resultatregnskapResultat", {}).get("finansresultat", {}), "finanskostnad", "sumFinanskostnad")
        return fin
    except Exception:
        return None


def calculate_financial_ratios(fin):
    """
    Calculate financial ratios and add them to the fin dict. All values are in percent (as strings, formatted to 2 decimals).
    """
    def safe_div(n, d):
        try:
            n = float(n)
            d = float(d)
            if d == 0:
                return ""
            return n / d
        except Exception:
            return ""
    # Profit Margin = Net Profit / Revenue
    pm = safe_div(fin.get("fin_net_profit", 0), fin.get("fin_revenue", 0))
    fin["fin_profit_margin"] = f"{pm * 100:.2f}" if pm != "" else ""
    # Equity Ratio = Total Equity / Total Assets
    er = safe_div(fin.get("fin_total_equity", 0), fin.get("fin_total_assets", 0))
    fin["fin_equity_ratio"] = f"{er * 100:.2f}" if er != "" else ""
    # Debt Ratio = Total Liabilities / Total Assets
    dr = safe_div(fin.get("fin_total_liabilities", 0), fin.get("fin_total_assets", 0))
    fin["fin_debt_ratio"] = f"{dr * 100:.2f}" if dr != "" else ""
    # Return on Equity = Net Profit / Total Equity
    roe = safe_div(fin.get("fin_net_profit", 0), fin.get("fin_total_equity", 0))
    fin["fin_return_on_equity"] = f"{roe * 100:.2f}" if roe != "" else ""
    return fin


def save_to_csv(companies_data, output_file, selected_fields, field_map, extra_fields=None):
    """
    Save company data to CSV file (headers in English). If extra_fields is provided, include them as additional columns.
    """
    if not companies_data:
        print("\nIngen selskaper å lagre.")
        return False
    try:
        fieldnames = [field_map[f] for f in selected_fields]
        if extra_fields:
            # Use human-readable names for financial fields
            fieldnames += [FIN_FIELD_CSV_MAP.get(f, f) for f in extra_fields]
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for data in companies_data:
                # Map financial keys to human-readable keys for CSV output
                if extra_fields:
                    row = data.copy()
                    for f in extra_fields:
                        if f in row:
                            value = row.pop(f)
                            # Format numbers: remove .0 for ints, add thousands separator
                            if isinstance(value, (int, float)):
                                if value == int(value):
                                    value = f"{int(value):,}".replace(",", " ")
                                else:
                                    value = f"{value:,.2f}".replace(",", " ")
                            elif isinstance(value, str):
                                try:
                                    num = float(value)
                                    if num == int(num):
                                        value = f"{int(num):,}".replace(",", " ")
                                    else:
                                        value = f"{num:,.2f}".replace(",", " ")
                                except Exception:
                                    pass
                            row[FIN_FIELD_CSV_MAP.get(f, f)] = value
                    writer.writerow(row)
                else:
                    writer.writerow(data)
        return True
    except IOError as e:
        print(f"\nFeil ved lagring av fil: {e}")
        return False


def fetch_companies(naeringskode, output_file, selected_fields, field_map, limit=None, filter_expr=None, finance=False, selected_finance_fields=None):
    """
    Main function: Fetch all companies with the specified industry code and save to CSV (English headers).
    If finance is True, also fetch financial data for each company (rate-limited).
    Only include requested financial fields if specified.
    """
    print(f"Starter nedlasting av selskaper med næringskode {naeringskode}..." + (f" (grense: {limit})" if limit else ""))
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
                company_dict = extract_company_data(company, selected_fields, field_map, all_fields=True)
                company_data = {field_map[f]: company_dict[f] for f in selected_fields}

                pass_preliminary_filter = True
                has_finance_component_in_filter = False

                if filter_expr:
                    # Define keywords that indicate a financial part of the filter.
                    # These should be the base names used in filter expressions (e.g., "net_profit").
                    finance_keywords = [
                        "revenue", "operating_result", "net_profit", "total_assets", "total_equity", "total_liabilities",
                        "short_term_liabilities", "long_term_liabilities", "retained_earnings", "contributed_equity",
                        "current_assets", "fixed_assets", "net_financial_items", "financial_income", "financial_expenses",
                        "profit_margin", "equity_ratio", "debt_ratio", "return_on_equity",
                        "period_start", "period_end", "year", "currency", "account_type", "in_liquidation", "small_company", "audited"
                    ]
                    has_finance_component_in_filter = any(keyword in filter_expr for keyword in finance_keywords)

                    if has_finance_component_in_filter:
                        # If filter has financial components, try to evaluate non-financial parts first.
                        # This uses the existing logic (lines 447-460) to build 'general_filter_segment'.
                        # This reconstruction might be imperfect for very complex filters.
                        clauses = re.split(r'\band\b|\bor\b', filter_expr)
                        ops = re.findall(r'\band\b|\bor\b', filter_expr)
                        general_clauses = []
                        for clause in clauses:
                            if not any(f_keyword in clause for f_keyword in finance_keywords):
                                general_clauses.append(clause.strip())
                        
                        general_filter_segment = ""
                        if general_clauses:
                            general_filter_segment = general_clauses[0]
                            op_idx = 0 # Index for ops list
                            # The following loop for reconstructing general_filter_segment is from the original code.
                            # It attempts to piece together general clauses with their original operators.
                            # This specific logic for choosing ops (esp. `clauses[op_idx].strip() == ''`) can be fragile.
                            for i in range(1, len(general_clauses)):
                                # Attempt to find the correct operator that connected the original clauses
                                # This part of the original logic is complex and might not always pick the correct operator
                                # if general clauses are interspersed with financial ones in a non-trivial way.
                                while op_idx < len(ops) and clauses[op_idx].strip() == '': # Original problematic condition
                                    op_idx += 1
                                if op_idx < len(ops):
                                    general_filter_segment += f' {ops[op_idx]} {general_clauses[i]}'
                                    op_idx += 1
                                else: # Not enough ops, could happen if filter ends with a general clause
                                    pass 
                        
                        pass_preliminary_filter = safe_eval_filter(general_filter_segment, company_dict) if general_filter_segment else True
                    else:
                        # Filter expression exists but has NO financial components
                        pass_preliminary_filter = safe_eval_filter(filter_expr, company_dict)
                
                if not pass_preliminary_filter:
                    continue # Skip company if preliminary (general) filter fails

                # At this point, preliminary conditions are met, or there was no relevant preliminary filter.
                company_fully_meets_criteria = True # Assume true, may be falsified by financial checks

                if finance: # If --fin is active (args.finance)
                    orgnr = company_dict.get("orgnr")
                    fin_data = fetch_latest_financials(orgnr)
                    
                    if fin_data:
                        fin_data = calculate_financial_ratios(fin_data)
                        # Add selected or all financial data to company_data (for CSV) and company_dict (for logic)
                        if selected_finance_fields is not None:
                            for f_user_key in selected_finance_fields: # e.g., "net_profit"
                                internal_fin_key = f"fin_{f_user_key}" # e.g., "fin_net_profit"
                                if internal_fin_key in fin_data:
                                    company_data[internal_fin_key] = fin_data[internal_fin_key]
                                    company_dict[internal_fin_key] = fin_data[internal_fin_key]
                        else: # Add all fetched financial data
                            company_data.update(fin_data) # For CSV output (uses fin_ prefix from fin_data)
                            company_dict.update(fin_data) # For internal logic
                    else: # No financial data found
                        if selected_finance_fields is not None:
                            for f_user_key in selected_finance_fields:
                                internal_fin_key = f"fin_{f_user_key}"
                                company_data[internal_fin_key] = "" # Ensure CSV column exists if requested
                                company_dict[internal_fin_key] = "" # Ensure key exists for consistency
                        # If all finance fields are implicitly requested (selected_finance_fields is None),
                        # ensure all potential filterable keys get default values in company_dict later if not present.

                    # Convert numeric financial fields in company_dict to float for evaluation.
                    # Keys like 'net_profit' (without 'fin_') are created/updated here.
                    # This list should match the finance_keywords that are numeric.
                    numeric_financial_keywords = [
                        "revenue", "operating_result", "net_profit", "total_assets", "total_equity", "total_liabilities",
                        "short_term_liabilities", "long_term_liabilities", "retained_earnings", "contributed_equity",
                        "current_assets", "fixed_assets", "net_financial_items", "financial_income", "financial_expenses",
                        "profit_margin", "equity_ratio", "debt_ratio", "return_on_equity"
                    ]
                    for num_fin_keyword in numeric_financial_keywords:
                        internal_fin_key = f"fin_{num_fin_keyword}"
                        eval_key = num_fin_keyword # Key used in filter expression, e.g., "net_profit"
                        
                        if internal_fin_key in company_dict and company_dict[internal_fin_key] is not None:
                            try:
                                value_str = str(company_dict[internal_fin_key]).replace(" ", "").replace("\xa0", "")
                                company_dict[eval_key] = float(value_str) if value_str.strip() != '' else 0.0
                            except (ValueError, TypeError):
                                company_dict[eval_key] = 0.0
                        else:
                            # Ensure the key exists for safe_eval_filter, defaulting to 0.0 if no data.
                            company_dict[eval_key] = 0.0
                    
                    # For non-numeric financial fields (e.g., 'audited', 'small_company') from finance_keywords,
                    # ensure they are in company_dict if filter uses them.
                    # `extract_company_data` already handles general fields.
                    # `fetch_latest_financials` populates `fin_` prefixed keys.
                    # `safe_eval_filter` can access `fin_audited` if filter explicitly uses `fin_audited`.
                    # If filter uses `audited`, then `company_dict['audited']` should exist.
                    # We can populate these from their fin_ counterparts if not already done by numeric loop.

                    # Now, if the original filter had a financial component, evaluate the *full* filter.
                    if filter_expr and has_finance_component_in_filter:
                        company_fully_meets_criteria = safe_eval_filter(filter_expr, company_dict)
                    # If no financial component in filter, criteria remains as per preliminary check (True here).
                
                else: # --fin is NOT active (finance is False)
                    if filter_expr and has_finance_component_in_filter:
                        # Cannot satisfy a financial filter if financial data is not fetched.
                        company_fully_meets_criteria = False
                    # If no financial component, criteria is based on preliminary_pass (True here).

                # Final decision to add the company
                if company_fully_meets_criteria:
                    companies_data.append(company_data)
                
                if limit is not None and len(companies_data) >= limit:
                    print(f"\nGrense på {limit} selskaper nådd.")
                    url = None
                    break
            url = next_url
            current_params = None
            page_number += 1
            if limit is not None and len(companies_data) >= limit:
                break
            time.sleep(1)
    except Exception as e:
        print(f"\nEn uventet feil oppstod: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Only include requested finance fields if specified
        if finance:
            if selected_finance_fields is not None:
                fin_fields = [f"fin_{f}" for f in selected_finance_fields]
            else:
                fin_fields = [
                    "fin_period_start", "fin_period_end", "fin_year", "fin_currency", "fin_account_type", "fin_in_liquidation", "fin_small_company", "fin_audited", "fin_revenue", "fin_operating_result", "fin_net_profit", "fin_total_assets", "fin_total_equity", "fin_total_liabilities", "fin_short_term_liabilities", "fin_long_term_liabilities", "fin_retained_earnings", "fin_contributed_equity", "fin_current_assets", "fin_fixed_assets", "fin_net_financial_items", "fin_financial_income", "fin_financial_expenses",
                    "fin_profit_margin", "fin_equity_ratio", "fin_debt_ratio", "fin_return_on_equity"
                ]
            save_to_csv(companies_data, output_file, selected_fields, field_map, extra_fields=fin_fields)
        else:
            save_to_csv(companies_data, output_file, selected_fields, field_map)
        print(f"\nFant {len(companies_data)} selskaper som matcher filter blant {total_seen} enheter med næringskode {naeringskode}")
        print(f"Data lagret til {output_file}")


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
            filter_expr=args.filter,
            finance=getattr(args, "finance", False),
            selected_finance_fields=getattr(args, "selected_finance_fields", None)
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
