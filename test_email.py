#!/usr/bin/env python3
"""
Test script to verify email configuration
Run this manually to test that SendGrid is set up correctly
"""
import sys
from email_sender import EmailSender


def main():
    """Send a test email to verify configuration"""
    print("=" * 60)
    print("NYC MOVIE SCREENING - EMAIL TEST")
    print("=" * 60)
    print("\nThis will send a test email to verify your SendGrid setup.\n")

    try:
        sender = EmailSender()
        print(f"Sending test email to: {sender.recipient_email}\n")

        success = sender.send_test_email()

        if success:
            print("\n" + "=" * 60)
            print("✓ SUCCESS! Test email sent!")
            print("=" * 60)
            print("\nCheck your inbox (and spam folder) for the test email.")
            print("If you received it, your setup is complete!")
            return 0
        else:
            print("\n" + "=" * 60)
            print("✗ FAILED: Could not send test email")
            print("=" * 60)
            print("\nTroubleshooting:")
            print("1. Check that SENDGRID_API_KEY is set correctly")
            print("2. Verify your SendGrid account is active")
            print("3. Make sure sender email is verified in SendGrid")
            return 1

    except ValueError as e:
        print(f"\n✗ Configuration Error: {e}")
        print("\nMake sure you've set the SENDGRID_API_KEY environment variable:")
        print("  export SENDGRID_API_KEY='your-api-key-here'")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
