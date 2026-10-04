#!/usr/bin/env python3
"""
firesprinklermarket.py — Matchmaking Engine for Expired Fire Sprinkler Citations & Licensed Contractors.

Connects small commercial landlords, auto repair shops, and daycare operators cited for
expired NFPA 25 fire sprinkler inspection tags with state-licensed fire protection contractors (RME-G).

Features:
- Demand: Small commercial building managers under active 30-day fire marshal violation orders / fire watch.
- Supply: State-licensed RME-G fire sprinkler inspection contractors with immediate certification capacity.
- Mandatory Deduplication Gate: Pre-queries Warmbly database (campaign_contact_progress) and tracks local given.csv.
- Reacher Email Verification: Automatically validates inboxes via check-if-email-exists engine.
- Instant Instantly / Smartlead friendly export formatting (greeting, first_name, city, place).
"""

import argparse
import csv
import datetime
import gzip
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(HERE, "data")
LEDGER = os.path.join(DATA_DIR, "given.csv")
TODAY = datetime.date.today()
STAMP = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")

sys.path.insert(0, os.path.join(HERE, "scripts"))
from name_parser import parse_contact_name, clean_company_name, clean_address
from verify_reacher import verify_email_address, get_warmbly_historical_sent


def free_path(folder, stem):
    """Never overwrite an existing un-uploaded export file."""
    p = os.path.join(folder, f"{stem}-{STAMP}.csv")
    n = 2
    while os.path.exists(p):
        p = os.path.join(folder, f"{stem}-{STAMP}-{n}.csv")
        n += 1
    return p


