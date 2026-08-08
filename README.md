# Daily News Brief – Automated PDF Generator

Professional 3-page daily news PDF:
- **Page 1**: Latest Tech / AI / Cybersecurity
- **Page 2**: 5 Trending stories from India
- **Page 3**: 5 Trending global stories

Fully automated via GitHub Actions (free).

---

## Quick Start (5–7 minutes)

### 1. Create a new GitHub repository
Go to https://github.com/new → create a private or public repo (e.g. `daily-news-brief`)

### 2. Upload these files
Copy the entire content of this folder into your new repository:

```
daily-news-automation/
├── .github/
│   └── workflows/
│       └── daily-news.yml
├── src/
│   └── daily_news_pdf.py
├── requirements.txt
└── README.md
```

You can drag-and-drop the files on GitHub or use git.

### 3. Enable GitHub Actions
- Go to the **Actions** tab of your repo
- Click “I understand my workflows, enable them” if prompted

### 4. Test it manually
- Go to **Actions** → **Daily News Brief PDF** → **Run workflow** → Run
- Wait 1–2 minutes
- Download the PDF from the **Artifacts** section

### 5. Automatic schedule
The workflow already runs every day at **07:00 IST** (01:30 UTC).  
You will find the PDF under:
- Actions → latest run → Artifacts
- Or in the `latest/Daily_News_Brief_Latest.pdf` file inside the repo (if commit step succeeds)

---

## Optional Delivery Methods (Email / Telegram / Google Drive)

### A. Email the PDF every morning

1. Create a Gmail App Password (or use any SMTP)
2. In your GitHub repo → **Settings** → **Secrets and variables** → **Actions**
3. Add secrets:
   - `EMAIL_USERNAME` → your email
   - `EMAIL_PASSWORD` → app password
4. Uncomment the “Send PDF via Email” step in `.github/workflows/daily-news.yml`
5. Change the `to:` address

### B. Send to Telegram

1. Create a bot with @BotFather → get token
2. Get your chat_id (message the bot, then visit `https://api.telegram.org/bot<token>/getUpdates`)
3. Add secrets:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. Uncomment the Telegram step

### C. Google Drive

Requires a Google Cloud service account. More setup — ask if you need the full guide.

---

## Local Testing (optional)

```bash
# Install
pip install -r requirements.txt

# Run
python src/daily_news_pdf.py
```

The PDF will appear in the current folder.

---

## Customization

| What you want to change          | Where to edit                          |
|----------------------------------|----------------------------------------|
| News sources (RSS feeds)         | `src/daily_news_pdf.py` → `FEEDS` dict |
| Number of stories                | `MAX_ITEMS_PER_SECTION`                |
| Run time                         | `.github/workflows/daily-news.yml` → cron |
| Colors / design                  | Color constants + TableStyle           |
| Add more sections                | Extend the script                      |

---

## Dark Side Notes (Read This)

- Free GitHub Actions has monthly minutes limits (private repos have less). For one daily job this is almost never a problem.
- RSS feeds can change or break. The script is resilient but not 100% bulletproof.
- This does **not** run inside Grok. It runs on GitHub’s servers and delivers the PDF to you.
- If you want even higher quality news ranking, you can later add NewsAPI.org (paid free tier available) or LLM-based ranking.

---

## Need Help?

Just reply with:
- “Help me set up email delivery”
- “Help me set up Telegram”
- “Make the script use NewsAPI”
- “Change the design”

You now have a production-grade daily news system.
