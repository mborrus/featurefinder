# NYC Movie Screening Weekly Email Automation 🎬

A fully automated system that scrapes NYC special movie screenings and sends you a curated weekly email digest every Monday morning at 8am EST.

## Features

- **Fully Automated**: Runs automatically in GitHub's cloud every Monday at 8am EST
- **Comprehensive Coverage**: Scrapes multiple sources including:
  - Screenslate.com (NYC film screening aggregator)
  - Film Forum, IFC Center, Metrograph (repertory theaters)
  - Time Out NYC film events
  - Reddit r/NYCmovies community
  - And more!
- **Smart Filtering**: Only includes special screenings:
  - IMAX and premium format releases
  - Q&As and director appearances
  - Premieres and advance screenings
  - Repertory/classic film screenings
  - Festival screenings and special series
- **AI-Powered Content Pipeline**: Uses Claude to generate engaging narratives and structure screening data
- **Beautiful HTML Emails**: Professionally formatted with intelligent organization and visual appeal
- **Zero Maintenance**: Set it up once and forget about it

## How It Works

1. Every Monday at 8am EST, GitHub Actions automatically runs the script
2. The script scrapes all configured sources for upcoming screenings
3. It filters out regular wide releases and focuses on special events
4. Claude AI analyzes the screening data and creates an engaging narrative story
5. The content is formatted into a beautiful HTML email
6. The email is sent to your inbox via SendGrid
7. You get your curated, intelligently-written weekly digest without lifting a finger!

## Setup Instructions

Follow these steps to get your automated system running:

### Step 1: Get API Keys

