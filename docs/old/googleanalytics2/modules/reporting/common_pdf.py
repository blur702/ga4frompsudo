import os
import tempfile
import logging
from datetime import datetime
from flask import current_app, render_template
from playwright.sync_api import sync_playwright
import pdfkit

from modules.reporting.common import format_date_for_display, format_number

def generate_report_pdf(report_data, template_name, output_path=None, title=None, 
                       include_summary=True, include_url_overview=False, 
                       first_url_only=False, include_screenshot=False):
    """
    Generate a PDF for any report.
    
    Args:
        report_data (dict): The report data.
        template_name (str): The name of the template to use.
        output_path (str): The path to save the PDF to. If None, a temporary file is created.
        title (str): The title of the report. If None, a default title is used.
        include_summary (bool): Whether to include a summary.
        include_url_overview (bool): Whether to include a URL overview.
        first_url_only (bool): Whether to only include the first URL in the overview.
        include_screenshot (bool): Whether to include screenshots of URLs.
        
    Returns:
        str: The path to the generated PDF.
    """
    # Create a temporary directory for screenshots
    temp_dir = tempfile.mkdtemp()
    screenshots = []
    
    # Take screenshots if requested
    if include_screenshot and include_url_overview:
        urls = get_urls_from_report(report_data)
        if first_url_only and urls:
            urls = [urls[0]]
        
        for url in urls:
            screenshot_path = take_url_screenshot(url, temp_dir)
            if screenshot_path:
                screenshots.append({
                    'url': url,
                    'path': screenshot_path
                })
    
    # Generate summary if requested
    summary = None
    if include_summary:
        summary = generate_report_summary(report_data, template_name)
    
    # Generate URL overview if requested
    url_overview = None
    if include_url_overview:
        url_overview = generate_url_overview(report_data, first_url_only)
    
    # Determine output path
    if not output_path:
        output_path = os.path.join(temp_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    
    # Determine title
    if not title:
        if template_name == 'url_analytics':
            title = f"URL Analytics Report - {report_data.get('url', 'Unknown URL')}"
        elif template_name == 'property_aggregation':
            title = "Property Aggregation Report"
        else:
            title = f"Analytics Report - {datetime.now().strftime('%Y-%m-%d')}"
    
    # Render the PDF template
    html = render_template(
        f'reports/pdf/{template_name}.html',
        report=report_data,
        title=title,
        summary=summary,
        url_overview=url_overview,
        screenshots=screenshots,
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        format_date=format_date_for_display,
        format_number=format_number
    )
    
    # Convert HTML to PDF
    try:
        # Try using pdfkit first (wkhtmltopdf)
        pdfkit_config = pdfkit.configuration(wkhtmltopdf=current_app.config.get('WKHTMLTOPDF_PATH', '/usr/local/bin/wkhtmltopdf'))
        pdfkit.from_string(html, output_path, configuration=pdfkit_config, options={
            'page-size': 'A4',
            'margin-top': '10mm',
            'margin-right': '10mm',
            'margin-bottom': '10mm',
            'margin-left': '10mm',
            'encoding': 'UTF-8',
            'no-outline': None,
            'enable-local-file-access': None
        })
    except Exception as e:
        current_app.logger.warning(f"Error generating PDF with pdfkit: {e}")
        
        # Fall back to Playwright
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(viewport={'width': 1280, 'height': 1600})
                page.set_content(html)
                page.pdf(path=output_path, format='A4', margin={
                    'top': '10mm',
                    'right': '10mm',
                    'bottom': '10mm',
                    'left': '10mm'
                })
                browser.close()
        except Exception as e:
            current_app.logger.error(f"Error generating PDF with Playwright: {e}")
            return None
    
    return output_path

def generate_report_summary(report_data, report_type):
    """
    Generate a text summary of a report.
    
    Args:
        report_data (dict): The report data.
        report_type (str): The type of report.
        
    Returns:
        str: The summary text.
    """
    summary = []
    
    if report_type == 'url_analytics':
        url = report_data.get('url', 'Unknown URL')
        start_date = format_date_for_display(report_data.get('start_date'))
        end_date = format_date_for_display(report_data.get('end_date'))
        
        metrics = report_data.get('aggregated_metrics', {})
        users = metrics.get('activeUsers', 0)
        sessions = metrics.get('sessions', 0)
        pageviews = metrics.get('screenPageViews', 0)
        
        summary.append(f"URL Analytics Report for {url}")
        summary.append(f"Date Range: {start_date} to {end_date}")
        summary.append("")
        summary.append(f"During this period, the URL received {format_number(users)} active users, {format_number(sessions)} sessions, and {format_number(pageviews)} page views.")
        
        # Add top referrers
        top_referrers = report_data.get('top_referrers', [])
        if top_referrers:
            summary.append("")
            summary.append("Top Referrers:")
            for i, referrer in enumerate(top_referrers[:5], 1):
                summary.append(f"{i}. {referrer['dimension']} - {referrer['formatted_metric']} sessions ({referrer['percentage']:.1f}%)")
        
        # Add top devices
        top_devices = report_data.get('top_devices', [])
        if top_devices:
            summary.append("")
            summary.append("Device Breakdown:")
            for device in top_devices:
                summary.append(f"- {device['dimension']}: {device['formatted_metric']} sessions ({device['percentage']:.1f}%)")
    
    elif report_type == 'property_aggregation':
        start_date = format_date_for_display(report_data.get('start_date'))
        end_date = format_date_for_display(report_data.get('end_date'))
        properties = report_data.get('properties', [])
        
        summary.append(f"Property Aggregation Report")
        summary.append(f"Date Range: {start_date} to {end_date}")
        summary.append(f"Properties Included: {len(properties)}")
        summary.append("")
        
        metrics = report_data.get('aggregated_metrics', {})
        users = metrics.get('activeUsers', 0)
        sessions = metrics.get('sessions', 0)
        pageviews = metrics.get('screenPageViews', 0)
        
        summary.append(f"During this period, the properties collectively received {format_number(users)} active users, {format_number(sessions)} sessions, and {format_number(pageviews)} page views.")
        
        # Add property comparison
        if properties:
            summary.append("")
            summary.append("Property Comparison (Active Users):")
            
            # Sort properties by active users
            sorted_properties = sorted(
                properties, 
                key=lambda p: p.get('aggregated_metrics', {}).get('activeUsers', 0),
                reverse=True
            )
            
            for i, prop in enumerate(sorted_properties[:5], 1):
                prop_users = prop.get('aggregated_metrics', {}).get('activeUsers', 0)
                summary.append(f"{i}. {prop['property_name']} - {format_number(prop_users)} active users")
    
    return "\n".join(summary)

def generate_url_overview(report_data, first_only=False):
    """
    Generate an overview of URLs in a report.
    
    Args:
        report_data (dict): The report data.
        first_only (bool): Whether to only include the first URL.
        
    Returns:
        str: The URL overview text.
    """
    urls = get_urls_from_report(report_data)
    
    if not urls:
        return None
    
    if first_only:
        urls = [urls[0]]
    
    overview = []
    for url in urls:
        overview.append(f"URL: {url}")
    
    return "\n".join(overview)

def get_urls_from_report(report_data):
    """
    Get URLs from a report.
    
    Args:
        report_data (dict): The report data.
        
    Returns:
        list: A list of URLs.
    """
    urls = []
    
    # URL analytics report
    if 'url' in report_data:
        urls.append(report_data['url'])
    
    # Property aggregation report
    if 'properties' in report_data:
        for prop in report_data['properties']:
            if 'website_url' in prop and prop['website_url']:
                urls.append(prop['website_url'])
    
    return urls

def take_url_screenshot(url, output_dir):
    """
    Take a screenshot of a URL.
    
    Args:
        url (str): The URL to screenshot.
        output_dir (str): The directory to save the screenshot to.
        
    Returns:
        str: The path to the screenshot or None if an error occurs.
    """
    if not url:
        return None
    
    # Generate a filename based on the URL
    filename = f"screenshot_{hash(url) % 10000}.png"
    output_path = os.path.join(output_dir, filename)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.screenshot(path=output_path, full_page=False)
            browser.close()
        
        return output_path
    except Exception as e:
        current_app.logger.error(f"Error taking screenshot of {url}: {e}")
        return None