# Accessibility Guidelines

## Overview

The GA4 Analytics Dashboard is committed to WCAG AA compliance to ensure accessibility for all users. This document outlines the guidelines and utilities available to help maintain accessibility standards throughout the application.

## WCAG AA Requirements

The Web Content Accessibility Guidelines (WCAG) 2.1 AA level requires:

- **Perceivable**: Information must be presentable to users in ways they can perceive
- **Operable**: Interface components must be operable by all users
- **Understandable**: Information and interface operation must be understandable
- **Robust**: Content must be robust enough to be interpreted by a wide variety of user agents

## Built-in Accessibility Utilities

The application provides utilities to help maintain compliance:

### Color Contrast

```python
from app.utils import check_contrast_compliance

# Check if colors meet contrast requirements
is_compliant = check_contrast_compliance('#007bff', '#ffffff', 'AA')
```

In templates:

```html
{% if color1|check_contrast(color2, 'AA') %}
  <!-- Colors are compliant -->
{% else %}
  <!-- Use alternative colors -->
{% endif %}
```

### Alt Text Generation

```python
from app.utils import generate_alt_text

# Generate appropriate alt text
alt = generate_alt_text("Graph showing user engagement over time", "Dashboard chart")
```

In templates:

```html
<img src="{{ image_url }}" alt="{{ image_description|alt_text(context) }}">
```

### Skip Links

```python
from app.utils import generate_skip_link

# Add skip link to template
skip_link_html = generate_skip_link()
```

### ARIA Attributes

```python
from app.utils import create_aria_attributes

# Create appropriate ARIA attributes for an element
aria_attrs = create_aria_attributes('button', 'Submit Form')
```

In templates:

```html
<button {% for key, value in 'button'|aria_attrs('Submit')|items %}{{ key }}="{{ value }}" {% endfor %}>
  Submit
</button>
```

### Accessibility Audit

```python
from app.utils import accessibility_audit

# Check HTML content for accessibility issues
issues = accessibility_audit(html_content)
```

## Implementation Checklist

When implementing new features, ensure:

### HTML Structure

- [ ] Use semantic HTML elements (`header`, `nav`, `main`, `footer`, etc.)
- [ ] Include proper heading hierarchy (h1-h6)
- [ ] Set the language attribute in HTML tag
- [ ] Include a skip link at the top of the page
- [ ] Ensure all form fields have associated labels

### Images and Media

- [ ] All images have appropriate alt text (empty for decorative images)
- [ ] Complex graphics have detailed descriptions
- [ ] Videos have captions and transcripts
- [ ] No information is conveyed through color alone

### Interaction

- [ ] All functionality is keyboard accessible
- [ ] Focus indicators are visible
- [ ] Sufficient time is provided for interactions
- [ ] Users can easily navigate and find content
- [ ] Input errors are clearly identified and described

### Content

- [ ] Text is readable (minimum contrast ratio 4.5:1)
- [ ] Text can be resized up to 200% without loss of content
- [ ] Page is usable with screen readers
- [ ] Tables have proper headers and captions
- [ ] Links have descriptive text (not "click here")

## Testing Accessibility

1. **Automated Testing**:
   - Use the built-in `accessibility_audit` function
   - Run the `check_security.py` script which includes accessibility checks

2. **Manual Testing**:
   - Test with keyboard navigation only
   - Test with screen readers (VoiceOver, NVDA, JAWS)
   - Verify focus management in interactive components
   - Check for proper color contrast in all states (hover, active, etc.)

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/TR/WCAG21/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [Color Contrast Analyser Tool](https://developer.paciellogroup.com/resources/contrastanalyser/)