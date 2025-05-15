"""
Accessibility utilities for ensuring WCAG compliance in the GA4 Analytics Dashboard.

This module provides utilities for:
- Ensuring color contrast compliance
- Generating accessible color palettes
- Creating screen reader friendly content
- Form accessibility validation
"""

import re
import logging
import math
from typing import Tuple, List, Dict, Optional

logger = logging.getLogger(__name__)

# Color constants
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """
    Convert RGB color to hex format.
    
    Args:
        rgb: Tuple of RGB values (0-255)
        
    Returns:
        Hex color string (e.g., '#FF5733')
    """
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert hex color to RGB format.
    
    Args:
        hex_color: Hex color string (e.g., '#FF5733' or 'FF5733')
        
    Returns:
        Tuple of RGB values (0-255)
    """
    # Remove the '#' if present
    hex_color = hex_color.lstrip('#')
    
    # Handle shorthand hex (e.g., #fff)
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    
    # Convert to RGB
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def calculate_luminance(rgb: Tuple[int, int, int]) -> float:
    """
    Calculate the relative luminance of a color.
    
    Based on WCAG 2.0 formula:
    https://www.w3.org/TR/WCAG20-TECHS/G17.html#G17-tests
    
    Args:
        rgb: Tuple of RGB values (0-255)
        
    Returns:
        Relative luminance value (0-1)
    """
    # Normalize RGB values to 0-1
    r, g, b = [x / 255 for x in rgb]
    
    # Convert to sRGB
    r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
    g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
    b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
    
    # Calculate luminance
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def calculate_contrast_ratio(color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
    """
    Calculate the contrast ratio between two colors.
    
    Based on WCAG 2.0 formula:
    https://www.w3.org/TR/WCAG20-TECHS/G17.html#G17-tests
    
    Args:
        color1: First color as RGB tuple
        color2: Second color as RGB tuple
        
    Returns:
        Contrast ratio (1-21)
    """
    # Calculate luminance values
    luminance1 = calculate_luminance(color1)
    luminance2 = calculate_luminance(color2)
    
    # Make sure luminance1 is the lighter color
    if luminance1 < luminance2:
        luminance1, luminance2 = luminance2, luminance1
    
    # Calculate contrast ratio
    return (luminance1 + 0.05) / (luminance2 + 0.05)

def check_contrast_compliance(color1: str, color2: str, level: str = 'AA') -> bool:
    """
    Check if two colors meet WCAG contrast requirements.
    
    Args:
        color1: First color in hex format
        color2: Second color in hex format
        level: Compliance level ('A', 'AA', or 'AAA')
        
    Returns:
        True if compliant, False otherwise
    """
    # Convert hex to RGB
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    
    # Calculate contrast ratio
    ratio = calculate_contrast_ratio(rgb1, rgb2)
    
    # Check compliance
    if level.upper() == 'A':
        return ratio >= 3  # Level A: 3:1 for large text, graphics and UI components
    elif level.upper() == 'AAA':
        return ratio >= 7  # Level AAA: 7:1 for normal text, 4.5:1 for large text
    else:  # Default: level AA
        return ratio >= 4.5  # Level AA: 4.5:1 for normal text, 3:1 for large text

def generate_accessible_color_palette(base_color: str, num_colors: int = 5, level: str = 'AA') -> List[str]:
    """
    Generate an accessible color palette based on a base color.
    
    Args:
        base_color: Base color in hex format
        num_colors: Number of colors to generate
        level: Compliance level ('A', 'AA', or 'AAA')
        
    Returns:
        List of hex color strings
    """
    base_rgb = hex_to_rgb(base_color)
    palette = [base_color]
    
    # Convert to HSV space for better color variations
    h, s, v = rgb_to_hsv(*base_rgb)
    
    # Generate colors with different hues
    for i in range(1, num_colors):
        new_h = (h + i * (360 / num_colors)) % 360
        new_rgb = hsv_to_rgb(new_h, s, v)
        
        # Adjust saturation and value if needed for contrast
        contrast = calculate_contrast_ratio(base_rgb, new_rgb)
        min_contrast = 4.5 if level.upper() == 'AA' else 7 if level.upper() == 'AAA' else 3
        
        if contrast < min_contrast:
            # Adjust value (brightness) to increase contrast
            if calculate_luminance(base_rgb) > 0.5:
                # Base is light, make new color darker
                new_rgb = hsv_to_rgb(new_h, s, max(0.2, v - 0.3))
            else:
                # Base is dark, make new color lighter
                new_rgb = hsv_to_rgb(new_h, s, min(0.9, v + 0.3))
        
        palette.append(rgb_to_hex(new_rgb))
    
    return palette

def rgb_to_hsv(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """
    Convert RGB color to HSV format.
    
    Args:
        r: Red component (0-255)
        g: Green component (0-255)
        b: Blue component (0-255)
        
    Returns:
        Tuple of HSV values (hue: 0-360, saturation: 0-1, value: 0-1)
    """
    r, g, b = r / 255, g / 255, b / 255
    
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    diff = max_val - min_val
    
    # Hue calculation
    if max_val == min_val:
        h = 0  # Achromatic (gray)
    elif max_val == r:
        h = (60 * ((g - b) / diff) + 360) % 360
    elif max_val == g:
        h = (60 * ((b - r) / diff) + 120) % 360
    else:  # max_val == b
        h = (60 * ((r - g) / diff) + 240) % 360
    
    # Saturation calculation
    s = 0 if max_val == 0 else diff / max_val
    
    # Value calculation
    v = max_val
    
    return h, s, v

def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
    """
    Convert HSV color to RGB format.
    
    Args:
        h: Hue component (0-360)
        s: Saturation component (0-1)
        v: Value component (0-1)
        
    Returns:
        Tuple of RGB values (0-255)
    """
    if s == 0:
        # Achromatic (gray)
        return tuple(int(v * 255) for _ in range(3))
    
    h /= 60  # sector 0 to 5
    i = math.floor(h)
    f = h - i  # factorial part of h
    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))
    
    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:  # i == 5
        r, g, b = v, p, q
    
    return tuple(int(x * 255) for x in (r, g, b))

def create_aria_attributes(element_type: str, content: Optional[str] = None) -> Dict[str, str]:
    """
    Generate appropriate ARIA attributes for different element types.
    
    Args:
        element_type: Type of element ('button', 'input', 'alert', etc.)
        content: Optional content or label text
        
    Returns:
        Dictionary of ARIA attributes
    """
    aria_attrs = {}
    
    if element_type == 'button':
        if content:
            aria_attrs['aria-label'] = content
    elif element_type == 'input':
        aria_attrs['aria-required'] = 'false'
        if content:
            aria_attrs['aria-label'] = content
    elif element_type == 'alert':
        aria_attrs['role'] = 'alert'
        aria_attrs['aria-live'] = 'assertive'
    elif element_type == 'status':
        aria_attrs['role'] = 'status'
        aria_attrs['aria-live'] = 'polite'
    elif element_type == 'progressbar':
        aria_attrs['role'] = 'progressbar'
        aria_attrs['aria-valuemin'] = '0'
        aria_attrs['aria-valuemax'] = '100'
        aria_attrs['aria-valuenow'] = '0'
    elif element_type == 'tab':
        aria_attrs['role'] = 'tab'
        if content:
            aria_attrs['aria-label'] = content
    elif element_type == 'tabpanel':
        aria_attrs['role'] = 'tabpanel'
    elif element_type == 'dialog':
        aria_attrs['role'] = 'dialog'
        aria_attrs['aria-modal'] = 'true'
        if content:
            aria_attrs['aria-labelledby'] = content
    
    return aria_attrs

def generate_alt_text(image_description: str, context: str = '') -> str:
    """
    Generate appropriate alt text for an image.
    
    Args:
        image_description: Description of the image
        context: Additional context (e.g., where the image appears)
        
    Returns:
        Alt text string
    """
    alt_text = image_description.strip()
    
    # If no description provided, use empty alt for decorative images
    if not alt_text:
        return ""
    
    # Avoid redundant phrases
    redundant_phrases = [
        "image of", "picture of", "photo of", "graphic of", 
        "screenshot of", "this is", "this shows"
    ]
    
    for phrase in redundant_phrases:
        if alt_text.lower().startswith(phrase):
            alt_text = alt_text[len(phrase):].strip()
    
    # Add context if provided
    if context:
        alt_text = f"{alt_text} - {context}"
    
    # Keep alt text concise (recommended < 125 characters)
    if len(alt_text) > 125:
        alt_text = alt_text[:122] + "..."
    
    return alt_text

def validate_form_accessibility(form_fields: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Validate form fields for accessibility issues.
    
    Args:
        form_fields: List of dictionaries containing form field information
                    (Each dict should have 'type', 'name', 'label', etc.)
        
    Returns:
        List of dictionaries containing validation errors
    """
    errors = []
    
    for field in form_fields:
        field_errors = {}
        field_id = field.get('id') or field.get('name', 'unknown')
        
        # Check for missing label
        if not field.get('label') and not field.get('aria-label') and not field.get('aria-labelledby'):
            field_errors['missing_label'] = f"Field {field_id} is missing a label or aria-label"
        
        # Check for missing input type
        if not field.get('type'):
            field_errors['missing_type'] = f"Field {field_id} is missing input type"
        
        # Check for properly associated labels
        if field.get('label') and not field.get('id'):
            field_errors['unassociated_label'] = f"Label for {field_id} cannot be properly associated without an id attribute"
        
        # Check for descriptive placeholder (should not be used as a label)
        if field.get('placeholder') and not field.get('label') and not field.get('aria-label'):
            field_errors['placeholder_as_label'] = f"Field {field_id} uses placeholder as label, which is not accessible"
        
        # Check for required attribute without proper indication
        if field.get('required') and not field.get('aria-required'):
            field_errors['missing_required_aria'] = f"Required field {field_id} should have aria-required='true'"
        
        # Add errors for this field if any
        if field_errors:
            errors.append({
                'field': field_id,
                'errors': field_errors
            })
    
    return errors

