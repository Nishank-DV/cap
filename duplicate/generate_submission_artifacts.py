"""Create final non-source submission artifacts from verified Stage 9 outputs."""
from pathlib import Path
from shutil import copy2
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak

BASE_DIR = Path(__file__).resolve().parent
OUTPUT = BASE_DIR / "output"
UC2 = OUTPUT / "usecase2"

def copy_compatibility_aliases():
    for source, alias in (("crime_by_category.png", "top_10_crime_categories.png"),
                          ("top_community_areas.png", "top_10_community_areas.png")):
        target = UC2 / alias
        if not target.exists():
            copy2(UC2 / source, target)

def build_insights_pdf():
    destination = OUTPUT / "insights" / "chicago_crime_analytics_insights.pdf"
    destination.parent.mkdir(exist_ok=True)
    styles = getSampleStyleSheet()
    story = [Paragraph("Chicago Crime Analytics — Insights", styles["Title"]), Spacer(1, 12),
             Paragraph("This document uses the validated Stage 9 analysis outputs for the supplied 2,000-record dataset. Findings are descriptive and do not establish causality.", styles["BodyText"]), Spacer(1, 12)]
    captions = [
        ("crime_trend_by_year.png", "Crime trend by year"),
        ("top_10_crime_categories.png", "Top crime categories"),
        ("arrest_rate_by_year.png", "Arrest rate by year"),
        ("crime_month_day_heatmap.png", "Month × DayOfWeek heatmap"),
        ("top_10_community_areas.png", "Top community areas"),
    ]
    for filename, caption in captions:
        story += [Paragraph(caption, styles["Heading2"]), Image(str(UC2 / filename), width=460, height=280), Spacer(1, 12)]
    story += [PageBreak(), Paragraph("Analytical notes", styles["Heading2"]),
              Paragraph("The charts identify variation across years, concentrated crime categories and community areas, changing arrest rates, and month/day frequency patterns. These results can guide further investigation and resource-planning questions when combined with context beyond this extract.", styles["BodyText"])]
    SimpleDocTemplate(str(destination), pagesize=letter).build(story)
    return destination

def build_screenshot_pdf():
    destination = OUTPUT / "screenshots" / "frontend_application_screenshots.pdf"
    styles = getSampleStyleSheet()
    story = [Paragraph("Chicago Crime Analytics — Frontend Screenshots", styles["Title"]), Spacer(1, 12)]
    labels = {"dashboard": "Dashboard", "data-management": "Data Management", "usecase1": "Use Case 1", "usecase2": "Use Case 2", "usecase3": "Use Case 3", "usecase4": "Use Case 4"}
    for key, label in labels.items():
        image = OUTPUT / "screenshots" / f"{key}.png"
        if not image.exists():
            raise FileNotFoundError(f"Actual screenshot not found: {image}")
        story += [Paragraph(label, styles["Heading2"]), Image(str(image), width=500, height=556), PageBreak()]
    SimpleDocTemplate(str(destination), pagesize=letter).build(story)
    return destination

if __name__ == "__main__":
    copy_compatibility_aliases()
    print(build_insights_pdf())
    print(build_screenshot_pdf())
