"""
Builds crowding.json from a realistic synthetic dataset of 13F holdings.

Used as a stand-in when EDGAR is not reachable from this environment. Output
schema matches fetch_13f.py exactly, so the dashboard works with either source.

Holdings are seeded from widely-reported public top positions of each fund
(13F filings are public record). Dollar values are approximated from recent
quarter-end share counts × prices and rounded; treat them as illustrative.
"""

import json
import math
import random
from collections import defaultdict
from pathlib import Path

random.seed(42)

# Common-name -> CUSIP map (real CUSIPs for major US tickers).
CUSIP = {
    "APPLE INC":                "037833100",
    "MICROSOFT CORP":           "594918104",
    "NVIDIA CORP":              "67066G104",
    "AMAZON.COM INC":           "023135106",
    "META PLATFORMS INC":       "30303M102",
    "ALPHABET INC CL A":        "02079K305",
    "ALPHABET INC CL C":        "02079K107",
    "TESLA INC":                "88160R101",
    "BERKSHIRE HATHAWAY CL B":  "084670702",
    "JPMORGAN CHASE & CO":      "46625H100",
    "VISA INC":                 "92826C839",
    "MASTERCARD INC":           "57636Q104",
    "UNITEDHEALTH GROUP INC":   "91324P102",
    "ELI LILLY & CO":           "532457108",
    "BANK OF AMERICA CORP":     "060505104",
    "PROCTER & GAMBLE CO":      "742718109",
    "JOHNSON & JOHNSON":        "478160104",
    "COCA-COLA CO":             "191216100",
    "AMERICAN EXPRESS CO":      "025816109",
    "CHEVRON CORP":             "166764100",
    "OCCIDENTAL PETROLEUM":     "674599105",
    "MOODY'S CORP":             "615369105",
    "KRAFT HEINZ CO":           "500754106",
    "CITIGROUP INC":            "172967424",
    "CAPITAL ONE FINANCIAL":    "14040H105",
    "COSTCO WHOLESALE CORP":    "22160K105",
    "WALMART INC":              "931142103",
    "NETFLIX INC":              "64110L106",
    "SALESFORCE INC":           "79466L302",
    "ADOBE INC":                "00724F101",
    "ORACLE CORP":              "68389X105",
    "BROADCOM INC":             "11135F101",
    "ASML HOLDING NV":          "N07059210",
    "TAIWAN SEMICONDUCTOR ADR": "874039100",
    "ADVANCED MICRO DEVICES":   "007903107",
    "INTUIT INC":               "461202103",
    "SERVICENOW INC":           "81762P102",
    "WORKDAY INC":              "98138H101",
    "PALANTIR TECHNOLOGIES":    "69608A108",
    "BLOCK INC":                "852234103",
    "ROKU INC":                 "77543R102",
    "COINBASE GLOBAL INC":      "19260Q107",
    "ROBINHOOD MARKETS":        "770700102",
    "UIPATH INC":               "90364P105",
    "SHOPIFY INC":              "82509L107",
    "SEA LTD ADR":              "Y7757P104",
    "SPOTIFY TECHNOLOGY SA":    "L8681T102",
    "UBER TECHNOLOGIES":        "90353T100",
    "AIRBNB INC":               "009066101",
    "RESTAURANT BRANDS INTL":   "76131D103",
    "HOWARD HUGHES HOLDINGS":   "44267T102",
    "LOWE'S COS INC":           "548661107",
    "HILTON WORLDWIDE":         "43300A203",
    "CHIPOTLE MEXICAN GRILL":   "169656105",
    "UNIVERSAL MUSIC GROUP":    "N90176104",
    "BROOKFIELD CORP":          "11271J107",
    "NIKE INC CL B":             "654106103",
    "PG&E CORP":                "69331C108",
    "BATH & BODY WORKS":        "070830106",
    "SIRIUS XM HOLDINGS":       "82968B103",
    "LIBERTY MEDIA SIRIUSXM":   "531229854",
    "VERTEX PHARMACEUTICALS":   "92532F100",
    "NOVO NORDISK ADR":         "670100205",
    "BRISTOL-MYERS SQUIBB":     "110122108",
    "ALIBABA GROUP ADR":        "01609W102",
    "JD.COM ADR":               "47215P106",
    "CAESARS ENTERTAINMENT":    "12769G100",
    "LIBERTY GLOBAL CL C":      "G5480U150",
    "THERAVANCE BIOPHARMA":     "G8807B106",
    "GARRETT MOTION":           "366505105",
    "VERITONE INC":             "923607109",
    "GREEN BRICK PARTNERS":     "393347107",
    "BRIGHTHOUSE FINANCIAL":    "10922N103",
    "CONSOL ENERGY":            "20854L108",
    "PENN ENTERTAINMENT":       "707569109",
    "US FOODS HOLDING":         "912008109",
    "DISNEY (WALT) CO":         "254687106",
    "MCDONALD'S CORP":          "580135101",
    "PEPSICO INC":              "713448108",
    "EXXON MOBIL CORP":         "30231G102",
    "T-MOBILE US INC":          "872590104",
    "VERIZON COMMUNICATIONS":   "92343V104",
    "GENERAL ELECTRIC":         "369604301",
    "BOEING CO":                "097023105",
    "WELLS FARGO & CO":         "949746101",
    "GOLDMAN SACHS GROUP":      "38141G104",
    "MORGAN STANLEY":           "617446448",
    "BLACKSTONE INC":           "09260D107",
    "KKR & CO INC":             "48251W104",
    "S&P GLOBAL INC":           "78409V104",
    "INTERCONTINENTAL EXCHG":   "45866F104",
    "NASDAQ INC":               "631103108",
    "MARRIOTT INTERNATIONAL":   "571903202",
    "STARBUCKS CORP":           "855244109",
    "BOOKING HOLDINGS":         "09857L108",
    "HOME DEPOT INC":           "437076102",
    "TJX COMPANIES":            "872540109",
    "MERCK & CO":               "58933Y105",
    "PFIZER INC":               "717081103",
    "ABBVIE INC":               "00287Y109",
    "COUPANG INC":              "22266T109",
    "WILLIAMS COS":             "969457100",
    "TEVA PHARMACEUTICAL":      "881624209",
    "COHERENT CORP":            "19247G107",
}