def generate_skip_link() -> str:
    """
    Generate a skip navigation link for keyboard users.
    
    Returns:
        HTML string for the skip link
    """
    return """
    <a href="#main-content" class="skip-link">
        Skip to main content
    </a>
    <style>
        .skip-link {
            position: absolute;
            top: -40px;
            left: 0;
            padding: 8px;
            background-color: #fff;
            color: #000;
            z-index: 100;
            transition: top 0.2s;
        }
        .skip-link:focus {
            top: 0;
        }
    </style>
    """

def set_lang_attribute(html_content: str, lang: str = 'en') -> str:
    """
    Ensure the HTML lang attribute is set correctly.
    
    Args:
        html_content: HTML content string
        lang: Language code
        
    Returns:
        Updated HTML string
    """
    if re.search(r'<html[^>]*lang=', html_content):
        # Replace existing lang attribute
        return re.sub(r'<html([^>]*)lang=(["\']).*?\2', f'<html\\1lang=\\2{lang}\\2', html_content)
    else:
        # Add lang attribute if missing
        return re.sub(r'<html([^>]*?)>', f'<html\\1 lang="{lang}">', html_content)

def accessibility_audit(html_content: str) -> Dict[str, List[str]]:
    """
    Perform a basic accessibility audit on HTML content.
    
    Args:
        html_content: HTML content to audit
        
    Returns:
        Dictionary of accessibility issues grouped by category
    """
    issues = {
        'images': [],
        'forms': [],
        'headings': [],
        'links': [],
        'landmarks': [],
        'contrast': [],
        'general': []
    }
    
    # Check for images without alt
    img_tags = re.findall(r'<img[^>]*>', html_content)
    for img in img_tags:
        if not re.search(r'alt=', img):
            issues['images'].append("Image without alt attribute found")
        elif re.search(r'alt=(["\'])\1', img):
            issues['images'].append("Image with empty alt attribute (should be used only for decorative images)")
    
    # Check for form inputs without labels
    input_tags = re.findall(r'<input[^>]*>', html_content)
    for input_tag in input_tags:
        input_id = re.search(r'id=(["\'])(.*?)\1', input_tag)
        if input_id:
            input_id = input_id.group(2)
            if not re.search(f'for=(["\']){input_id}\\1', html_content) and not re.search(r'aria-label=', input_tag):
                issues['forms'].append(f"Input field with id '{input_id}' has no associated label")
    
    # Check for heading hierarchy
    headings = re.findall(r'<h([1-6])[^>]*>', html_content)
    if headings:
        # Check if H1 exists
        if '1' not in headings:
            issues['headings'].append("No H1 heading found")
        
        # Check for skipped levels
        for i in range(1, 6):
            if str(i+1) in headings and str(i) not in headings:
                issues['headings'].append(f"Heading level H{i} is skipped (found H{i+1} without H{i})")
    
    # Check for empty links
    links = re.findall(r'<a[^>]*>(.*?)</a>', html_content)
    for link_content in links:
        if not link_content.strip() and not re.search(r'aria-label=', link_content):
            issues['links'].append("Empty link found without accessible text")
    
    # Check for ARIA landmarks
    if not re.search(r'<(header|nav|main|footer)[^>]*>|role=(["\'])(banner|navigation|main|contentinfo)\2', html_content):
        issues['landmarks'].append("Missing ARIA landmarks or HTML5 semantic elements")
    
    # Check for language attribute
    if not re.search(r'<html[^>]*lang=', html_content):
        issues['general'].append("Missing lang attribute on html element")
    
    # Check for page title
    if not re.search(r'<title>[^<]+</title>', html_content):
        issues['general'].append("Missing page title")
    
    return issues