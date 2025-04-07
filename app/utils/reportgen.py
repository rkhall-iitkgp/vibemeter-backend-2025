import os
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, RegularPolygon
from matplotlib.path import Path
from matplotlib.projections import register_projection
from matplotlib.projections.polar import PolarAxes
from matplotlib.spines import Spine
from matplotlib.transforms import Affine2D
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.platypus import (
    CondPageBreak,
    Frame,
    Image,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class EmployeeReportPDF:
    def __init__(self, filename, company_name="VibeMeter", logo_path=None):
        self.filename = filename
        self.company_name = company_name
        self.logo_path = logo_path
        self.elements = []

        # Register professional fonts
        self._register_fonts()

        # Create custom styles
        self._create_styles()

        # Set up document with templates
        self.doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            leftMargin=1.25 * cm,
            rightMargin=1.25 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        # Create page templates with headers and footers
        self._create_page_templates()

    def _register_fonts(self):
        """Register professional fonts - using system fonts as fallback"""
        # You can add custom font registration here if you have font files

    def _create_styles(self):
        """Create custom styles with professional fonts"""
        self.styles = getSampleStyleSheet()

        # Define Deloitte-inspired color palette
        self.colors = {
            "primary": colors.HexColor("#80C342"),  # Main green
            "dark": colors.HexColor("#5B8F2F"),  # Darker green for headers
            "light": colors.HexColor("#A6D775"),  # Lighter green for backgrounds
            "very_light": colors.HexColor(
                "#EEF7E5"
            ),  # Very light green for subtle backgrounds
            "text": colors.HexColor("#333333"),  # Dark text color
            "accent": colors.HexColor("#005336"),  # Deloitte-like dark green
            "positive": colors.HexColor("#5B8F2F"),  # For positive metrics
            "negative": colors.HexColor("#C53030"),  # For negative metrics
        }

        # Title style
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=self.styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=12,
            textColor=self.colors["dark"],
        )
        self.styles.add(title_style)

        # Subtitle style
        subtitle_style = ParagraphStyle(
            "CustomSubtitle",
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            alignment=TA_LEFT,
            spaceAfter=6,
            textColor=self.colors["primary"],
        )
        self.styles.add(subtitle_style)

        # Section header style
        section_header_style = ParagraphStyle(
            "SectionHeader",
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            spaceBefore=12,
            spaceAfter=6,
            textColor=self.colors["accent"],
        )
        self.styles.add(section_header_style)

        # Body text style
        body_text_style = ParagraphStyle(
            "CustomBodyText",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            spaceBefore=6,
            spaceAfter=6,
            textColor=self.colors["text"],
        )
        self.styles.add(body_text_style)

        # Metric style
        metric_style = ParagraphStyle(
            "Metric",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            spaceBefore=6,
            spaceAfter=6,
            alignment=TA_LEFT,
        )
        self.styles.add(metric_style)

        # Footer style
        footer_style = ParagraphStyle(
            "Footer", fontName="Helvetica", fontSize=8, textColor=colors.gray
        )
        self.styles.add(footer_style)

    def _create_page_templates(self):
        """Create page templates with headers and footers"""

        def header(canvas, doc):
            canvas.saveState()
            # Logo
            if self.logo_path and os.path.exists(self.logo_path):
                canvas.drawImage(
                    self.logo_path,
                    1 * cm,
                    A4[1] - 2 * cm,
                    width=2 * cm,
                    height=1 * cm,
                    preserveAspectRatio=True,
                )

            # Company name
            canvas.setFont("Helvetica-Bold", 10)
            canvas.setFillColor(self.colors["dark"])
            canvas.drawString(3.5 * cm, A4[1] - 1.5 * cm, self.company_name)

            # Report date
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(self.colors["text"])
            date_text = f"Generated: {datetime.now().strftime('%B %d, %Y')}"
            canvas.drawRightString(A4[0] - 1.25 * cm, A4[1] - 1.5 * cm, date_text)

            # Horizontal line
            canvas.setStrokeColor(self.colors["light"])
            canvas.line(1.25 * cm, A4[1] - 2 * cm, A4[0] - 1.25 * cm, A4[1] - 2 * cm)
            canvas.restoreState()

        def footer(canvas, doc):
            canvas.saveState()
            # Footer line
            canvas.setStrokeColor(self.colors["light"])
            canvas.line(1.25 * cm, 1.5 * cm, A4[0] - 1.25 * cm, 1.5 * cm)

            # Page number
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(self.colors["text"])
            page_num = canvas.getPageNumber()
            canvas.drawCentredString(A4[0] / 2, 1 * cm, f"Page {page_num}")

            # Confidential text
            canvas.setFont("Helvetica", 8)
            canvas.drawString(1.25 * cm, 1 * cm, "CONFIDENTIAL")

            # Company copyright
            canvas.drawRightString(
                A4[0] - 1.25 * cm,
                1 * cm,
                f"© {datetime.now().year} {self.company_name}",
            )
            canvas.restoreState()

        self.doc.addPageTemplates(
            [
                PageTemplate(
                    id="normal",
                    frames=[
                        Frame(
                            self.doc.leftMargin,
                            self.doc.bottomMargin,
                            self.doc.width,
                            self.doc.height,
                            leftPadding=0,
                            rightPadding=0,
                            topPadding=0,
                            bottomPadding=0,
                        )
                    ],
                    onPage=lambda canvas, doc: (
                        header(canvas, doc),
                        footer(canvas, doc),
                    ),
                )
            ]
        )

    def add_title(self, title):
        """Main title of the report with enhanced styling"""
        self.elements.append(Paragraph(title, self.styles["CustomTitle"]))
        self.elements.append(Spacer(1, 20))

    def add_subtitle(self, subtitle):
        """Add a subtitle to the report"""
        self.elements.append(Paragraph(subtitle, self.styles["CustomSubtitle"]))
        self.elements.append(Spacer(1, 10))

    def add_metric(self, label, value, change):
        """Display a large metric with its change percentage using color coding"""
        # Determine color based on change value
        color_val = (
            self.colors["positive"]
            if float(change.replace("%", "").replace("+", "")) >= 0
            else self.colors["negative"]
        )
        color = (
            "green" if float(change.replace("%", "").replace("+", "")) >= 0 else "red"
        )
        change_sign = (
            "+"
            if not change.startswith("+")
            and not change.startswith("-")
            and float(change.replace("%", "")) > 0
            else ""
        )

        metric_text = f"""
        <table width="100%" cellpadding="4" cellspacing="0" style="border: 1px solid {self.colors['light'].hexval()}; background-color: {self.colors['very_light'].hexval()}; border-radius: 4px">
            <tr>
                <td width="50%"><b>{label}</b></td>
                <td width="25%"><font size="14" face="Helvetica-Bold">{value}%</font></td>
                <td width="25%"><font color='{color}' face="Helvetica-Bold">{change_sign}{change}</font></td>
            </tr>
        </table>
        """
        self.elements.append(Paragraph(metric_text, self.styles["Metric"]))
        self.elements.append(Spacer(1, 10))

    def add_trend_chart(self, values, labels):
        """Generate a professional bar chart for trends"""
        plt.figure(figsize=(7, 3.5))

        # Replace ggplot style with a cleaner style
        plt.style.use("default")

        # Set clean background
        fig, ax = plt.subplots(figsize=(7, 3.5))
        ax.set_facecolor("white")
        fig.patch.set_facecolor("white")

        # Enhanced bar chart
        r_primary, g_primary, b_primary = (
            self.colors["primary"].red,
            self.colors["primary"].green,
            self.colors["primary"].blue,
        )
        r_dark, g_dark, b_dark = (
            self.colors["dark"].red,
            self.colors["dark"].green,
            self.colors["dark"].blue,
        )

        bars = ax.bar(
            labels,
            values,
            color=(r_primary, g_primary, b_primary),
            width=0.6,
            edgecolor=(r_dark, g_dark, b_dark),
            linewidth=1,
        )

        # Add trend line
        r_accent, g_accent, b_accent = (
            self.colors["accent"].red,
            self.colors["accent"].green,
            self.colors["accent"].blue,
        )
        ax.plot(
            labels,
            values,
            color=(r_accent, g_accent, b_accent),
            marker="o",
            linestyle="-",
            linewidth=2,
            markersize=6,
        )

        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 1,
                f"{height}%",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        # Styling
        ax.set_title("Vibe Scores Over Time", fontsize=12, fontweight="bold", pad=15)
        ax.set_ylabel("Score (%)", fontsize=10)
        ax.set_ylim(0, max(values) * 1.15)  # Add some headroom for labels

        # Add light grid lines instead of grey background
        ax.grid(axis="y", linestyle="--", alpha=0.3, color="#CCCCCC")

        # Improve x and y axis appearance
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(labelsize=10)

        # Save with high DPI for better quality
        chart_path = "trend_chart.png"
        plt.tight_layout()
        plt.savefig(chart_path, bbox_inches="tight", dpi=300)
        plt.close()

        # Create a table to center the image with a caption
        self.elements.append(Spacer(1, 15))
        self.elements.append(Image(chart_path, width=6 * inch, height=3 * inch))
        self.elements.append(
            Paragraph(
                "<i>Figure: Employee satisfaction trend over time</i>",
                self.styles["CustomBodyText"],
            )
        )
        self.elements.append(Spacer(1, 15))

    def add_employee_table(self, data):
        """Highlight employees needing attention with improved styling"""
        # Add a heading before the table
        self.elements.append(
            Paragraph("Employee Attention Report", self.styles["SectionHeader"])
        )
        self.elements.append(Spacer(1, 10))

        table_data = [["Employee", "Issue", "Impact"]]
        table_data.extend(data)

        # Calculate appropriate column widths
        col_widths = [self.doc.width * 0.3, self.doc.width * 0.4, self.doc.width * 0.3]

        table = Table(table_data, colWidths=col_widths)

        # Enhanced table styling
        table_style = [
            # Header row
            ("BACKGROUND", (0, 0), (-1, 0), self.colors["primary"]),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            # Body rows
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("TEXTCOLOR", (0, 1), (-1, -1), self.colors["text"]),
            ("ALIGN", (0, 1), (0, -1), "LEFT"),  # Left align employee names
            ("ALIGN", (1, 1), (1, -1), "LEFT"),  # Left align issues
            ("ALIGN", (2, 1), (2, -1), "CENTER"),  # Center align impact
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
            ("TOPPADDING", (0, 1), (-1, -1), 6),
            # Borders
            ("GRID", (0, 0), (-1, -1), 0.5, self.colors["light"]),
            ("BOX", (0, 0), (-1, -1), 1, self.colors["dark"]),
            # Zebra striping for readability
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ]

        # Add zebra striping
        for i in range(1, len(table_data), 2):
            table_style.append(
                ("BACKGROUND", (0, i), (-1, i), self.colors["very_light"])
            )

        # Highlight negative impacts
        for i in range(1, len(table_data)):
            impact = table_data[i][2]
            if isinstance(impact, str) and ("-" in impact or "Urgent" in impact):
                table_style.append(
                    ("TEXTCOLOR", (2, i), (2, i), self.colors["negative"])
                )
                table_style.append(("FONTNAME", (2, i), (2, i), "Helvetica-Bold"))

        table.setStyle(TableStyle(table_style))
        self.elements.append(table)
        self.elements.append(Spacer(1, 15))

    def add_issues_summary(self, issues, issue_counts=None):
        """Summarize major issues with visual enhancements and a horizontal bar chart"""
        self.elements.append(
            Paragraph("Major Employee Concerns", self.styles["SectionHeader"])
        )
        self.elements.append(Spacer(1, 10))

        # Create an enhanced HTML table with Unicode bullet points instead of SVG images
        issues_html = f"""
        <table width="100%" cellpadding="5" cellspacing="0" style="background-color: {self.colors['very_light'].hexval()}; border: 1px solid {self.colors['light'].hexval()}; border-radius: 4px">
        """

        # Add each issue as a row with Unicode bullet character
        for i, issue in enumerate(issues):
            # Split the issue into category and description if it has a colon
            if ":" in issue:
                category, description = issue.split(":", 1)
                issues_html += f"""
                <tr>
                    <td width="5%" valign="top"><font color="{self.colors['primary'].hexval()}" size="+2">&#8226;</font></td>
                    <td width="25%" valign="top"><b>{category}</b></td>
                    <td width="70%" valign="top">{description}</td>
                </tr>
                """
            else:
                # For issues without a category/description split
                issues_html += f"""
                <tr>
                    <td width="5%" valign="top"><font color="{self.colors['primary'].hexval()}" size="+2">&#8226;</font></td>
                    <td width="95%" colspan="2" valign="top">{issue}</td>
                </tr>
                """

        issues_html += """
        </table>
        """

        self.elements.append(Paragraph(issues_html, self.styles["CustomBodyText"]))
        self.elements.append(Spacer(1, 15))

        # Rest of the method unchanged...

        # Create visualization of issues if counts are provided
        if issue_counts is None:
            # Generate sample data if none provided, just for visualization
            issue_counts = [
                len(i.split()) % 10 + 5 for i in issues
            ]  # Just a formula to get varied numbers

        # Create horizontal bar chart of issues
        fig, ax = plt.subplots(figsize=(7, 4))
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        # Reverse the lists to have the most critical issue at the top
        issues_short = [i.split(":")[0] if ":" in i else i[:30] + "..." for i in issues]
        issues_short.reverse()
        issue_counts.reverse()

        # Fix: Extract RGB components directly
        r_primary, g_primary, b_primary = (
            self.colors["primary"].red,
            self.colors["primary"].green,
            self.colors["primary"].blue,
        )
        r_dark, g_dark, b_dark = (
            self.colors["dark"].red,
            self.colors["dark"].green,
            self.colors["dark"].blue,
        )

        # Create horizontal bar chart with RGB tuples
        bars = ax.barh(
            range(len(issues_short)),
            issue_counts,
            color=(r_primary, g_primary, b_primary),
            edgecolor=(r_dark, g_dark, b_dark),
            linewidth=1,
        )

        # Add count labels to the end of each bar
        for i, (count, bar) in enumerate(zip(issue_counts, bars)):
            ax.text(
                count + 0.5,
                bar.get_y() + bar.get_height() / 2,
                str(count),
                va="center",
                fontweight="bold",
                fontsize=9,
            )

        # Customize chart
        ax.set_yticks(range(len(issues_short)))
        ax.set_yticklabels(issues_short)
        ax.set_xlabel("Frequency/Severity", fontsize=10)
        ax.set_title(
            "Major Employee Concerns by Frequency/Severity",
            fontsize=12,
            fontweight="bold",
            pad=15,
        )

        # Improve grid appearance
        ax.grid(axis="x", linestyle="--", alpha=0.3, color="#CCCCCC")

        # Remove top and right spines for cleaner look
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        plt.tight_layout()

        # Save chart
        chart_path = "issues_chart.png"
        plt.savefig(chart_path, bbox_inches="tight", dpi=300)
        plt.close()

        # Add to the report
        self.elements.append(Image(chart_path, width=6.5 * inch, height=4 * inch))
        self.elements.append(
            Paragraph(
                "<i>Figure: Frequency/severity of major employee concerns</i>",
                self.styles["CustomBodyText"],
            )
        )
        self.elements.append(Spacer(1, 15))

    def add_section_divider(self):
        """Add a visual divider between sections"""
        self.elements.append(Spacer(1, 10))
        self.elements.append(
            CondPageBreak(inch * 2)
        )  # Break page if less than 2 inches left
        self.elements.append(Spacer(1, 10))

    def add_satisfaction_radar(
        self, categories, data, title="Employee Satisfaction Dimensions"
    ):
        """Add a radar chart showing multiple dimensions of employee satisfaction"""
        N = len(categories)
        theta = radar_factory(N, frame="polygon")

        # Create the figure
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection="radar"))

        # Fix: Use RGB tuple values directly instead of hex string
        r, g, b = (
            self.colors["primary"].red,
            self.colors["primary"].green,
            self.colors["primary"].blue,
        )

        # Plot the data
        ax.plot(theta, data, color=(r, g, b))
        ax.fill(theta, data, alpha=0.25, color=(r, g, b))

        # Customize the chart
        ax.set_varlabels(categories)
        ax.set_ylim(0, 100)
        plt.title(title, weight="bold", size=12, y=1.1)

        # Add value labels at each point
        for i, value in enumerate(data):
            angle = theta[i]
            ax.text(
                angle,
                value + 5,
                f"{value}%",
                ha="center",
                va="center",
                fontweight="bold",
                fontsize=9,
            )

        # Save figure
        chart_path = "satisfaction_radar.png"
        plt.tight_layout()
        plt.savefig(chart_path, bbox_inches="tight", dpi=300)
        plt.close()

        # Add to the report
        self.elements.append(Spacer(1, 10))
        self.elements.append(Image(chart_path, width=5 * inch, height=5 * inch))
        self.elements.append(
            Paragraph(
                "<i>Figure: Multi-dimensional employee satisfaction analysis</i>",
                self.styles["CustomBodyText"],
            )
        )
        self.elements.append(Spacer(1, 15))

    def generate_pdf(self):
        """Generate and save the PDF"""
        self.doc.build(self.elements)
        print(f"PDF Report Created: {self.filename}")


