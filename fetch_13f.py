"""
Crowding Agent — 13F fetcher and crowding-score builder.

Pulls the latest 13F-HR filing for a curated list of prominent institutional
investors from SEC EDGAR, aggregates holdings by CUSIP, and computes a per-stock
"crowding score" weighted by the number of fund holders and total dollar value.

Outputs crowding.json (consumed by crowding_dashboard.html).
"""

import json
import math
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

# SEC requires a descriptive User-Agent with contact info.
USER_AGENT = "Crowding Agent Demo alex@example.com"

# Curated list of 13F filers. CIKs verified against EDGAR.
FUNDS = {
    "Berkshire Hathaway": "0001067983",
    "Bridgewater Associates": "0001350694",
    "Citadel Advisors": "0001423053",
    "Renaissance Technologies": "0001037389",
    "Two Sigma Investments": "0001179392",
    "Millennium Management": "0001273087",
    "D.E. Shaw": "0001009207",
    "Tiger Global Management": "0001167483",
    "Coatue Management": "0001135730",
    "Point72 Asset Management": "0001603466",
    "Pershing Square Capital": "0001336528",
    "Third Point": "0001040273",
    "Greenlight Capital": "0001079114",
    "Appaloosa": "0001056903",
    "Baupost Group": "0001061768",
    "ARK Investment Management": "0001697748",
    "Soros Fund Management": "0001029160",
    "Viking Global Investors": "0001103804",
    "Lone Pine Capital": "0001061165",
    "Maverick Capital": "0001088875",
    "Whale Rock Capital": "0001545440",
    "Duquesne Family Office": "0001536411",
    "Sequoia Capital Operations": "0001056831",
    "Tudor Investment": "0001037767",
    "Marshall Wace": "0001595888",
}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def latest_13f_filing(cik: str):
    """Return (accession_no, report_date) for most recent 13F-HR filing."""
    cik_padded = cik.zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    data = json.loads(fetch(url))
    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accessions = recent.get("accessionNumber", [])
    report_dates = recent.get("reportDate", [])
    for i, form in enumerate(forms):
        if form == "13F-HR":
            return accessions[i], report_dates[i]
    return None


def fetch_information_table(cik: str, accession_no: str):
    """Locate and parse the information table XML for a 13F-HR filing."""
    cik_int = str(int(cik))
    accession_clean = accession_no.replace("-", "")
    index_url = (
        f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_clean}/index.json"
    )
    idx = json.loads(fetch(index_url))

    # Find the info-table XML (skip primary_doc.xml which is the cover page).
    info_file = None
    for item in idx.get("directory", {}).get("item", []):
        name = item.get("name", "")
        if name.endswith(".xml") and "primary_doc" not in name.lower():
            info_file = name
            break
    if not info_file:
        return []

    xml_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_clean}/{info_file}"
    raw = fetch(xml_url)

    # Strip XML namespaces for trivial parsing.
    text = re.sub(rb'\sxmlns(:\w+)?="[^"]+"', b"", raw)
    root = ET.fromstring(text)

    holdings = []
    for el in root.iter():
        if el.tag.endswith("infoTable"):
            name = (el.findtext("nameOfIssuer") or "").strip()
            cusip = (el.findtext("cusip") or "").strip().upper()
            value_raw = (el.findtext("value") or "0").strip()
            try:
                value = int(value_raw)
            except ValueError:
                value = 0
            if name and cusip:
                holdings.append({"name": name, "cusip": cusip, "value": value})
    return holdings


def main():
    out_dir = Path(__file__).parent
    raw = {}
    for fund, cik in FUNDS.items():
        try:
            print(f"Fetching {fund}...")
            result = latest_13f_filing(cik)
            if not result:
                print("  no 13F-HR found")
                continue
            accession, report_date = result
            holdings = fetch_information_table(cik, accession)
            raw[fund] = {
                "cik": cik,
                "accession": accession,
                "report_date": report_date,
                "holdings": holdings,
            }
            print(f"  {len(holdings)} positions, report {report_date}")
            time.sleep(0.15)  # respect SEC ~10 req/s rate limit
        except Exception as e:
            print(f"  ERROR: {e}")

    (out_dir / "holdings_raw.json").write_text(json.dumps(raw))

    # Aggregate by CUSIP. 13F "value" is reported in thousands of USD.
    by_cusip = defaultdict(lambda: {"name": "", "funds": [], "total_value": 0})
    for fund, info in raw.items():
        # Collapse multiple share classes for the same fund+cusip.
        per_cusip_in_fund = defaultdict(lambda: {"name": "", "value": 0})
        for h in info["holdings"]:
            slot = per_cusip_in_fund[h["cusip"]]
            slot["name"] = h["name"]
            slot["value"] += h["value"]
        for cusip, slot in per_cusip_in_fund.items():
            row = by_cusip[cusip]
            row["name"] = slot["name"]
            row["funds"].append({"fund": fund, "value": slot["value"]})
            row["total_value"] += slot["value"]

    # Crowding score: 60% number-of-holders, 40% log-scaled total value.
    records = []
    if not by_cusip:
        print("No data fetched. Aborting.")
        return
    max_holders = max(len(v["funds"]) for v in by_cusip.values())
    max_value = max(v["total_value"] for v in by_cusip.values())
    log_max_value = math.log10(max_value + 1)

    for cusip, info in by_cusip.items():
        n_holders = len(info["funds"])
        if n_holders < 2:
            continue  # not crowded if only one fund holds it
        holders_score = (n_holders / max_holders) * 100
        value_score = (math.log10(info["total_value"] + 1) / log_max_value) * 100
        crowding_score = round(0.6 * holders_score + 0.4 * value_score, 1)
        records.append({
            "cusip": cusip,
            "name": info["name"],
            "n_holders": n_holders,
            "total_value_thousands": info["total_value"],
            "crowding_score": crowding_score,
            "holders_pct_of_max": round(holders_score, 1),
            "value_pct_of_max": round(value_score, 1),
            "funds": sorted(
                [{"fund": f["fund"], "value_thousands": f["value"]} for f in info["funds"]],
                key=lambda x: -x["value_thousands"],
            ),
        })
    records.sort(key=lambda x: -x["crowding_score"])

    output = {
        "fund_count": len(raw),
        "fund_names": list(raw.keys()),
        "report_dates": {f: info["report_date"] for f, info in raw.items()},
        "records": records,
        "methodology": (
            "Crowding score = 0.6 * (n_holders / max_n_holders) + "
            "0.4 * (log10(total_value) / log10(max_total_value)), scaled 0-100. "
            "Only securities held by 2+ funds in the cohort are scored."
        ),
    }
    (out_dir / "crowding.json").write_text(json.dumps(output, indent=2))

    print(f"\n{len(records)} crowded names ranked across {len(raw)} funds.")
    print("Top 15:")
    for r in records[:15]:
        print(
            f"  {r['crowding_score']:5.1f}  "
            f"{r['n_holders']:2d} funds  "
            f"${r['total_value_thousands']/1e6:8.2f}B  "
            f"{r['name'][:50]}"
        )


if __name__ == "__main__":
    main()
