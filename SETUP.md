# Quick Setup Guide - NYC Movie Screening Automation

Follow these 5 simple steps to set up your automated weekly movie screening emails.

## Step 1: Get SendGrid API Key (5 minutes)

1. Sign up at [SendGrid.com](https://sendgrid.com/) (free account)
2. Go to **Settings** → **API Keys** → **Create API Key**
3. Name it "NYC Movie Screenings", select **Full Access**
4. **Copy the API key** (you won't see it again!)
5. Go to **Settings** → **Sender Authentication** → **Verify a Single Sender**
6. Enter your email and verify it (check your inbox for verification link)

## Step 2: (Optional) Get Reddit Credentials (3 minutes)

This adds community-posted screenings from r/NYCmovies.

1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Click **create another app...**
3. Name: "NYC Movie Scraper", Type: **script**, Redirect: http://localhost:8080
4. Copy the **client ID** and **secret**

## Step 3: Add Secrets to GitHub (2 minutes)

1. In your GitHub repo, go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** for each:

   **Required:**
   - Name: `SENDGRID_API_KEY` → Value: [paste your SendGrid key]

   **Optional:**
   - Name: `REDDIT_CLIENT_ID` → Value: [paste Reddit client ID]
   - Name: `REDDIT_CLIENT_SECRET` → Value: [paste Reddit secret]

## Step 4: Enable GitHub Actions (1 minute)

1. Go to **Actions** tab in your repository
2. If needed, click **Enable workflows**

## Step 5: Test It! (1 minute)

1. In **Actions** tab, click **Weekly NYC Movie Screening Email**
2. Click **Run workflow** → **Run workflow**
3. Wait ~1 minute, check your email inbox (and spam folder!)

✅ **Done!** If you got the email, the system is now fully automated and will run every Monday at 8am EST.

---

## What Happens Next?

- Every Monday at 8am EST, GitHub automatically runs the scraper
- You'll receive a beautifully formatted email with all special NYC screenings
- No manual action needed - it's completely hands-off!

## Need Help?

See the full [README.md](README.md) for:
- Troubleshooting
- Customization options
- Detailed documentation
- Local testing instructions

---

**Total setup time: ~12 minutes** ⏱️

**Total cost: $0** 💰

**Weekly effort: 0 minutes** ✨
