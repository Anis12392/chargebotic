---
name: feedback-google-suite
description: Always deliver outputs as Google Docs/Sheets/Slides, never as local Word/Excel/PowerPoint files
metadata:
  type: feedback
---

Always use Google Suite for all deliverables — Google Docs (not .docx), Google Slides (not .pptx), Google Sheets (not .xlsx).

**Why:** User explicitly corrected this. Also matches CLAUDE.md architecture rule: "Deliverables live in cloud services (Google Sheets, Slides, etc.) where the user can access them. Local files are only for processing intermediates."

**How to apply:** When generating any report, deck, or spreadsheet, the Python execution script must use the Google APIs (Docs, Slides, Sheets) to create and share the file in Google Drive — not save a local .docx/.pptx/.xlsx. The local .tmp/ folder is only for intermediate processing. Never deliver a local Office file as the final output.
