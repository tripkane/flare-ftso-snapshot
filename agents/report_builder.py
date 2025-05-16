
def build_report(analysis_results):
    report = "# FTSO Snapshot Report\n\n"
    if not analysis_results:
        report += "No alerts or anomalies detected.\n"
    for entry in analysis_results:
        report += f"- **{entry['provider']}**: {entry['status']} ({entry['rate']:.2f}%)\n"
    return report
