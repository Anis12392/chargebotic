# Directive: CRM Dashboard

## Purpose
Scan Gmail to extract all investor, product-interest, partner, and media contacts into a Google Sheet ("Powerbird CRM"). Gives a live count of who's in the pipeline and when they were last contacted.

## Script
`execution/scan_crm.py`

## Run
```bash
python3 execution/scan_crm.py
```

## First-time setup (one-time)
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create project → Enable **Gmail API** and **Google Sheets API** and **Google Drive API**
3. OAuth 2.0 → Desktop App → Download JSON → save as `credentials.json` in project root
4. Run script once → browser opens for auth → `token.json` generated automatically
5. All future runs use `token.json` (no browser needed)

## Output (Google Sheets)
- **CRM tab:** Name | Email | Company | Category | Last Contact | Last Subject | Status | Notes
- **Summary tab:** total count + breakdown by category

## Categories (priority order)
1. Investor
2. Product Interest
3. Partner / Supplier
4. Media
5. Discovery Call

## Update frequency
Run manually before important meetings or weekly to refresh the sheet.

## Known contacts (pre-seeded by scan)
- Antoine Moyroud — Lightspeed Venture Partners — Investor
- Christian Keil — a16z American Dynamism — Investor
- Ed (Virtus Solis) — Partner interest — May 2026
- Avery Schmitz — CNN — Media
- Daniele — Cognivix — Product Interest
- Alex Burkardt — Lowercase Capital — Product Interest
- Steve Macenski — OpenNav — Partner / Advisor
- Luke Liu — Longsing Technology — Partner / Supplier

## Edge cases
- Script skips internal emails (anis@, bo@, cherietcompte@)
- Skips newsletters, calendly notifications, otter.ai, etc.
- If a contact appears in multiple categories, highest-priority category wins
- Subject lines truncated to 100 chars in sheet