# Each entry: (issuer_name, value_in_thousands_USD).
# Values are illustrative based on recent quarter-end disclosures.
HOLDINGS = {
    "Berkshire Hathaway": [
        ("APPLE INC", 75200000),
        ("BANK OF AMERICA CORP", 31600000),
        ("AMERICAN EXPRESS CO", 36500000),
        ("COCA-COLA CO", 25400000),
        ("CHEVRON CORP", 18800000),
        ("OCCIDENTAL PETROLEUM", 14600000),
        ("KRAFT HEINZ CO", 11200000),
        ("MOODY'S CORP", 11700000),
        ("SIRIUS XM HOLDINGS", 2400000),
        ("CITIGROUP INC", 2900000),
        ("CAPITAL ONE FINANCIAL", 1700000),
    ],
    "Bridgewater Associates": [
        ("PROCTER & GAMGE CO".replace("PROCTER & GAMGE", "PROCTER & GAMBLE"), 850000),
        ("JOHNSON & JOHNSON", 720000),
        ("COCA-COLA CO", 660000),
        ("COSTCO WHOLESALE CORP", 540000),
        ("WALMART INC", 510000),
        ("PEPSICO INC", 470000),
        ("MCDONALD'S CORP", 380000),
        ("APPLE INC", 360000),
        ("MICROSOFT CORP", 340000),
        ("ALPHABET INC CL C", 280000),
        ("AMAZON.COM INC", 260000),
        ("NVIDIA CORP", 240000),
        ("EXXON MOBIL CORP", 220000),
        ("ELI LILLY & CO", 210000),
    ],
    "Citadel Advisors": [
        ("APPLE INC", 5400000),
        ("MICROSOFT CORP", 4900000),
        ("NVIDIA CORP", 4600000),
        ("META PLATFORMS INC", 3200000),
        ("AMAZON.COM INC", 3000000),
        ("ALPHABET INC CL A", 2800000),
        ("TESLA INC", 1900000),
        ("BROADCOM INC", 1700000),
        ("ELI LILLY & CO", 1600000),
        ("UNITEDHEALTH GROUP INC", 1500000),
        ("VISA INC", 1400000),
        ("MASTERCARD INC", 1100000),
        ("BERKSHIRE HATHAWAY CL B", 980000),
        ("JPMORGAN CHASE & CO", 920000),
        ("ADVANCED MICRO DEVICES", 870000),
    ],
    "Renaissance Technologies": [
        ("VERTEX PHARMACEUTICALS", 1900000),
        ("NOVO NORDISK ADR", 1800000),
        ("BRISTOL-MYERS SQUIBB", 1500000),
        ("PALANTIR TECHNOLOGIES", 1300000),
        ("AIRBNB INC", 1100000),
        ("UBER TECHNOLOGIES", 980000),
        ("APPLE INC", 950000),
        ("MICROSOFT CORP", 870000),
        ("NVIDIA CORP", 740000),
        ("ELI LILLY & CO", 660000),
        ("META PLATFORMS INC", 600000),
        ("ALPHABET INC CL C", 510000),
        ("MERCK & CO", 480000),
        ("PFIZER INC", 410000),
    ],
    "Two Sigma Investments": [
        ("APPLE INC", 1900000),
        ("MICROSOFT CORP", 1800000),
        ("NVIDIA CORP", 1500000),
        ("AMAZON.COM INC", 1400000),
        ("META PLATFORMS INC", 1200000),
        ("ALPHABET INC CL A", 1100000),
        ("TESLA INC", 880000),
        ("ELI LILLY & CO", 760000),
        ("UNITEDHEALTH GROUP INC", 720000),
        ("JPMORGAN CHASE & CO", 690000),
        ("BERKSHIRE HATHAWAY CL B", 580000),
        ("VISA INC", 540000),
        ("MASTERCARD INC", 470000),
        ("BROADCOM INC", 430000),
    ],
    "Millennium Management": [
        ("MICROSOFT CORP", 3100000),
        ("APPLE INC", 2900000),
        ("NVIDIA CORP", 2700000),
        ("META PLATFORMS INC", 2200000),
        ("ALPHABET INC CL A", 1900000),
        ("AMAZON.COM INC", 1800000),
        ("TESLA INC", 1300000),
        ("ELI LILLY & CO", 1100000),
        ("BROADCOM INC", 970000),
        ("ADVANCED MICRO DEVICES", 850000),
        ("VISA INC", 770000),
        ("MASTERCARD INC", 720000),
        ("BERKSHIRE HATHAWAY CL B", 660000),
        ("JPMORGAN CHASE & CO", 620000),
    ],
    "D.E. Shaw": [
        ("APPLE INC", 2400000),
        ("MICROSOFT CORP", 2200000),
        ("NVIDIA CORP", 2000000),
        ("AMAZON.COM INC", 1700000),
        ("META PLATFORMS INC", 1400000),
        ("ALPHABET INC CL A", 1200000),
        ("ELI LILLY & CO", 950000),
        ("BERKSHIRE HATHAWAY CL B", 720000),
        ("JPMORGAN CHASE & CO", 690000),
        ("UNITEDHEALTH GROUP INC", 640000),
        ("BROADCOM INC", 580000),
        ("VISA INC", 540000),
        ("MASTERCARD INC", 490000),
    ],
    "Tiger Global Management": [
        ("MICROSOFT CORP", 1700000),
        ("META PLATFORMS INC", 1500000),
        ("APPLE INC", 1100000),
        ("JD.COM ADR", 540000),
        ("SEA LTD ADR", 480000),
        ("SHOPIFY INC", 420000),
        ("SPOTIFY TECHNOLOGY SA", 380000),
        ("ALPHABET INC CL A", 360000),
        ("AMAZON.COM INC", 340000),
        ("NVIDIA CORP", 290000),
        ("ASML HOLDING NV", 250000),
    ],
    "Coatue Management": [
        ("MICROSOFT CORP", 1900000),
        ("META PLATFORMS INC", 1700000),
        ("AMAZON.COM INC", 1400000),
        ("NETFLIX INC", 1100000),
        ("ALPHABET INC CL C", 950000),
        ("SPOTIFY TECHNOLOGY SA", 690000),
        ("UBER TECHNOLOGIES", 620000),
        ("DISNEY (WALT) CO", 510000),
        ("NVIDIA CORP", 470000),
        ("APPLE INC", 410000),
    ],
    "Point72 Asset Management": [
        ("APPLE INC", 1300000),
        ("MICROSOFT CORP", 1200000),
        ("NVIDIA CORP", 1100000),
        ("META PLATFORMS INC", 880000),
        ("ALPHABET INC CL A", 820000),
        ("AMAZON.COM INC", 760000),
        ("TESLA INC", 540000),
        ("ELI LILLY & CO", 470000),
        ("BROADCOM INC", 410000),
        ("UNITEDHEALTH GROUP INC", 380000),
    ],
    "Pershing Square Capital": [
        ("RESTAURANT BRANDS INTL", 1700000),
        ("HOWARD HUGHES HOLDINGS", 1500000),
        ("CHIPOTLE MEXICAN GRILL", 1400000),
        ("HILTON WORLDWIDE", 1300000),
        ("LOWE'S COS INC", 1200000),
        ("UNIVERSAL MUSIC GROUP", 1100000),
        ("ALPHABET INC CL C", 980000),
        ("ALPHABET INC CL A", 880000),
        ("NIKE INC CL B", 760000),
        ("BROOKFIELD CORP", 660000),
    ],
    "Third Point": [
        ("MICROSOFT CORP", 590000),
        ("AMAZON.COM INC", 470000),
        ("PG&E CORP", 410000),
        ("BATH & BODY WORKS", 320000),
        ("META PLATFORMS INC", 280000),
        ("APPLE INC", 240000),
        ("ALPHABET INC CL A", 220000),
        ("NVIDIA CORP", 190000),
    ],
    "Greenlight Capital": [
        ("GREEN BRICK PARTNERS", 480000),
        ("BRIGHTHOUSE FINANCIAL", 130000),
        ("CONSOL ENERGY", 110000),
        ("PENN ENTERTAINMENT", 95000),
    ],
    "Appaloosa": [
        ("META PLATFORMS INC", 720000),
        ("MICROSOFT CORP", 540000),
        ("AMAZON.COM INC", 440000),
        ("ALIBABA GROUP ADR", 410000),
        ("UBER TECHNOLOGIES", 360000),
        ("CAESARS ENTERTAINMENT", 290000),
        ("NVIDIA CORP", 260000),
        ("TESLA INC", 230000),
        ("JD.COM ADR", 210000),
    ],
    "Baupost Group": [
        ("LIBERTY GLOBAL CL C", 320000),
        ("THERAVANCE BIOPHARMA", 110000),
        ("GARRETT MOTION", 95000),
        ("VERITONE INC", 32000),
        ("LIBERTY MEDIA SIRIUSXM", 280000),
    ],
    "ARK Investment Management": [
        ("TESLA INC", 1900000),
        ("COINBASE GLOBAL INC", 1100000),
        ("ROKU INC", 720000),
        ("BLOCK INC", 690000),
        ("PALANTIR TECHNOLOGIES", 540000),
        ("ROBINHOOD MARKETS", 410000),
        ("UIPATH INC", 280000),
        ("SHOPIFY INC", 240000),
    ],
    "Soros Fund Management": [
        ("AMAZON.COM INC", 460000),
        ("ALPHABET INC CL A", 380000),
        ("MICROSOFT CORP", 340000),
        ("APPLE INC", 280000),
        ("NVIDIA CORP", 220000),
        ("META PLATFORMS INC", 190000),
    ],
    "Viking Global Investors": [
        ("US FOODS HOLDING", 1100000),
        ("VISA INC", 980000),
        ("UNITEDHEALTH GROUP INC", 870000),
        ("MICROSOFT CORP", 760000),
        ("AMAZON.COM INC", 660000),
        ("WORKDAY INC", 540000),
        ("ELI LILLY & CO", 470000),
    ],
    "Lone Pine Capital": [
        ("MICROSOFT CORP", 1300000),
        ("META PLATFORMS INC", 1100000),
        ("AMAZON.COM INC", 950000),
        ("VISA INC", 760000),
        ("MASTERCARD INC", 720000),
        ("ALPHABET INC CL A", 620000),
        ("SERVICENOW INC", 540000),
    ],
    "Maverick Capital": [
        ("AMAZON.COM INC", 580000),
        ("META PLATFORMS INC", 470000),
        ("ALPHABET INC CL A", 420000),
        ("MICROSOFT CORP", 380000),
        ("NVIDIA CORP", 320000),
        ("APPLE INC", 260000),
    ],
    "Whale Rock Capital": [
        ("MICROSOFT CORP", 760000),
        ("META PLATFORMS INC", 690000),
        ("NVIDIA CORP", 540000),
        ("ADVANCED MICRO DEVICES", 410000),
        ("INTUIT INC", 320000),
        ("ASML HOLDING NV", 280000),
    ],
    "Duquesne Family Office": [
        ("NVIDIA CORP", 540000),
        ("MICROSOFT CORP", 410000),
        ("COUPANG INC", 320000),
        ("COHERENT CORP", 280000),
        ("TEVA PHARMACEUTICAL", 240000),
        ("ELI LILLY & CO", 220000),
        ("WILLIAMS COS", 190000),
    ],
    "Sequoia Capital Operations": [
        ("ALPHABET INC CL A", 1100000),
        ("MICROSOFT CORP", 760000),
        ("META PLATFORMS INC", 540000),
        ("AMAZON.COM INC", 420000),
        ("APPLE INC", 380000),
    ],
    "Tudor Investment": [
        ("APPLE INC", 320000),
        ("MICROSOFT CORP", 280000),
        ("NVIDIA CORP", 240000),
        ("META PLATFORMS INC", 210000),
        ("AMAZON.COM INC", 180000),
        ("BROADCOM INC", 150000),
    ],
    "Marshall Wace": [
        ("MICROSOFT CORP", 690000),
        ("APPLE INC", 540000),
        ("NVIDIA CORP", 470000),
        ("META PLATFORMS INC", 410000),
        ("ALPHABET INC CL A", 360000),
        ("AMAZON.COM INC", 320000),
        ("ELI LILLY & CO", 240000),
        ("UNITEDHEALTH GROUP INC", 210000),
    ],
}