def radar_factory(num_vars, frame="circle"):
    """Create a radar chart with `num_vars` axes."""
    # Calculate evenly-spaced axis angles
    theta = np.linspace(0, 2 * np.pi, num_vars, endpoint=False)

    class RadarAxes(PolarAxes):
        name = "radar"

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.set_theta_zero_location("N")

        def fill(self, *args, **kwargs):
            """Override fill so that line is closed by default"""
            closed = kwargs.pop("closed", True)
            return super().fill(closed=closed, *args, **kwargs)

        def plot(self, *args, **kwargs):
            """Override plot so that line is closed by default"""
            lines = super().plot(*args, **kwargs)
            for line in lines:
                self._close_line(line)
            return lines

        def _close_line(self, line):
            x, y = line.get_data()
            # FIXME: markers at x[0], y[0] get doubled-up
            if x[0] != x[-1]:
                x = np.append(x, x[0])
                y = np.append(y, y[0])
                line.set_data(x, y)

        def set_varlabels(self, labels):
            self.set_thetagrids(np.degrees(theta), labels)

        def _gen_axes_patch(self):
            # The Axes patch must be centered at (0.5, 0.5) and of radius 0.5
            # in axes coordinates.
            if frame == "circle":
                return Circle((0.5, 0.5), 0.5)
            elif frame == "polygon":
                return RegularPolygon((0.5, 0.5), num_vars, radius=0.5, edgecolor="k")
            else:
                raise ValueError("Unknown value for 'frame': %s" % frame)

        def _gen_axes_spines(self):
            if frame == "circle":
                return super()._gen_axes_spines()
            elif frame == "polygon":
                # spine_type must be 'left'/'right'/'top'/'bottom'/'circle'.
                spine = Spine(
                    axes=self,
                    spine_type="circle",
                    path=Path.unit_regular_polygon(num_vars),
                )
                # unit_regular_polygon returns a polygon of radius 1 centered at
                # (0, 0) but we want a polygon of radius 0.5 centered at (0.5,
                # 0.5) in axes coordinates.
                spine.set_transform(
                    Affine2D().scale(0.5).translate(0.5, 0.5) + self.transAxes
                )
                return {"polar": spine}
            else:
                raise ValueError("Unknown value for 'frame': %s" % frame)

    register_projection(RadarAxes)
    return theta


