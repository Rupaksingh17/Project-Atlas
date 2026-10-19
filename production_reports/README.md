# Authorized report corpus

Place only reports that your organization is licensed to use here. The deployment reads Markdown and PDF files. Markdown reports should include these metadata lines so ingestion can register them in MySQL:

```markdown
# Report title
**Report ID:** R-201
**Publisher:** Publisher name
**Publication Date:** 2026-01-15
**Sector:** Utilities
**Access:** paid

<!-- Page 1 -->
Page text...
```

Use `**Access:** public excerpt` only for material approved for public access. After adding or updating reports, call the authenticated `POST /ingest` endpoint. Add each customer's report entitlements to the `clients.purchased_reports` column through your organization's trusted client provisioning process.

For PDF files, add a same-name JSON sidecar. For example, `R-201_market-outlook.pdf` must have `R-201_market-outlook.json` containing:

```json
{
  "report_id": "R-201",
  "title": "Market Outlook",
  "publisher": "Publisher name",
  "published": "2026-01-15",
  "sector": "Utilities",
  "access": "paid"
}
```

The ingestion pipeline extracts text page by page. Scanned image-only PDFs need OCR before ingestion.

Do not place synthetic assignment reports or unlicensed third-party content in this directory.
