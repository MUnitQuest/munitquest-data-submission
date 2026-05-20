"""
After validation (BIDS + custom MUnitQuest),
we provide an interactive HTML report to the submitter.
This report includes:
- An overall summary of the validation results (n errors, n warnings, etc.)
- An aggregate description of the errors and warnings, grouped by type.
- An interactive and detailed depiction of the errors and warnings.
If the validation has been successful, the report header will contain
the current url to the upload destination.
"""


import json
import os

from collections import Counter, defaultdict


class MUnitQuestDataSubmissionReport:

    def __init__(self, valid: bool, errors: str | dict, warnings: str | dict):
        self.valid: bool = valid
        self.errors: dict = self.load_json(errors) if isinstance(errors, str) else errors
        self.warnings: dict = self.load_json(warnings) if isinstance(warnings, str) else warnings

        self.html: str = ""

    @property
    def validation_status(self) -> str:
        return "Valid" if self.valid else "Invalid"
    
    @property
    def total_errors(self) -> int:
        return len(self.errors)
    
    @property
    def total_warnings(self) -> int:
        return len(self.warnings)

    @staticmethod
    def load_json(path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
        
    @staticmethod
    def aggregate_by_code(items: list[dict]) -> tuple[Counter, defaultdict]:
        counter: Counter = Counter()
        grouped: defaultdict = defaultdict(list)

        for item in items:
            code: str = item["code"]
            counter[code] += 1
            grouped[code].append(item)

        return counter, grouped

    def generate_html(self) -> str:
        # raise NotImplementedError
        error_counts, error_groups = self.aggregate_by_code(self.errors)
        warning_counts, warning_groups = self.aggregate_by_code(self.warnings)

        self.html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
            <meta charset="UTF-8">
            <title>Validation Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 40px;
                    background: #f8f9fa;
                    color: #222;
                }}

                h1, h2, h3 {{
                    color: #333;
                }}

                .summary {{
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 30px;
                    background: {"#e6ffe6" if self.valid else "#ffe6e6"};
                }}

                .error {{ color: #c62828; }}
                .warning {{ color: #ef6c00; }}

                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin-bottom: 30px;
                }}

                th, td {{
                    border: 1px solid #ddd;
                    padding: 10px;
                    text-align: left;
                }}

                th {{
                    background: #f0f0f0;
                }}

                details {{
                    margin: 10px 0;
                    padding: 10px;
                    border: 1px solid #ccc;
                    border-radius: 6px;
                    background: white;
                }}

                summary {{
                    cursor: pointer;
                    font-weight: bold;
                }}

                .location {{
                    font-family: monospace;
                    color: #444;
                }}
            </style>
            </head>
            <body>

            <h1>Validation Report</h1>

            <div class="summary">
                <h2>1. Overall Validation Result</h2>
                <p><strong>Status:</strong> {self.validation_status}</p>
                <p><strong>Error Count:</strong> <span class="error">{self.total_errors}</span></p>
                <p><strong>Warning Count:</strong> <span class="warning">{self.total_warnings}</span></p>
            </div>

            <h2>2. Aggregated Issues</h2>

            <h3>Errors</h3>
            <table>
            <tr><th>Code</th><th>Occurrences</th></tr>
        """

        for code, count in error_counts.items():
            self.html += f"<tr><td>{code}</td><td>{count}</td></tr>"

        self.html += """
            </table>

            <h3>Warnings</h3>
            <table>
            <tr><th>Code</th><th>Occurrences</th></tr>
        """

        for code, count in warning_counts.items():
            self.html += f"<tr><td>{code}</td><td>{count}</td></tr>"

        self.html += """
            </table>

            <h2>3. Detailed Findings</h2>
        """

        # Errors
        self.html += "<h3 class='error'>Errors</h3>"
        for code, items in error_groups.items():
            self.html += f"<details><summary>{code} ({len(items)})</summary>"

            for item in items:
                self.html += f"""
                <details>
                    <summary>{item['location']}</summary>
                    <p><strong>Severity:</strong> {item['severity']}</p>
                    <p><strong>Location:</strong> <span class="location">{item['location']}</span></p>
                    <p><strong>Origin:</strong> {item.get('origin', 'BIDS Validator')}</p>
                </details>
                """

            self.html += "</details>"

        # Warnings
        self.html += "<h3 class='warning'>Warnings</h3>"
        for code, items in warning_groups.items():
            self.html += f"<details><summary>{code} ({len(items)})</summary>"

            for item in items:
                self.html += f"""
                <details>
                    <summary>{item['location']}</summary>
                    <p><strong>Severity:</strong> {item['severity']}</p>
                    <p><strong>Location:</strong> <span class="location">{item['location']}</span></p>
                    <p><strong>Rule:</strong> {item.get('rule', 'N/A')}</p>
                    <p><strong>Origin:</strong> {item.get('origin', 'BIDS Validator')}</p>
                </details>
                """

            self.html += "</details>"

        self.html += """
            </body>
            </html>
        """

        return self.html
    
    def write_report(self, path: str) -> None:
        if not self.html:
            self.generate_html()

        with open(path, "w", encoding="utf-8") as f:
            f.write(self.html)

        return None