**Anthropic (Claude) API Key:**
1. Go to [console.anthropic.com](https://console.anthropic.com/) and sign up for an account
2. Navigate to **API Keys** in the console
3. Click **Create Key**
4. Give it a name (e.g., "NYC Movie Screenings")
5. **IMPORTANT**: Copy the API key immediately (you won't see it again!)
6. **Note**: Anthropic offers $5 free credits for new accounts.

**SerpAPI Key (Optional - for AMC theaters):**
1. Go to [serpapi.com](https://serpapi.com/) and sign up for an account
2. Navigate to your **API Key** in the dashboard
3. Copy your API key
4. **Note**: SerpAPI offers a free tier with 100 searches/month. AMC scraping uses ~2 searches per run (once weekly = ~8/month), well within the free tier.
5. If not configured, AMC theaters will be skipped (other theaters will still work)

### Step 2: Get a SendGrid API Key (Free)

SendGrid offers a free tier with 100 emails/day, which is more than enough.

1. Go to [SendGrid.com](https://sendgrid.com/) and sign up for a free account
2. Verify your email address
3. In SendGrid dashboard, go to **Settings** → **API Keys**
4. Click **Create API Key**
   - Name: `NYC Movie Screenings`
   - Permissions: Select **Full Access** (or at minimum **Mail Send**)
5. **IMPORTANT**: Copy the API key immediately (you won't see it again!)
6. **Verify your sender email**:
   - Go to **Settings** → **Sender Authentication**
   - Click **Verify a Single Sender**
   - Enter your email (can be any email you control)
   - Check that email and click the verification link

### Step 3: (Optional) Get Reddit API Credentials

This is optional but recommended to get community-posted screening events.

1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Scroll down and click **create another app...**
3. Fill in:
   - **name**: NYC Movie Scraper
   - **type**: Select **script**
   - **description**: Personal movie screening scraper
   - **redirect uri**: http://localhost:8080
4. Click **create app**
5. Copy the **client ID** (under the app name) and **secret**

### Step 4: Add Secrets to GitHub

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add:

   **Required:**
   - Name: `ANTHROPIC_API_KEY`
   - Value: Paste your Anthropic API key

   - Name: `SENDGRID_API_KEY`
   - Value: Paste your SendGrid API key

   **Optional (but recommended):**
   - Name: `SERPAPI_KEY`
   - Value: Your SerpAPI key (enables AMC theater scraping)

   - Name: `REDDIT_CLIENT_ID`
   - Value: Your Reddit app client ID (deprecated, but kept for compatibility)

   - Name: `REDDIT_CLIENT_SECRET`
   - Value: Your Reddit app secret (deprecated, but kept for compatibility)

### Step 5: Enable GitHub Actions

1. In your repository, go to the **Actions** tab
2. If prompted, click **I understand my workflows, go ahead and enable them**
3. You should see the workflow "Weekly NYC Movie Screening Email" listed

### Step 6: Test It!

Before waiting until Monday, test that everything works:

1. Go to **Actions** tab in your GitHub repository
2. Click on **Weekly NYC Movie Screening Email** workflow
3. Click **Run workflow** button on the right
4. Click the green **Run workflow** button in the dropdown
5. Wait a minute, then refresh - you should see a workflow run in progress
6. Click on the run to see detailed logs
7. Check your email inbox (and spam folder!) for the digest

If the test succeeds, you're all set! The system will now run automatically every Monday at 8am EST.

## Project Structure

```
featurefinder/
├── .github/
│   └── workflows/
│       └── weekly-screening-email.yml  # GitHub Actions workflow
├── scrapers/
│   ├── __init__.py
│   ├── base.py                          # Base scraper class
│   ├── screenslate.py                   # Screenslate.com scraper
│   ├── reddit.py                        # Reddit r/NYCmovies scraper
│   ├── timeout_nyc.py                   # Time Out NYC scraper
│   ├── film_forum.py                    # Film Forum scraper
│   ├── ifc_center.py                    # IFC Center scraper
│   └── metrograph.py                    # Metrograph scraper
├── aggregator.py                        # Collects and filters screenings
├── llm_formatter.py                     # AI-powered story formatting
├── email_formatter.py                   # Legacy HTML email formatter
├── email_sender.py                      # Sends emails via SendGrid
├── config.py                            # Configuration
├── main.py                              # Main entry point
├── test_email.py                        # Test script
├── requirements.txt                     # Python dependencies
└── README.md                            # This file
```

## Customization

### Change Email Address

Edit `config.py` and change:
```python
RECIPIENT_EMAIL = "your-email@gmail.com"
```

### Change Schedule

Edit `.github/workflows/weekly-screening-email.yml` and modify the cron expression:
```yaml
schedule:
  - cron: '0 13 * * 1'  # Every Monday at 1pm UTC (8am EST)
```

Cron format: `minute hour day month day-of-week`

Examples:
- `0 13 * * 1` - Every Monday at 8am EST
- `0 13 * * 3` - Every Wednesday at 8am EST
- `0 17 * * 5` - Every Friday at noon EST

Use [crontab.guru](https://crontab.guru/) to build custom schedules.

### Add More Theaters

Edit `config.py` and add theaters to the `THEATERS` dictionary:
```python
THEATERS = {
    'Your Theater Name': {
        'url': 'https://theater-website.com',
        'location': 'Manhattan',
        'priority': 2
    },
    # ... existing theaters
}
```

Then create a new scraper in `scrapers/` following the pattern of existing scrapers.

## Troubleshooting

### Email Not Arriving

1. **Check spam folder** - First time emails often go to spam
2. **Verify sender email** - Make sure you verified your sender email in SendGrid
3. **Check GitHub Actions logs**:
   - Go to Actions tab
   - Click on the most recent workflow run
   - Check the logs for errors
4. **Check SendGrid dashboard** - Look at Activity Feed to see if emails are being sent

### GitHub Actions Not Running

1. **Make sure Actions are enabled** in your repository settings
2. **Check if the workflow file is on your default branch** (usually `main` or `master`)
3. **Manually trigger** a test run from the Actions tab

### No Screenings Found

This can happen if:
- Websites have changed their structure (scrapers may need updates)
- No special screenings are scheduled for that week
- Network issues during scraping

The system will still send an email notifying you that no screenings were found.

### API Rate Limits

If you hit rate limits:
- Reddit: The free tier should be sufficient for weekly runs
- SendGrid: Free tier includes 100 emails/day

## Local Testing

To test locally on your computer:

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables:
   ```bash
   export ANTHROPIC_API_KEY='your-anthropic-key-here'
   export GEMINI_API_KEY='your-gemini-key-here'
   export SENDGRID_API_KEY='your-sendgrid-key-here'
   export REDDIT_CLIENT_ID='your-id-here'  # optional
   export REDDIT_CLIENT_SECRET='your-secret-here'  # optional
   ```

4. Run test email:
   ```bash
   python test_email.py
   ```

5. Run full scraping and email:
   ```bash
   python main.py
   ```

## Costs

**Very Low Cost!**

- GitHub Actions: Free for public repositories, 2000 minutes/month for private
- SendGrid: Free tier includes 100 emails/day
- Reddit API: Free
- SerpAPI: Free tier includes 100 searches/month (uses ~8/month for weekly runs)
- Anthropic API (Claude): $5 free credits for new accounts, ~$0.01-0.02 per email
- This automation uses less than 5 minutes/week of GitHub Actions

**Total estimated cost**: Free for the first ~250-500 emails (using free tier credits), then approximately $0.50-1.00 per year for weekly emails.

## Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Review GitHub Actions logs for detailed error messages
3. Make sure all secrets are set correctly in GitHub
4. Verify your SendGrid sender email is verified

## License

MIT License - Feel free to modify and use as you wish!

---

**Enjoy your automated weekly NYC movie screening digest!** 🎬🍿

make default
