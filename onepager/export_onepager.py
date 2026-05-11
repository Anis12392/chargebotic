"""Export chargebotic.com one-pager to a single A4 PDF with QR code + link at the bottom.
Injects CSS overrides to reduce spacing so the page fits at ~scale 1.0."""
import asyncio
import base64
import io
import qrcode
from playwright.async_api import async_playwright

FINAL_PDF = "/Users/cheriet/claude-code-official-memory/projects/chargebotic/chargebotic-onepager.pdf"
SITE_URL = "https://chargebotic.com"

A4_WIDTH = 794
A4_HEIGHT = 1123


def generate_qr_base64(url: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="white", back_color="transparent")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


async def main():
    qr_b64 = generate_qr_base64(f"{SITE_URL}/built.html")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": A4_WIDTH, "height": A4_HEIGHT})
        await page.goto(f"{SITE_URL}/deck/index.html", wait_until="networkidle")

        # Inject CSS to tighten spacing - targets the exact classes from the site
        await page.evaluate("""() => {
            const style = document.createElement('style');
            style.textContent = `
                body {
                    padding: 18px 30px 10px !important;
                }
                .header {
                    margin-bottom: 10px !important;
                }
                .hero {
                    padding: 14px 22px !important;
                    margin-bottom: 12px !important;
                }
                .thesis {
                    margin-bottom: 10px !important;
                }
                .thesis h2 {
                    margin-bottom: 4px !important;
                    font-size: 16px !important;
                }
                .thesis p {
                    font-size: 11px !important;
                    line-height: 1.5 !important;
                }
                .hypotheses {
                    gap: 8px !important;
                    margin-bottom: 10px !important;
                }
                .hypothesis {
                    padding: 10px 14px !important;
                }
                .hypothesis p {
                    font-size: 10px !important;
                    line-height: 1.4 !important;
                }
                .verticals {
                    margin-bottom: 10px !important;
                }
                .vertical-card {
                    padding: 8px 6px !important;
                }
                .vertical-card .v-icon {
                    font-size: 18px !important;
                    margin-bottom: 3px !important;
                }
                .market-bar {
                    gap: 8px !important;
                    margin-bottom: 10px !important;
                }
                .market-stat {
                    padding: 10px 12px !important;
                }
                .market-stat .number {
                    font-size: 20px !important;
                }
                .approach {
                    padding: 12px 18px !important;
                    margin-bottom: 10px !important;
                }
                .team {
                    margin-bottom: 10px !important;
                }
                .team-member {
                    padding: 10px 14px !important;
                }
                .footer {
                    padding-top: 8px !important;
                }
            `;
            document.head.appendChild(style);
        }""")

        # Remove existing CTA
        await page.evaluate("""() => {
            const existingLinks = document.querySelectorAll('a[href="built.html"]');
            existingLinks.forEach(el => {
                const parent = el.closest('div') || el.closest('section');
                if (parent && el.textContent.includes('Built')) {
                    parent.remove();
                }
            });
        }""")

        # Add QR + button at the bottom
        await page.evaluate(f"""() => {{
            const container = document.createElement('div');
            container.style.cssText = 'display:flex;align-items:center;justify-content:center;gap:14px;padding:8px 20px;margin-top:4px;';
            container.innerHTML = `
                <a href="{SITE_URL}/built.html" style="
                    display:inline-flex;align-items:center;padding:8px 24px;
                    background:#f97316;color:white;text-decoration:none;
                    border-radius:6px;font-size:14px;font-weight:600;
                    font-family:system-ui,sans-serif;
                ">See What We've Built &rarr;</a>
                <img src="data:image/png;base64,{qr_b64}"
                     style="width:60px;height:60px;border-radius:5px;" alt="QR Code" />
            `;
            document.body.appendChild(container);
        }}""")

        body_height = await page.evaluate("document.body.scrollHeight")
        print(f"Body height: {body_height}px (A4={A4_HEIGHT}px)")

        if body_height > A4_HEIGHT:
            scale = A4_HEIGHT / body_height
        else:
            scale = 1.0

        print(f"Scale: {scale:.2f}")

        await page.pdf(
            path=FINAL_PDF,
            format="A4",
            scale=scale,
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )

        await browser.close()

    from PyPDF2 import PdfReader
    reader = PdfReader(FINAL_PDF)
    print(f"PDF: {FINAL_PDF} — {len(reader.pages)} page(s)")


asyncio.run(main())
