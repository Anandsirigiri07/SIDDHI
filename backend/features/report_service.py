# backend/features/report_service.py
from datetime import datetime
from backend.report_providers import report_manager

def compile_dossier_html(case_id: str, case_data: dict, recommendations: list) -> str:
    recs_li = "".join([f"<li>{r}</li>" for r in recommendations])
    return f"""
    <html>
    <head><style>body {{ font-family: sans-serif; padding: 20px; }} h1 {{ color: #0891b2; }}</style></head>
    <body>
        <h1>Case Dossier Briefing: {case_data.get('fir_number', 'N/A')}</h1>
        <p><strong>Generated on:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <hr/>
        <h3>Factual Database Evidence</h3>
        <ul>
            <li><strong>Case ID:</strong> {case_id}</li>
            <li><strong>Registration Date:</strong> {case_data.get('date', 'N/A')}</li>
            <li><strong>Category:</strong> {case_data.get('crime_type', 'N/A')}</li>
            <li><strong>Description:</strong> {case_data.get('description', 'N/A')}</li>
        </ul>
        <h3>Recommended Investigative Leads</h3>
        <ul>
            {recs_li}
        </ul>
    </body>
    </html>
    """

def compile_executive_html(summary_data: dict) -> str:
    dr_rows = "".join([
        f"<tr><td>#{idx + 1} {dr['district']}</td><td align='right'>{dr['case_count']}</td><td align='right'>+{dr['forecasted_growth']:.1f}%</td></tr>"
        for idx, dr in enumerate(summary_data.get("district_rankings", []))
    ])
    return f"""
    <html>
    <head><style>body {{ font-family: sans-serif; padding: 20px; }} h1 {{ color: #0891b2; }} table {{ width: 100%; border-collapse: collapse; }} th, td {{ padding: 8px; border: 1px solid #ddd; }}</style></head>
    <body>
        <h1>City-Wide Crime Intelligence briefing</h1>
        <p><strong>Total Cases:</strong> {summary_data.get('city_wide_summary', {}).get('total_cases', 0)} | <strong>Active Hotspots:</strong> {summary_data.get('city_wide_summary', {}).get('active_hotspots_count', 0)}</p>
        <hr/>
        <h3>District Rankings</h3>
        <table>
            <thead>
                <tr><th>District</th><th align='right'>Cases</th><th align='right'>Forecast Growth</th></tr>
            </thead>
            <tbody>
                {dr_rows}
            </tbody>
        </table>
    </body>
    </html>
    """

def generate_case_dossier_pdf(case_id: str, case_data: dict, recommendations: list) -> str:
    html = compile_dossier_html(case_id, case_data, recommendations)
    filename = f"dossier_case_{case_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return report_manager.generate(html, filename)

def generate_executive_pdf(summary_data: dict) -> str:
    html = compile_executive_html(summary_data)
    filename = f"executive_briefing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return report_manager.generate(html, filename)

def generate_district_pdf(district_name: str, district_data: dict) -> str:
    html = f"<html><body><h1>District Intelligence Report: {district_name}</h1><p>Cases: {district_data.get('district_summary', {}).get('case_count', 0)}</p></body></html>"
    filename = f"district_{district_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return report_manager.generate(html, filename)

def generate_hotspots_pdf(hotspots_data: list) -> str:
    html = f"<html><body><h1>Hotspot Intelligence Bulletin</h1><p>Active DBSCAN Hotspots: {len(hotspots_data)}</p></body></html>"
    filename = f"hotspots_bulletin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return report_manager.generate(html, filename)
