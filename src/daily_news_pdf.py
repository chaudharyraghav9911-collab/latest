#!/usr/bin/env python3
"""
Daily News Brief PDF Generator (Advanced Edition)
Generates a professional 3-page PDF:
  Page 1 → Tech / AI / Cybersecurity
  Page 2 → India Trending (5 stories)
  Page 3 → Global Trending (5 stories)

Designed for GitHub Actions / cron / local scheduled runs.
"""

import os
import sys
import feedparser
import requests
from datetime import datetime, timezone
from dateutil import parser as date_parser
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional

# ====================== CONFIG ======================
OUTPUT_DIR = os.getenv("OUTPUT_DIR", ".")
MAX_ITEMS_PER_SECTION = 5

# RSS Feeds (no API key required)
FEEDS = {
    "tech_ai_cyber": [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "https://www.wired.com/feed/tag/ai/latest/rss",
        "https://krebsonsecurity.com/feed/",
        "https://www.bleepingcomputer.com/feed/",
        "https://thehackernews.com/feeds/posts/default",
        "https://www.darkreading.com/rss.xml",
    ],
    "india": [
        "https://indianexpress.com/section/india/feed/",
        "https://www.thehindu.com/news/national/feeder/default.rss",
        "https://feeds.feedburner.com/ndtvnews-india-news",
        "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
        "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
    ],
    "global": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://www.theguardian.com/world/rss",
    ],
}

# Colors
HEADER_BG = HexColor("#1e293b")
ACCENT_BLUE = HexColor("#3b82f6")
ACCENT_CYAN = HexColor("#06b6d4")
ACCENT_GREEN = HexColor("#10b981")
ACCENT_ORANGE = HexColor("#f59e0b")
ACCENT_RED = HexColor("#ef4444")
MED_GRAY = HexColor("#64748b")
DARK_TEXT = HexColor("#1e293b")
CARD_BG = HexColor("#ffffff")
LIGHT_BORDER = HexColor("#e2e8f0")


