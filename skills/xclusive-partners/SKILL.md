---
name: xclusive-partners
description: "Query and manage XCLUSIVE luxury partner directory and fleet."
version: 0.1.0
author: Mat (unthai), Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Concierge, Luxury, Aviation, Supercars, Yachts, XCLUSIVE]
    category: productivity
---

# XCLUSIVE Partner Directory & Asset Catalog Skill

Query, verify, register, and manage vetted high-end luxury partners (private jets, helicopters, superyachts, supercars, close protection, and off-market estates) and their real-time catalog assets via the XCLUSIVE Sovereign Command API.

## When to Use

- "Find private aviation or jet charter partners in Bangkok."
- "Check member daily rate for Ferrari or Lamborghini in Phuket."
- "Lookup emergency 24/7 dispatch hotline for Sovereign Protection."
- "Register new VIP partner company or stage candidate for audit."
- "Search fleet inventory by tail number, hull ID, or station hub."

## Prerequisites

- Environment variables:
  - `XCLUSIVE_API_BASE`: API base URL (default: `https://admin.xclusive-world.com`).
  - `XCLUSIVE_AGENT_KEY` or `XCLUSIVE_STAFF_SECRET`: Authentication secret for the platform service.

## How to Run

Execute the helper script via `terminal`:

```bash
# 1. Search partner companies
python3 <skill-dir>/scripts/xclusive_client.py companies --hub "Bangkok" --category "aviation_jet"

# 2. Get detailed company dossier with registered fleet
python3 <skill-dir>/scripts/xclusive_client.py company --id "comp_mjets"

# 3. Search fleet and luxury assets
python3 <skill-dir>/scripts/xclusive_client.py services --q "Ferrari" --hub "Bangkok"

# 4. Onboard / create high-end partner
python3 <skill-dir>/scripts/xclusive_client.py create-company \
  --name "Skyline Helicopters" \
  --category "helicopter" \
  --tier "vetted_partner" \
  --hubs "Bangkok,Phuket" \
  --sla 15 \
  --dispatch-channel "signal" \
  --dispatch-line "+66 81 234 5678"
```

## Safety & Boundaries

- Never disclose raw operator wholesale margins or wholesale spreads directly to external end-clients.
- 24/7 Emergency dispatch hotlines are strictly for authorized liaison and director desks.