# --- Updated Usage Example with Real Data ---
def make_report(
    title, subtitle, metrics, issues, high_concern_employees, vibeMeterData
):
    # Create a report with optional company logo
    report = EmployeeReportPDF(
        "employee_dashboard.pdf", company_name="VibeMeter", logo_path=None
    )

    # Add document sections
    report.add_title(title=title)
    report.add_subtitle(subtitle=subtitle)
    metric_title = (
        metrics["metric_title"]
        if "metric_title" in metrics
        else "Employee Satisfaction Metrics"
    )
    metric_score = metrics["metric_score"] if "metric_score" in metrics else 68
    metric_change = metrics["metric_change"] if "metric_change" in metrics else "+5.3%"
    # Metrics section using the EmployeeSatisfactionGauge data
    report.add_metric(metric_title, metric_score, metric_change)
    # report.add_metric("Employee Engagement", 72, "+3.1%")
    # report.add_metric("Team Collaboration", 65, "-2.4%")

    # Radar chart showing multiple satisfaction dimensions
    # Using data derived from the issues provided
    # report.add_satisfaction_radar(
    #     categories=["Workload", "Recognition", "Compensation",
    #                "Career Growth", "Team Culture", "Leadership"],
    #     data=[75, 60, 70, 65, 50, 60]
    # )

    # Trend visualization using the ChartData
    chart_data = vibeMeterData["chart_data"]

    report.add_trend_chart(
        values=[item["score"] for item in chart_data["scores"]],
        labels=[item["month"] for item in chart_data["scores"]],
    )

    # Add a divider
    report.add_section_divider()

    # High concern employees table using defaultEmployees data
    report.add_title("High Concern Employees")
    high_concern_data = high_concern_employees["high_concern_employees"]
    report.add_employee_table(high_concern_data)

    # Issues summary with visualization - using the provided issues data
    issue = issues["issues"]
    issue_counts = issues["issue_count"]  # Just a formula to get varied numbers
    report.add_issues_summary(issue, issue_counts)

    # Recommendations with impact/effort scores
    # recommendations = [
    #     "Implement leadership training program for team leads",
    #     "Review and adjust workload distribution across teams",
    #     "Develop a formal recognition program for achievements",
    #     "Conduct compensation benchmarking and adjust as needed",
    #     "Create clearer career advancement paths and opportunities"
    # ]

    # # Impact scores derived from the provided data
    # impact_scores = [9, 8, 7, 8, 9]
    # effort_scores = [6, 7, 4, 8, 7]
    # report.add_recommendations(recommendations, impact_scores, effort_scores)

    # Generate the PDF
    report.generate_pdf()


# if __name__ == "__main__":
#     # Example data for testing
#     title = "Employee Engagement & Satisfaction Report"
#     subtitle = "Quarterly Analysis - Q2 2025"
#     metrics = {
#         "satisfaction": 68,
#         "engagement": 72,
#         "collaboration": 65,
#     }
#     issues = [
#         "Workload: Heavy workload affecting wellness",
#         "Recognition: Insufficient recognition systems",
#         "Compensation: Concerns about fair compensation",
#         "Work-Life: Work-life balance issues",
#         "Career Growth: Limited career advancement",
#         "Team Culture: Team dynamic challenges",
#         "Leadership: Leadership effectiveness",
#     ]
#     defaultEmployees = [
#         {"name": "Ankan", "issue": "Leadership Training", "impact": "-28%"},
#         {"name": "John Doe", "issue": "Morality", "impact": "-40%"},
#         {"name": "Jane Smith", "issue": "Engagement", "impact": "-18%"},
#     ]

#     make_report(title, subtitle, metrics, issues, defaultEmployees)
