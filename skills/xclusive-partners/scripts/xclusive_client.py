#!/usr/bin/env python3
"""
xclusive_client.py — CLI and library client for XCLUSIVE Partner Directory and Asset Catalog.

Communicates with the sovereign back-office platform at admin.xclusive-world.com
using the agent API key. Zero external dependencies (uses standard urllib).
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def get_base_url():
    base = os.getenv("XCLUSIVE_API_BASE", "https://xclusive-world.com")
    return base.rstrip("/")


def get_api_key():
    key = os.getenv("XCLUSIVE_AGENT_KEY") or os.getenv("XCLUSIVE_STAFF_SECRET")
    if not key:
        sys.stderr.write("Error: XCLUSIVE_AGENT_KEY or XCLUSIVE_STAFF_SECRET environment variable is required.\n")
        sys.exit(1)
    return key.strip()


def api_request(path, method="GET", body=None, params=None):
    base = get_base_url()
    api_key = get_api_key()

    url = f"{base}{path}"
    if params:
        clean_params = {k: v for k, v in params.items() if v is not None and v != ""}
        if clean_params:
            url += f"?{urllib.parse.urlencode(clean_params)}"

    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("x-api-key", api_key)
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "HermesAgent/XCLUSIVE-Client")

    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            res_data = res.read().decode("utf-8")
            if not res_data:
                return {"ok": True}
            return json.loads(res_data)
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_msg)
            sys.stderr.write(f"API Error ({e.code}): {err_json.get('error', err_msg)}\n")
        except Exception:
            sys.stderr.write(f"API Error ({e.code}): {err_msg}\n")
        sys.exit(1)
    except urllib.error.URLError as e:
        sys.stderr.write(f"Connection Error: {e.reason}\n")
        sys.exit(1)


# ── Subcommand Handlers ───────────────────────────────────────────────────────

def cmd_companies(args):
    params = {
        "q": args.q,
        "category": args.category,
        "tier": args.tier,
        "hub": args.hub,
        "active": "all" if args.all else None,
    }
    data = api_request("/api/xclusive/partners/companies", method="GET", params=params)
    companies = data.get("companies", [])
    if args.json:
        print(json.dumps(companies, indent=2))
        return

    if not companies:
        print("No partner companies found matching query.")
        return

    print(f"=== XCLUSIVE Partners ({len(companies)}) ===")
    for c in companies:
        hubs_str = ", ".join(c.get("hubs") or [])
        status = "ACTIVE" if c.get("active") else "INACTIVE"
        print(f"\n[{c.get('tier', '').upper()}] {c.get('name')} (ID: {c.get('id')}) - {status}")
        print(f"  Category: {c.get('category')} | Hubs: {hubs_str}")
        print(f"  SLA: <= {c.get('sla_dispatch_minutes')}m | Margin: {c.get('commission_margin_percent')}% | Disc: {c.get('member_discount_percent')}%")
        print(f"  Dispatch: {c.get('dispatch_24_7_line') or c.get('contact_phone') or 'N/A'} (via {c.get('dispatch_channel')})")
        if c.get("notes"):
            print(f"  Notes: {c.get('notes')}")


def cmd_company(args):
    data = api_request(f"/api/xclusive/partners/companies/{urllib.parse.quote(args.id)}", method="GET")
    company = data.get("company", {})
    if args.json:
        print(json.dumps(company, indent=2))
        return

    print(f"=== {company.get('name')} ===")
    print(f"Legal Name: {company.get('legal_name') or 'N/A'}")
    print(f"Category:   {company.get('category')} | Tier: {company.get('tier')}")
    print(f"Hubs:       {', '.join(company.get('hubs') or [])}")
    print(f"Contact:    {company.get('contact_primary_name')} ({company.get('contact_email')})")
    print(f"Dispatch:   {company.get('dispatch_24_7_line')} (Channel: {company.get('dispatch_channel')})")
    print(f"SLA:        <= {company.get('sla_dispatch_minutes')} mins")
    print(f"Commercial: Margin {company.get('commission_margin_percent')}%, Member Disc {company.get('member_discount_percent')}%")
    print(f"Compliance: NDA={company.get('nda_signed')}, Insurance={company.get('insurance_verified')}")
    if company.get("notes"):
        print(f"Notes:      {company.get('notes')}")

    services = company.get("services") or []
    if services:
        print(f"\n--- Registered Assets ({len(services)}) ---")
        for s in services:
            m_rate = f"{s.get('base_currency')} {s.get('member_rate')/100:,.0f}" if s.get('member_rate') else "On Request"
            print(f"  * {s.get('title')} [{s.get('asset_identifier') or 'N/A'}] - {m_rate} / {s.get('rate_basis')}")


def cmd_create_company(args):
    hubs = [h.strip() for h in args.hubs.split(",")] if args.hubs else ["Bangkok"]
    body = {
        "name": args.name,
        "category": args.category,
        "tier": args.tier or "vetted_partner",
        "hubs": hubs,
        "legal_name": args.legal_name,
        "contact_primary_name": args.contact_name,
        "contact_email": args.contact_email,
        "contact_phone": args.contact_phone,
        "dispatch_24_7_line": args.dispatch_line,
        "dispatch_channel": args.dispatch_channel or "signal",
        "sla_dispatch_minutes": args.sla or 15,
        "member_discount_percent": args.discount or 0,
        "commission_margin_percent": args.margin or 15,
        "license_or_cert": args.license,
        "notes": args.notes,
    }
    data = api_request("/api/xclusive/partners/companies", method="POST", body=body)
    c = data.get("company", {})
    print(f"Created Partner Company: {c.get('name')} (ID: {c.get('id')})")
    if args.json:
        print(json.dumps(c, indent=2))


def cmd_update_company(args):
    body = {}
    if args.name: body["name"] = args.name
    if args.category: body["category"] = args.category
    if args.tier: body["tier"] = args.tier
    if args.hubs: body["hubs"] = [h.strip() for h in args.hubs.split(",")]
    if args.dispatch_line: body["dispatch_24_7_line"] = args.dispatch_line
    if args.dispatch_channel: body["dispatch_channel"] = args.dispatch_channel
    if args.sla: body["sla_dispatch_minutes"] = args.sla
    if args.margin is not None: body["commission_margin_percent"] = args.margin
    if args.discount is not None: body["member_discount_percent"] = args.discount
    if args.notes: body["notes"] = args.notes
    if args.active is not None: body["active"] = (args.active.lower() in ("true", "1", "yes"))

    data = api_request(f"/api/xclusive/partners/companies/{urllib.parse.quote(args.id)}", method="PATCH", body=body)
    c = data.get("company", {})
    print(f"Updated Partner Company: {c.get('name')} (ID: {c.get('id')})")


def cmd_delete_company(args):
    api_request(f"/api/xclusive/partners/companies/{urllib.parse.quote(args.id)}", method="DELETE")
    print(f"Deactivated Partner Company {args.id}")


def cmd_services(args):
    params = {
        "q": args.q,
        "company_id": args.company_id,
        "category": args.category,
        "hub": args.hub,
        "visibility": args.visibility,
    }
    data = api_request("/api/xclusive/partners/services", method="GET", params=params)
    services = data.get("services", [])
    if args.json:
        print(json.dumps(services, indent=2))
        return

    if not services:
        print("No luxury assets found matching query.")
        return

    print(f"=== XCLUSIVE Fleet & Asset Inventory ({len(services)}) ===")
    for s in services:
        m_rate = f"{s.get('base_currency')} {s.get('member_rate')/100:,.0f}" if s.get('member_rate') else "On Request"
        print(f"\n* {s.get('title')} ({s.get('category')})")
        print(f"  Operator:   {s.get('company_name')} [{s.get('company_tier')}]")
        print(f"  Station:    {s.get('hub_or_region') or 'Global'} | Identifier: {s.get('asset_identifier') or '—'}")
        print(f"  Member Rate: {m_rate} / {s.get('rate_basis')} (Vis: {s.get('visibility')})")


def cmd_create_service(args):
    specs = {}
    if args.specs:
        try:
            specs = json.loads(args.specs)
        except Exception:
            pass
    body = {
        "company_id": args.company_id,
        "title": args.title,
        "category": args.category,
        "asset_identifier": args.identifier,
        "hub_or_region": args.hub,
        "base_currency": args.currency or "THB",
        "base_rate": args.base_rate,
        "member_rate": args.member_rate,
        "rate_basis": args.rate_basis or "per_day",
        "visibility": args.visibility or "members_only",
        "specifications": specs,
    }
    data = api_request("/api/xclusive/partners/services", method="POST", body=body)
    s = data.get("service", {})
    print(f"Registered Luxury Asset: {s.get('title')} (ID: {s.get('id')})")


# ── Main Entry Point ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="XCLUSIVE Sovereign Partner Directory CLI for Hermes")
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    # companies
    p_comp = subparsers.add_parser("companies", help="Search partner companies")
    p_comp.add_argument("--q", help="Search keyword")
    p_comp.add_argument("--category", help="Category filter")
    p_comp.add_argument("--tier", help="Tier filter")
    p_comp.add_argument("--hub", help="Operating hub filter")
    p_comp.add_argument("--all", action="store_true", help="Include inactive companies")
    p_comp.add_argument("--json", action="store_true", help="Output raw JSON")
    p_comp.set_defaults(func=cmd_companies)

    # company detail
    p_c = subparsers.add_parser("company", help="Get single company by ID")
    p_c.add_argument("--id", required=True, help="Company ID")
    p_c.add_argument("--json", action="store_true", help="Output raw JSON")
    p_c.set_defaults(func=cmd_company)

    # create company
    p_cc = subparsers.add_parser("create-company", help="Create partner company")
    p_cc.add_argument("--name", required=True)
    p_cc.add_argument("--category", required=True)
    p_cc.add_argument("--tier", default="vetted_partner")
    p_cc.add_argument("--hubs", help="Comma-separated hubs")
    p_cc.add_argument("--legal-name")
    p_cc.add_argument("--contact-name")
    p_cc.add_argument("--contact-email")
    p_cc.add_argument("--contact-phone")
    p_cc.add_argument("--dispatch-line")
    p_cc.add_argument("--dispatch-channel", choices=["signal", "whatsapp", "direct_phone", "encrypted_email"])
    p_cc.add_argument("--sla", type=int)
    p_cc.add_argument("--discount", type=float)
    p_cc.add_argument("--margin", type=float)
    p_cc.add_argument("--license")
    p_cc.add_argument("--notes")
    p_cc.add_argument("--json", action="store_true")
    p_cc.set_defaults(func=cmd_create_company)

    # update company
    p_uc = subparsers.add_parser("update-company", help="Update partner company")
    p_uc.add_argument("--id", required=True)
    p_uc.add_argument("--name")
    p_uc.add_argument("--category")
    p_uc.add_argument("--tier")
    p_uc.add_argument("--hubs")
    p_uc.add_argument("--dispatch-line")
    p_uc.add_argument("--dispatch-channel")
    p_uc.add_argument("--sla", type=int)
    p_uc.add_argument("--margin", type=float)
    p_uc.add_argument("--discount", type=float)
    p_uc.add_argument("--active")
    p_uc.add_argument("--notes")
    p_uc.set_defaults(func=cmd_update_company)

    # delete company
    p_dc = subparsers.add_parser("delete-company", help="Deactivate partner company")
    p_dc.add_argument("--id", required=True)
    p_dc.set_defaults(func=cmd_delete_company)

    # services
    p_svc = subparsers.add_parser("services", help="Search luxury assets")
    p_svc.add_argument("--q", help="Search keyword")
    p_svc.add_argument("--company-id")
    p_svc.add_argument("--category")
    p_svc.add_argument("--hub")
    p_svc.add_argument("--visibility")
    p_svc.add_argument("--json", action="store_true")
    p_svc.set_defaults(func=cmd_services)

    # create service
    p_cs = subparsers.add_parser("create-service", help="Register asset under partner")
    p_cs.add_argument("--company-id", required=True)
    p_cs.add_argument("--title", required=True)
    p_cs.add_argument("--category", required=True)
    p_cs.add_argument("--identifier")
    p_cs.add_argument("--hub")
    p_cs.add_argument("--currency", default="THB")
    p_cs.add_argument("--base-rate", type=int)
    p_cs.add_argument("--member-rate", type=int)
    p_cs.add_argument("--rate-basis", default="per_day")
    p_cs.add_argument("--visibility", default="members_only")
    p_cs.add_argument("--specs")
    p_cs.set_defaults(func=cmd_create_service)

    parsed = parser.parse_args()
    parsed.func(parsed)


if __name__ == "__main__":
    main()
