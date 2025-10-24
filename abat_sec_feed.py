import requests, datetime
from xml.etree.ElementTree import Element, SubElement, tostring

# ===== CONFIG =====
CIK = "0001576873"  # ABAT
OUTPUT_FILE = "abat_sec_filings.xml"
SEC_JSON_URL = f"https://data.sec.gov/submissions/CIK{CIK}.json"

# IMPORTANT: Put a real contact in the User-Agent per SEC guidance.
HEADERS = {
    "User-Agent": "YourName/1.0 your-email@example.com"
}

# ===== FETCH SEC JSON =====
r = requests.get(SEC_JSON_URL, headers=HEADERS, timeout=30)
r.raise_for_status()
data = r.json()
recent = data["filings"]["recent"]

forms = recent["form"]
dates = recent["filingDate"]
accessions = recent["accessionNumber"]
descriptions = recent.get("primaryDocDescription", [])
reports = recent.get("reportDate", [])

# ===== BUILD RSS =====
root = Element("rss", version="2.0")
channel = SubElement(root, "channel")

company_name = data.get("name", "Company")
SubElement(channel, "title").text = f"{company_name} SEC Filings (10-K, 10-Q, 8-K)"
SubElement(channel, "link").text = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={CIK}"
SubElement(channel, "description").text = f"Auto-updating SEC filings feed for {company_name}"
SubElement(channel, "lastBuildDate").text = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

def make_link(cik, accession_with_dashes):
    # SEC folder path removes dashes in the folder component, but the file keeps dashes + '-index.htm'
    folder = accession_with_dashes.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{folder}/{accession_with_dashes}-index.htm"

for i in range(len(forms)):
    form = forms[i]
    if form not in ["10-K", "10-Q", "8-K"]:
        continue

    accession = accessions[i]
    link = make_link(CIK, accession)
    desc = descriptions[i] if i < len(descriptions) and descriptions[i] else "SEC filing"
    rpt = reports[i] if i < len(reports) and reports[i] else "N/A"
    filed = dates[i]

    item = SubElement(channel, "item")
    SubElement(item, "title").text = f"{form} — {desc}"
    SubElement(item, "link").text = link
    # pubDate should be RFC 2822; the SEC gives YYYY-MM-DD, which most readers accept.
    SubElement(item, "pubDate").text = filed
    SubElement(item, "description").text = f"Report date: {rpt}"

rss_xml = tostring(root, encoding="utf-8", method="xml")

with open(OUTPUT_FILE, "wb") as f:
    f.write(rss_xml)

print(f"✅ RSS feed saved as {OUTPUT_FILE}")