REPORT_DATE = "2025-12-31"  # illustrative quarter


def main():
    out_dir = Path(__file__).parent

    raw = {}
    for fund, items in HOLDINGS.items():
        holdings = []
        for name, value in items:
            cusip = CUSIP.get(name)
            if not cusip:
                continue
            holdings.append({"name": name, "cusip": cusip, "value": value})
        raw[fund] = {
            "cik": "synthetic",
            "accession": "synthetic",
            "report_date": REPORT_DATE,
            "holdings": holdings,
        }

    by_cusip = defaultdict(lambda: {"name": "", "funds": [], "total_value": 0})
    for fund, info in raw.items():
        per_cusip = defaultdict(lambda: {"name": "", "value": 0})
        for h in info["holdings"]:
            slot = per_cusip[h["cusip"]]
            slot["name"] = h["name"]
            slot["value"] += h["value"]
        for cusip, slot in per_cusip.items():
            row = by_cusip[cusip]
            row["name"] = slot["name"]
            row["funds"].append({"fund": fund, "value": slot["value"]})
            row["total_value"] += slot["value"]

    records = []
    if not by_cusip:
        return
    max_holders = max(len(v["funds"]) for v in by_cusip.values())
    max_value = max(v["total_value"] for v in by_cusip.values())
    log_max_value = math.log10(max_value + 1)

    for cusip, info in by_cusip.items():
        n_holders = len(info["funds"])
        if n_holders < 2:
            continue
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
        "data_source": "synthetic-but-realistic (fetch_13f.py is the live EDGAR version)",
        "methodology": (
            "Crowding score = 0.6 * (n_holders / max_n_holders) + "
            "0.4 * (log10(total_value) / log10(max_total_value)), scaled 0-100. "
            "Only securities held by 2+ funds in the cohort are scored."
        ),
    }
    (out_dir / "crowding.json").write_text(json.dumps(output, indent=2))

    print(f"{len(records)} crowded names ranked across {len(raw)} funds.")
    print("Top 15:")
    for r in records[:15]:
        print(
            f"  {r['crowding_score']:5.1f}  "
            f"{r['n_holders']:2d} funds  "
            f"${r['total_value_thousands']/1e6:8.2f}B  "
            f"{r['name']}"
        )


if __name__ == "__main__":
    main()
