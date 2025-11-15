#!/usr/bin/env python3
"""
NYC Movie Screening Weekly Email Automation
Automatically scrapes and sends weekly digests of special movie screenings in NYC
"""
import sys
from aggregator import ScreeningAggregator
from llm_formatter import LLMFormatter
from email_sender import EmailSender
from datetime import datetime


def main():
    """Main function to run the screening aggregation and email sending"""
    print("=" * 60)
    print("NYC MOVIE SCREENING WEEKLY DIGEST")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Step 1: Collect screenings
    print("📡 STEP 1: Collecting screenings from all sources...")
    print("-" * 60)
    aggregator = ScreeningAggregator()
    all_screenings = aggregator.collect_all_screenings()

    if not all_screenings:
        print("\n⚠️  No screenings found from any source.")
        print("This could mean:")
        print("  - Websites are temporarily unavailable")
        print("  - Site structures have changed")
        print("  - Network issues")
        # Continue anyway to send an email notifying of the issue
    else:
        print(f"\n✓ Collected {len(all_screenings)} total screenings")

    # Step 2: Filter and deduplicate
    print("\n🔍 STEP 2: Filtering and deduplicating...")
    print("-" * 60)
    filtered_screenings = aggregator.filter_and_deduplicate(all_screenings)
    print(f"✓ {len(filtered_screenings)} unique special screenings after filtering")

    # Step 3: Sort and group
    print("\n📊 STEP 3: Sorting and grouping...")
    print("-" * 60)
    sorted_screenings = aggregator.sort_screenings(filtered_screenings)
    grouped_screenings = aggregator.group_by_theater(sorted_screenings)
    print(f"✓ Grouped into {len(grouped_screenings)} theaters")

    # Step 4: Format email with LLM
    print("\n✉️  STEP 4: Formatting email with LLM...")
    print("-" * 60)
    formatter = LLMFormatter()
    subject, html_body = formatter.format_with_llm(grouped_screenings)
    print(f"✓ Email formatted with LLM-generated story")
    print(f"  Subject: {subject}")
    print(f"  Content length: {len(html_body)} characters")

    # Optional: Save HTML for debugging
    try:
        with open('last_email.html', 'w', encoding='utf-8') as f:
            f.write(html_body)
        print(f"  ✓ Saved copy to last_email.html for preview")
    except Exception as e:
        print(f"  ⚠️  Could not save HTML preview: {e}")

    # Step 5: Send email
    print("\n📧 STEP 5: Sending email...")
    print("-" * 60)
    try:
        sender = EmailSender()
        success = sender.send_email(subject, html_body)

        if success:
            print("\n" + "=" * 60)
            print("✓ SUCCESS! Weekly digest sent successfully!")
            print("=" * 60)
            print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return 0
        else:
            print("\n" + "=" * 60)
            print("✗ FAILED: Email could not be sent")
            print("=" * 60)
            return 1

    except Exception as e:
        print(f"\n✗ Error sending email: {e}")
        print("\nPlease check:")
        print("  - SENDGRID_API_KEY is set correctly in GitHub Secrets")
        print("  - SendGrid account is active and has send permissions")
        print("  - Sender email is verified in SendGrid")
        return 1


if __name__ == "__main__":
    sys.exit(main())
