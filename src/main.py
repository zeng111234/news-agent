"""News Agent main entry - Automated news fetching and briefing generation"""
import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.config import config
from src.scraper import scrape_all_sources
from src.ai_processor import AINewsProcessor
from src.email_sender import EmailSender
from src.rule_manager import RuleManager
from datetime import datetime


def run_full_pipeline():
    """Run full workflow: fetch -> AI process -> email push"""
    print("=" * 60)
    print("  News Agent - Daily International News Briefing Generator")
    print("  Run time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

    if config.has_deepseek_config:
        print("  [OK] DeepSeek API: configured")
    else:
        print("  [WARN] DeepSeek API: not configured (will use basic filter mode)")

    if config.has_email_config:
        print("  [OK] Email service: configured")
        print("      Recipient: " + config.mail_to)
    else:
        print("  [WARN] Email service: not configured (results saved locally)")

    print()
    print("Step 1: Fetching news...")
    articles = scrape_all_sources()
    if not articles:
        print()
        print("[FAIL] No articles fetched, pipeline terminated")
        return False

    print()
    print("Raw data: " + str(len(articles)) + " articles")

    print()
    print("Step 2: AI processing...")
    processor = AINewsProcessor()
    try:
        briefing_content = processor.process_articles(articles)
    finally:
        processor.close()

    print()
    print("Step 3: Saving briefing...")
    today = datetime.now().strftime("%Y%m%d")
    history_dir = ROOT_DIR / "storage" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    md_path = history_dir / ("briefing_" + today + ".md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(briefing_content)
    print("  [OK] Briefing saved to: " + str(md_path))

    from src.email_sender import build_html_briefing
    html_content = build_html_briefing(briefing_content)
    html_path = history_dir / ("briefing_" + today + ".html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print("  [OK] HTML version saved to: " + str(html_path))

    if config.has_email_config:
        print()
        print("Step 4: Sending email...")
        sender = EmailSender()
        success = sender.send_briefing(briefing_content)
        if success:
            print()
            print("=" * 60)
            print("  Daily briefing generated and pushed successfully!")
            print("=" * 60)
        else:
            print()
            print("=" * 60)
            print("  [WARN] Briefing generated, but email push failed")
            print("  Please check email config in .env")
            print("=" * 60)
    else:
        print()
        print("Step 4: Skipping email push (not configured)")
        print("  Briefing file saved to: " + str(md_path))
        print("  Open HTML file to preview: " + str(html_path))
        print()
        print("=" * 60)
        print("  Briefing generated successfully!")
        print("  Configure .env to enable email push")
        print("=" * 60)

    return True


def run_interactive_mode():
    """Interactive mode - manage config via natural language"""
    manager = RuleManager()
    print()
    print("=" * 60)
    print("  Interactive Management Mode")
    print("  Enter commands to manage sources and filter rules")
    print("  Enter 'run' to execute a full briefing pipeline")
    print("  Enter 'help' for available commands")
    print("  Enter 'exit' or Ctrl+C to quit")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n> ").strip()
            if not user_input:
                continue

            if user_input in ("exit", "quit", "q"):
                print("Goodbye!")
                break

            if user_input in ("run", "run"):
                print()
                print("Starting briefing generation...")
                print()
                run_full_pipeline()
                continue

            result = manager.parse_and_execute(user_input)
            print()
            print(result)

        except KeyboardInterrupt:
            print()
            print("Goodbye!")
            break
        except Exception as e:
            print()
            print("[ERROR] " + str(e))


def main():
    """Main entry"""
    import argparse

    parser = argparse.ArgumentParser(
        description="News Agent - Daily News Briefing Automation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "mode",
        nargs="?",
        default="run",
        choices=["run", "interactive", "i"],
        help="Run mode: run (execute briefing), i (interactive management)",
    )

    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Skip email sending, save locally only",
    )

    args = parser.parse_args()

    if args.mode in ("interactive", "i"):
        run_interactive_mode()
    else:
        run_full_pipeline()


if __name__ == "__main__":
    main()
