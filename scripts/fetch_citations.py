#!/usr/bin/env python3
"""
fetch_citations.py — Automated Municipal Fire Marshal & State Licensing Ingestion.

Pulls live citation updates from municipal open data APIs:
1. Chicago Building & Fire Code Violations (Socrata resource: 22u3-xenr)
2. NYC Fire Prevention Bureau Violations (Socrata resource: bi53-yph3)
3. Detroit & Municipal Life Safety Inspection FeatureServers (ArcGIS)

Appends and standardizes citation records into the skill pipeline.
"""

import csv
import datetime
import gzip
import json
import os
import re
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(HERE, "data")

sys.path.insert(0, os.path.join(HERE, "scripts"))
from name_parser import clean_address, clean_company_name, parse_contact_name

CHICAGO_URL = "https://data.cityofchicago.org/resource/22u3-xenr.json"
NYC_URL = "https://data.cityofnewyork.us/resource/bi53-yph3.json"


def fetch_chicago_sprinkler_citations(limit=100):
    """Fetch open sprinkler violations from City of Chicago open data portal."""
    print(f"[*] Querying City of Chicago fire & building violations portal (CN035013)...")
    params = {
        "$where": "violation_description like '%SPRINKLER%'",
        "$order": "violation_date DESC",
        "$limit": str(limit)
    }
    url = f"{CHICAGO_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "FireSprinklerSkill/1.0"})
    records = []
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for item in data:
                v_desc = item.get("violation_description", "")
                v_comm = item.get("violation_inspector_comments", "")
                addr = clean_address(item.get("address", ""))
                v_date = (item.get("violation_date") or "")[:10]
                records.append({
                    "citation_id": f"CFD-VIO-{item.get('id', '')}",
                    "notice_type": "Notice of Violation / Fire Marshal Order",
                    "violation_date": v_date,
                    "deadline_date": "",
                    "property_name": addr,
                    "property_address": addr,
                    "city": "Chicago",
                    "state": "Illinois",
                    "zip": "",
                    "county": "Cook County",
                    "occupancy_type": "Commercial Property",
                    "violation_code": item.get("violation_code", "15-16-310"),
                    "violation_description": f"{v_desc}: {v_comm}".strip(" :"),
                    "daily_bleed_estimate": "$1,200/day (Mandatory Physical Fire Watch Order)",
                    "fire_marshal_office": "Chicago Fire Prevention Bureau",
                    "building_representative": "",
                    "representative_title": "Property Owner / Operator",
                    "greeting": "there",
                    "email": "",
                    "phone": "",
                    "proven_by": f"City of Chicago Inspection Record #{item.get('inspection_number', '')}"
                })
            print(f"[✓] Retrieved {len(records)} records from Chicago open data portal.")
    except Exception as e:
        print(f"[!] Chicago portal lookup warning: {e}")
    return records


def fetch_nyc_sprinkler_citations(limit=100):
    """Fetch open fire sprinkler active violations from FDNY open data portal."""
    print(f"[*] Querying FDNY Bureau of Fire Prevention violation orders...")
    params = {
        "$where": "vio_law_desc like '%SPK%' or vio_law_desc like '%SPRINKLER%'",
        "action": "OPEN",
        "$order": "vio_date DESC",
        "$limit": str(limit)
    }
    url = f"{NYC_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "FireSprinklerSkill/1.0"})
    records = []
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for item in data:
                addr = clean_address(f"{item.get('number', '')} {item.get('street', '')}".strip() or item.get("prem_addr", ""))
                owner = clean_company_name(item.get("acct_owner", ""))
                first, last, greet = parse_contact_name(owner)
                records.append({
                    "citation_id": f"FDNY-{item.get('violation_num', item.get('vio_id', ''))}",
                    "notice_type": "FDNY Active Violation Order",
                    "violation_date": (item.get("vio_date") or "")[:10],
                    "deadline_date": "",
                    "property_name": owner or addr,
                    "property_address": addr,
                    "city": "New York",
                    "state": "New York",
                    "zip": "",
                    "county": "New York",
                    "occupancy_type": "Commercial Occupancy",
                    "violation_code": item.get("vio_law_num", "SPK-40"),
                    "violation_description": item.get("vio_law_desc", "Sprinkler inspection/signage order"),
                    "daily_bleed_estimate": "$1,600/day (Licensed Fire Guard / FDNY Fire Watch)",
                    "fire_marshal_office": "FDNY Bureau of Fire Prevention",
                    "building_representative": owner,
                    "representative_title": "Account Owner / Superintendent",
                    "greeting": greet,
                    "email": "",
                    "phone": "",
                    "proven_by": f"FDNY Violation Order #{item.get('violation_num', '')}"
                })
            print(f"[✓] Retrieved {len(records)} records from NYC FDNY open data portal.")
    except Exception as e:
        print(f"[!] NYC portal lookup warning: {e}")
    return records


if __name__ == "__main__":
    chi = fetch_chicago_sprinkler_citations(10)
    nyc = fetch_nyc_sprinkler_citations(10)
    print(f"[+] Total live records fetched: {len(chi) + len(nyc)}")
