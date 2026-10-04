---
name: firesprinklerskill
description: Expired Fire Suppression Sprinkler Tests & Municipal Fire Marshal Citations. Connects commercial building owners, auto repair shops, and daycares facing 30-day fire watch citations with state-licensed RME-G fire sprinkler inspection contractors. Includes public municipal citation ingestion, reacherhq email verification, and warm intro broker scripts.
---

# Expired Fire Suppression Sprinkler Tests & Municipal Fire Marshal Citations

**Small commercial landlords, auto repair shops, and commercial daycares must pass an annual NFPA 25 fire sprinkler and suppression inspection. When the local Fire Marshal conducts an annual survey and finds an expired tag, they issue a "30-Day Notice of Violation / Fire Watch Order". If not rectified immediately, the business is forced to pay off-duty firefighters $50–$100/hour to sit on physical "Fire Watch," costing $1,200/day until a state-licensed fire sprinkler contractor signs off.**

---

## 1. Supply & Demand Dynamics (1 + 1 = 2)

| Dimension | Description |
|---|---|
| **Demand** | Small commercial business owners, auto repair shops, daycares, and building operators with overdue NFPA 25 fire inspection citations facing mandatory physical fire watch. |
| **Supply** | State-licensed commercial fire sprinkler inspection, riser tag certification, and backflow testing contractors (e.g. Texas RME-G, Florida Class I/II, NYC Master Suppression). |
| **The Bleed** | **\$1,200/day**. Local fire codes mandate that an uncertified or impaired fire sprinkler system cannot operate unattended. The city requires certified off-duty firefighters on continuous site patrol (\$50–\$100/hr) or shuts the building down. |
| **Your Payout** | **\$1,500 – \$2,500 flat introduction fee** paid by the licensed fire contractor upon contract signing. |

---

## 2. Mandatory Core Rule: Cross-Campaign Historical Deduplication

> [!IMPORTANT]
> **Never email the same recipient twice across ANY campaign.**
> 
> Before launching ANY outreach (Austin, Chicago, Miami, Dallas, or future regions), all extracted leads MUST be cross-referenced against historical sends in the Warmbly database:
> ```sql
> SELECT DISTINCT LOWER(c.email) 
> FROM campaign_contact_progress ccp 
> JOIN contacts c ON c.id = ccp.contact_id 
> WHERE ccp.sent_at IS NOT NULL;
> ```
> Any lead whose email address was already emailed in ANY past campaign is automatically filtered out by `scripts/firesprinklermarket.py` and `scripts/verify_reacher.py`.

---

## 3. The Public Files & Direct Data Sources

### Demand Sources (Municipal Fire Marshal & Code Enforcement Portals)
Updated weekly across public municipal open data hubs and GIS feature servers:
* **City of Austin / Travis County**: Austin Fire Department Life Safety inspection dockets and Citizen Connect code compliance filings.
* **City of Chicago**: Chicago Fire Prevention Bureau & Department of Buildings violations portal (`data.cityofchicago.org/resource/22u3-xenr.json`, violation code `CN035013` - sprinkler pump & flow test deficiencies).
* **New York City (FDNY)**: Bureau of Fire Prevention Active Violation Orders (`data.cityofnewyork.us/resource/bi53-yph3.json`, law `SPK 40` & `FC 901.6`).
* **Miami-Dade County**: Fire Rescue Bureau of Fire Prevention Accela Citizen Access (ACA) portal and Open Data Hub.
* **Open Record Fields**: Property Address, Building Representative Name, Title, Email, Phone, Citation Date, and 30-Day Remediation Deadline.

### Supply Sources (State Fire Marshal Office Licensee Databases)
* **Texas State Fire Marshal's Office (SFMO)**: Official registry of licensed **RME-G** (Responsible Managing Employee - General) and SCR (Sprinkler Certificate of Registration) contractors.
* **Florida Division of State Fire Marshal (DFS)**: Bureau of Fire Prevention registered Class I, II, and III Fire Protection System Contractors.
* **Illinois State Fire Marshal (OSFM)** & City of Chicago Licensed Fire Suppression Contractors.
* **Federal Small Business Registry (SBA DSBS)**: NAICS `238220` (Commercial Fire Sprinkler & Piping Contractors).

---

## 4. Email Verification Engine (reacherhq/check-if-email-exists)