def clean_html(raw_html: str) -> str:
    """Strip HTML tags and clean text."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "lxml")
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def truncate(text: str, max_len: int = 320) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rsplit(" ", 1)[0] + "..."


def parse_date(entry) -> Optional[datetime]:
    """Best-effort date parsing from feed entry."""
    for key in ("published", "updated", "created"):
        if hasattr(entry, key) and getattr(entry, key):
            try:
                return date_parser.parse(getattr(entry, key))
            except Exception:
                continue
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        except Exception:
            pass
    return None


def fetch_feed(url: str, timeout: int = 12) -> List[Dict]:
    """Fetch and parse a single RSS/Atom feed."""
    items = []
    try:
        # Some feeds need a user-agent
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; DailyNewsBot/1.0; +https://github.com)"
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)

        for entry in feed.entries[:8]:  # take a few extra, we will rank later
            title = clean_html(getattr(entry, "title", "") or "")
            summary = clean_html(
                getattr(entry, "summary", "")
                or getattr(entry, "description", "")
                or ""
            )
            link = getattr(entry, "link", "") or ""
            published = parse_date(entry)

            if not title:
                continue

            items.append({
                "title": title,
                "summary": truncate(summary, 340),
                "link": link,
                "published": published,
                "source": feed.feed.get("title", url.split("/")[2]),
            })
    except Exception as e:
        print(f"[WARN] Failed to fetch {url}: {e}", file=sys.stderr)
    return items


def collect_news(section: str) -> List[Dict]:
    """Collect, deduplicate and rank news for a section."""
    all_items = []
    for url in FEEDS.get(section, []):
        all_items.extend(fetch_feed(url))

    # Deduplicate by similar titles
    seen = set()
    unique = []
    for item in all_items:
        key = re.sub(r"[^a-z0-9]", "", item["title"].lower())[:60]
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    # Sort by recency (newest first)
    unique.sort(
        key=lambda x: x["published"] or datetime(1970, 1, 1, tzinfo=timezone.utc),
        reverse=True,
    )
    return unique[:MAX_ITEMS_PER_SECTION]


def create_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="PageHeader",
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=DARK_TEXT,
        alignment=TA_LEFT,
        spaceBefore=4,
        spaceAfter=6,
        leading=19,
    ))

    styles.add(ParagraphStyle(
        name="NewsTitle",
        fontName="Helvetica-Bold",
        fontSize=9.5,
        textColor=DARK_TEXT,
        alignment=TA_LEFT,
        spaceBefore=1,
        spaceAfter=2,
        leading=12,
    ))

    styles.add(ParagraphStyle(
        name="NewsBody",
        fontName="Helvetica",
        fontSize=8.2,
        textColor=MED_GRAY,
        alignment=TA_JUSTIFY,
        spaceAfter=3,
        leading=10.5,
    ))

    styles.add(ParagraphStyle(
        name="SourceTag",
        fontName="Helvetica",
        fontSize=7,
        textColor=ACCENT_BLUE,
        alignment=TA_LEFT,
        spaceAfter=2,
    ))

    styles.add(ParagraphStyle(
        name="SectionLabel",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=white,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name="Footer",
        fontName="Helvetica",
        fontSize=7.5,
        textColor=MED_GRAY,
        alignment=TA_CENTER,
    ))

    return styles


def add_header_footer(canvas, doc):
    canvas.saveState()
    page_w, page_h = A4

    # Top bar
    canvas.setFillColor(HEADER_BG)
    canvas.rect(0, page_h - 20 * mm, page_w, 20 * mm, fill=1, stroke=0)

    canvas.setFillColor(ACCENT_CYAN)
    canvas.rect(0, page_h - 21 * mm, page_w, 1.1 * mm, fill=1, stroke=0)

    canvas.setFillColor(white)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(14 * mm, page_h - 11 * mm, "DAILY NEWS BRIEF")

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(HexColor("#94a3b8"))
    today = datetime.now().strftime("%A, %d %B %Y")
    canvas.drawRightString(page_w - 14 * mm, page_h - 11 * mm, today)

    # Bottom bar
    canvas.setFillColor(HEADER_BG)
    canvas.rect(0, 0, page_w, 11 * mm, fill=1, stroke=0)

    canvas.setFillColor(HexColor("#94a3b8"))
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(
        page_w / 2,
        4 * mm,
        f"Page {doc.page} of 3  •  Auto-generated  •  Stay informed. Stay ahead."
    )
    canvas.restoreState()


def news_card(title: str, body: str, source: str, styles, accent):
    title_p = Paragraph(f"<b>{title}</b>", styles["NewsTitle"])
    body_p = Paragraph(body or "No summary available.", styles["NewsBody"])
    source_p = Paragraph(f"Source: {source}", styles["SourceTag"])

    data = [[title_p], [body_p], [source_p]]
    t = Table(data, colWidths=[172 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (0, 0), 5),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 3),
        ("BOX", (0, 0), (-1, -1), 0.4, LIGHT_BORDER),
        ("LINEBEFORE", (0, 0), (0, -1), 2.8, accent),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return [t, Spacer(1, 3.2 * mm)]


def build_section_header(text: str, color, styles):
    data = [[Paragraph(text, styles["SectionLabel"])]]
    t = Table(data, colWidths=[186 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("TOPPADDING", (0, 0), (-1, -1), 5.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5.5),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    return [t, Spacer(1, 4.5 * mm)]


def generate_pdf(output_path: str):
    print("[INFO] Collecting news...")
    tech_items = collect_news("tech_ai_cyber")
    india_items = collect_news("india")
    global_items = collect_news("global")

    print(f"[INFO] Tech/AI/Cyber: {len(tech_items)} | India: {len(india_items)} | Global: {len(global_items)}")

    styles = create_styles()
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=26 * mm,
        bottomMargin=15 * mm,
    )

    story = []

    # ---------- PAGE 1 : TECH / AI / CYBER ----------
    story.extend(build_section_header("TECH • AI • CYBERSECURITY", ACCENT_BLUE, styles))
    accents = [ACCENT_RED, ACCENT_ORANGE, ACCENT_CYAN, ACCENT_RED, ACCENT_ORANGE]
    for i, item in enumerate(tech_items):
        story.extend(news_card(
            f"{i+1}. {item['title']}",
            item["summary"],
            item.get("source", "Unknown"),
            styles,
            accents[i % len(accents)],
        ))
    if not tech_items:
        story.append(Paragraph("No recent items found.", styles["NewsBody"]))

    story.append(PageBreak())

    # ---------- PAGE 2 : INDIA ----------
    story.extend(build_section_header("INDIA — 5 TRENDING STORIES", ACCENT_ORANGE, styles))
    accents_in = [ACCENT_RED, ACCENT_CYAN, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_BLUE]
    for i, item in enumerate(india_items):
        story.extend(news_card(
            f"{i+1}. {item['title']}",
            item["summary"],
            item.get("source", "Unknown"),
            styles,
            accents_in[i % len(accents_in)],
        ))
    if not india_items:
        story.append(Paragraph("No recent items found.", styles["NewsBody"]))

    story.append(PageBreak())

    # ---------- PAGE 3 : GLOBAL ----------
    story.extend(build_section_header("WORLD — 5 TRENDING STORIES", ACCENT_GREEN, styles))
    accents_gl = [ACCENT_CYAN, ACCENT_RED, ACCENT_RED, ACCENT_ORANGE, ACCENT_BLUE]
    for i, item in enumerate(global_items):
        story.extend(news_card(
            f"{i+1}. {item['title']}",
            item["summary"],
            item.get("source", "Unknown"),
            styles,
            accents_gl[i % len(accents_gl)],
        ))
    if not global_items:
        story.append(Paragraph("No recent items found.", styles["NewsBody"]))

    print(f"[INFO] Building PDF → {output_path}")
    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    print("[SUCCESS] PDF generated successfully.")
    return output_path


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"Daily_News_Brief_{today}.pdf"
    output_path = os.path.join(OUTPUT_DIR, filename)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    generate_pdf(output_path)
    print(f"\n✅ File ready: {output_path}")


if __name__ == "__main__":
    main()
