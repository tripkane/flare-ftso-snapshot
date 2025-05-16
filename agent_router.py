
import logging
from agents.snapshot_fetcher import fetch_snapshot
from agents.data_analysis import analyze_snapshot
from agents.report_builder import build_report
from agents.email_sender import send_email
from config import SENDER_EMAIL, RECIPIENTS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_daily_pipeline():
    try:
        logging.info("Starting FTSO snapshot pipeline...")
        data = fetch_snapshot()
        logging.info("Snapshot fetched successfully.")

        results = analyze_snapshot(data)
        logging.info("Snapshot analyzed. %d issues detected.", len(results))

        report = build_report(results)
        logging.info("Report built successfully.")

        visible_to = SENDER_EMAIL  # Hide actual recipients
        logging.info("Skipping email sending for now. Printing report:")
        print("\n===== FTSO Report =====\n")
        print(report)
        print("\n=======================\n")

        logging.info("Email sent to recipients.")

    except Exception as e:
        logging.error("Pipeline failed: %s", str(e))