All emails in the pipeline are verified using the open-source Rust engine [reacherhq/check-if-email-exists](https://github.com/reacherhq/check-if-email-exists) via the local Docker backend at `http://localhost:8081/v0/check_email`.

The verification pipeline executes 5 sequential checks:
1. **Syntax Validation**: Strict RFC compliance check.
2. **Disposable Domain Detection**: Real-time screening against burner domain registries.
3. **MX Record Resolution**: Verification that the target domain has active Mail Exchanger servers.
4. **SMTP Reachability Check**: Low-level handshake simulating mail exchange without sending spam.
5. **Warmbly Deduplication Gate**: Cross-references against Warmbly PostgreSQL database to prevent duplicate outreach.

---

## 5. Running the Pipeline

All scripts are located in `scripts/`:

```bash
# 1. Pull demand and supply leads for a campaign
python3 .agents/skills/firesprinklerskill/scripts/firesprinklermarket.py --demand 100 --contractors 50 --out ~/Desktop

# 2. Filter by specific city or state
python3 .agents/skills/firesprinklerskill/scripts/firesprinklermarket.py --state Texas --city Austin --demand 25 --contractors 10 --out ~/Desktop

# 3. Pull live municipal sprinkler citations from Chicago & NYC open data APIs
python3 .agents/skills/firesprinklerskill/scripts/fetch_citations.py

# 4. Verify any CSV through reacherhq/check-if-email-exists
python3 .agents/skills/firesprinklerskill/scripts/verify_reacher.py input_leads.csv verified_leads.csv

# 5. Check a single email directly via reacher
python3 .agents/skills/firesprinklerskill/scripts/verify_reacher.py --email owner@commercialbldg.com
```

### Command Flags:
| Flag | Action |
|---|---|
| `--demand N` | Pull $N$ building owners/operators with active citations |
| `--contractors N` | Pull $N$ licensed RME-G fire sprinkler contractors |
| `--city "Austin"` | Narrow down to a target municipality |
| `--state "Texas"` | Narrow down to a target state |
| `--again` | Include previously dispatched records (least-recently-given first) |
| `--forget` | Wipe the local ledger (`data/given.csv`) |
| `--out <dir>` | Destination folder for export CSVs |

---

## 6. Cold Outreach Scripts & The Neutral Introduction

### To the Building Manager / Property Owner (Demand)
*Subject:* Fire Watch - {{.property_address}}

```text
Hey {{.FirstName}}

Saw the FDNY compliance notice filed on the {{.property_address}} sprinkler tags.

Paying for mandatory fire watch while waiting on contractors in NYC is brutal.

I partner with a licensed fire suppression contractor here that has open slots to inspect the riser and file with the marshal this week.

Open to an intro?

Best,
Abdulaziz
```

*(Sent strictly in plain text: `text_only = true`, no HTML, no tracking pixel).*

---

### To the Licensed Fire Sprinkler Contractor / RME-G (Supply)
*Subject:* Sprinkler accounts

```text
Hey {{.FirstName}}

I have commercial properties and landlords in NYC under active FDNY sprinkler violation orders looking for sign-offs this week to avoid fire watch.

Before I send anyone your way, wanted to check if you have inspection bandwidth right now.

What boroughs do you cover?

Best,
Abdulaziz
```

---

### The Warm 3-Way Introduction (Once Contractor Confirms Fee)
*Subject:* Intro: {building_representative} <> {contractor_name} (Sprinkler Recertification)

```text
Hi {building_greeting}, {contractor_greeting},

Connecting you both here.

{building_representative} runs {property_name} at {property_address} and needs an expedited NFPA 25 inspection and riser valve tag recertification to clear the active Fire Marshal notice before the deadline.

{contractor_representative} is an RME-G licensed fire protection contractor with open inspection bandwidth in {place} who can certify the system and submit the required documentation directly to the Fire Prevention Bureau.

I'll step aside and let you two coordinate access, scheduling, and paperwork from here.

Best,
Abdulaziz
```

---

## 7. Deliverability & Platform Mapping Guidelines

When loading export CSVs into Instantly or Smartlead:
* Always map using **snake_case** parameters:
  * `first_name` $\rightarrow$ `first_name`
  * `greeting` $\rightarrow$ `greeting`
  * `property_address` $\rightarrow$ `property_address`
  * `place` $\rightarrow$ `city`
* Outbound cold outreach emails must default to `text_only = true` (pure `text/plain` format).
* Enforce safe per-mailbox pacing (minimum 5 minutes between outbound sends).