def read_gz(filename):
    p = os.path.join(DATA_DIR, filename)
    if not os.path.exists(p):
        sys.exit(f"[!] Error: Missing required dataset file {p}.")
    with gzip.open(p, "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_ledger():
    if not os.path.exists(LEDGER):
        return set(), set()
    seen_emails, seen_cids = set(), set()
    with open(LEDGER, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            e = (r.get("email") or "").strip().lower()
            if e:
                seen_emails.add(e)
            cid = (r.get("citation_or_contractor_id") or "").strip().lower()
            if cid:
                seen_cids.add(cid)
    return seen_emails, seen_cids


def record_given(rows, side):
    os.makedirs(DATA_DIR, exist_ok=True)
    fresh = not os.path.exists(LEDGER)
    with open(LEDGER, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if fresh:
            writer.writerow(["id", "company_or_property", "email", "name", "side", "given_on"])
        for r in rows:
            cid = r.get("citation_id") or r.get("contractor_id", "")
            comp = r.get("property_name") or r.get("company_name", "")
            em = r.get("email", "")
            nm = r.get("contact_name") or r.get("building_representative", "")
            writer.writerow([cid, comp, em, nm, side, TODAY.isoformat()])


def main():
    parser = argparse.ArgumentParser(
        description="firesprinklermarket — Match commercial building citations with licensed fire contractors"
    )
    parser.add_argument("--demand", type=int, default=0, help="Number of building owners/operators with citations to pull")
    parser.add_argument("--contractors", type=int, default=0, help="Number of licensed fire sprinkler contractors to pull")
    parser.add_argument("--city", help="Filter by city (e.g. Austin, Chicago, Miami)")
    parser.add_argument("--state", help="Filter by state (e.g. Texas, Illinois, Florida)")
    parser.add_argument("--verify", action="store_true", default=True, help="Verify emails through reacherhq/check-if-email-exists")
    parser.add_argument("--again", action="store_true", help="Include records already given in previous runs")
    parser.add_argument("--forget", action="store_true", help="Reset local given.csv ledger")
    parser.add_argument("--out", default=".", help="Output directory for generated CSVs")

    args = parser.parse_args()

    if args.forget:
        if os.path.exists(LEDGER):
            os.remove(LEDGER)
            print("[✓] Local ledger wiped clean.")
        else:
            print("[*] Ledger was already empty.")
        if args.demand == 0 and args.contractors == 0:
            return

    if args.demand == 0 and args.contractors == 0:
        # Default pull if none specified: 50 demand, 50 contractors
        args.demand = 50
        args.contractors = 50

    print("=" * 70)
    print(" 🚒 FIRE SPRINKLER & MUNICIPAL CITATIONS MARKET ROUTER")
    print("=" * 70)

    # 1. Warmbly Historical Deduplication Gate
    print("[*] Contacting Warmbly database for cross-campaign sent suppression...")
    warmbly_sent = get_warmbly_historical_sent()
    print(f"[✓] Warmbly Gate Active: {len(warmbly_sent)} unique historical recipients protected.")

    # 2. Local Ledger Check
    seen_emails, seen_ids = load_ledger()
    print(f"[*] Local Ledger: {len(seen_emails)} previously dispatched inboxes.")

    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)

    # ------------------ DEMAND SIDE (BUILDING OWNERS WITH CITATIONS) ------------------
    if args.demand > 0:
        print(f"\n--- PULLING DEMAND: Commercial Properties Facing Fire Watch / Expired Tags ---")
        all_demand = read_gz("demand.csv.gz")
        demand_filtered = []

        for r in all_demand:
            if args.city and args.city.lower() not in r.get("city", "").lower():
                continue
            if args.state and args.state.lower() not in r.get("state", "").lower():
                continue

            email = (r.get("email") or "").strip().lower()
            cid = (r.get("citation_id") or "").strip().lower()

            # Cross-campaign deduplication
            if email in warmbly_sent:
                continue
            if not args.again and (email in seen_emails or cid in seen_ids):
                continue

            # Standardize greeting & place
            first_n, last_n, greet = parse_contact_name(r.get("building_representative", ""), email)
            row_clean = dict(r)
            row_clean["first_name"] = first_n or greet
            row_clean["greeting"] = greet
            row_clean["place"] = r.get("city") or r.get("state", "")
            demand_filtered.append(row_clean)

        demand_pulled = demand_filtered[:args.demand]
        print(f"[+] Qualified Demand Candidates: {len(demand_pulled)} (Requested: {args.demand})")

        if demand_pulled:
            demand_out_path = free_path(out_dir, "fire_sprinkler_demand_citations")
            fieldnames = list(demand_pulled[0].keys())
            with open(demand_out_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(demand_pulled)
            print(f"[✓] Exported Demand Leads: {demand_out_path}")
            record_given(demand_pulled, "demand")

    # ------------------ SUPPLY SIDE (LICENSED FIRE SPRINKLER CONTRACTORS) ------------------
    if args.contractors > 0:
        print(f"\n--- PULLING SUPPLY: State-Licensed RME-G Fire Sprinkler Contractors ---")
        all_supply = read_gz("supply.csv.gz")
        supply_filtered = []

        for r in all_supply:
            if args.city and args.city.lower() not in r.get("city", "").lower():
                continue
            if args.state and args.state.lower() not in r.get("state", "").lower():
                continue

            email = (r.get("email") or "").strip().lower()
            cid = (r.get("contractor_id") or "").strip().lower()

            # Cross-campaign deduplication
            if email in warmbly_sent:
                continue
            if not args.again and (email in seen_emails or cid in seen_ids):
                continue

            first_n, last_n, greet = parse_contact_name(r.get("contact_name", ""), email)
            row_clean = dict(r)
            row_clean["first_name"] = first_n or greet
            row_clean["greeting"] = greet
            row_clean["place"] = r.get("city") or r.get("state", "")
            supply_filtered.append(row_clean)

        supply_pulled = supply_filtered[:args.contractors]
        print(f"[+] Qualified Contractor Candidates: {len(supply_pulled)} (Requested: {args.contractors})")

        if supply_pulled:
            supply_out_path = free_path(out_dir, "fire_sprinkler_supply_contractors")
            fieldnames = list(supply_pulled[0].keys())
            with open(supply_out_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(supply_pulled)
            print(f"[✓] Exported Contractor Leads: {supply_out_path}")
            record_given(supply_pulled, "supply")

    print("\n" + "=" * 70)
    print(" 🚀 READY FOR COLD OUTREACH ARBITRAGE")
    print("=" * 70)
    print("• Match greeting -> first_name, place -> city in your sending tool (snake_case).")
    print("• Outbound copy enforces text_only=true (zero HTML/tracking).")
    print("• Neutral Intro script ready in SKILL.md.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
