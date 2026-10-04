"""
name_parser.py — Normalization and Contact Parsing for Fire Marshals & Sprinkler Contractors.

Handles:
1. Building Representatives, Property Managers, and Owners:
   - Cleans entity names (e.g. 'ABC REALTY MANAGEMENT LLC' -> 'ABC Realty Management')
   - Distinguishes individuals from corporate/entity strings
   - Generates natural, human email salutations ('Hi Robert' or 'Hi there')
2. Licensed Fire Sprinkler Contractors & RME-G (Responsible Managing Employees):
   - Cleans contractor firm names ('TITAN FIRE PROTECTION INC' -> 'Titan Fire Protection')
   - Parses RME names, license numbers (RME-G, SCR, Class I/II/III)
"""

import re

ENTITY_SUFFIXES = re.compile(
    r'\b(inc\.?|llc|l\.l\.c\.?|corp\.?|corporation|enterprises|properties|property|realty|'
    r'holdings?|management|mgmt|services|associates|group|ltd\.?|limited|co\.?|company)\b',
    re.I
)

SMALL_WORDS = {"of", "the", "and", "in", "on", "at", "for", "a", "an", "de", "la"}


def clean_company_name(name):
    """Normalize loud, all-caps or messy contractor/property management company names."""
    if not name:
        return ""
    s = re.sub(r'\s+', ' ', str(name)).strip()
    # Strip common noise
    s = re.sub(r'[\(\[\{].*?[\)\]\}]', '', s).strip()
    if s.isupper():
        words = s.split(' ')
        res = []
        for w in words:
            wl = w.lower()
            if wl in SMALL_WORDS and res:
                res.append(wl)
            elif wl in ("llc", "inc", "corp", "ltd", "lp", "llp", "rme", "scr", "nfpa"):
                res.append(wl.upper())
            else:
                res.append(w.capitalize())
        s = " ".join(res)
    return s.strip()


def parse_contact_name(full_name, email="", default_greeting="there"):
    """
    Given a name string from inspection portals or contractor rosters, returns:
    (first_name, last_name, greeting)
    """
    if not full_name:
        # Check if email can yield a hint, otherwise fallback
        if email and "@" in email:
            user_part = email.split("@")[0].lower()
            if "." in user_part:
                candidate = user_part.split(".")[0].capitalize()
                if len(candidate) > 2 and candidate.isalpha():
                    return candidate, "", candidate
        return "", "", default_greeting

    raw = re.sub(r'\s+', ' ', str(full_name)).strip()

    # Check if raw name is an LLC or Corporate entity, not a human
    if ENTITY_SUFFIXES.search(raw) or any(term in raw.lower() for term in ["dept", "department", "fire", "plaza", "center", "shop"]):
        return "", "", default_greeting

    # Remove titles/credentials (P.E., NICET, RME, etc.)
    cleaned = re.sub(r'\b(P\.?E\.?|NICET(\s*[I|V|X]+)?|RME-?[A-Z]*|CFPS|MS|BS)\b', '', raw, flags=re.I).strip()
    cleaned = re.sub(r'[,;].*$', '', cleaned).strip()

    parts = [p.strip() for p in cleaned.split(" ") if p.strip()]
    if not parts:
        return "", "", default_greeting

    # If format is "LAST, FIRST"
    if "," in raw:
        sub = raw.split(",")[1].strip().split(" ")[0].capitalize()
        if sub.isalpha() and len(sub) > 1:
            return sub, parts[0].capitalize(), sub

    # If first token is title like Mr./Ms.
    if parts[0].lower() in ["mr.", "mr", "ms.", "ms", "mrs.", "mrs", "dr.", "dr"]:
        if len(parts) >= 2:
            return parts[1].capitalize(), parts[-1].capitalize(), parts[1].capitalize()

    first = parts[0].capitalize()
    last = parts[-1].capitalize() if len(parts) > 1 else ""

    # Check if first looks like initials or numbers
    if len(first) == 1 or not first.isalpha():
        return "", "", default_greeting

    return first, last, first


def clean_address(addr):
    """Normalize street addresses into clean title case."""
    if not addr:
        return ""
    s = re.sub(r'\s+', ' ', str(addr)).strip()
    if s.isupper():
        words = s.split(" ")
        res = []
        for w in words:
            wl = w.lower()
            if wl in ["ne", "nw", "se", "sw", "n", "s", "e", "w"]:
                res.append(wl.upper())
            elif wl in ["apt", "ste", "suite", "unit", "bldg", "fl"]:
                res.append(wl.capitalize())
            else:
                res.append(w.capitalize())
        return " ".join(res)
    return s
