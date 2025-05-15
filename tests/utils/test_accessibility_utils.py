import unittest
from app.utils.accessibility_utils import (
    hex_to_rgb, rgb_to_hex, calculate_luminance, calculate_contrast_ratio,
    check_contrast_compliance, generate_alt_text, set_lang_attribute,
    validate_form_accessibility, create_aria_attributes, accessibility_audit
)

class TestAccessibilityUtils(unittest.TestCase):
    """Test suite for the accessibility utilities."""

    def test_hex_to_rgb(self):
        """Test conversion from hex to RGB."""
        self.assertEqual(hex_to_rgb('#ffffff'), (255, 255, 255))
        self.assertEqual(hex_to_rgb('000000'), (0, 0, 0))
        self.assertEqual(hex_to_rgb('#ff5733'), (255, 87, 51))
        self.assertEqual(hex_to_rgb('#f00'), (255, 0, 0))

    def test_rgb_to_hex(self):
        """Test conversion from RGB to hex."""
        self.assertEqual(rgb_to_hex((255, 255, 255)), '#ffffff')
        self.assertEqual(rgb_to_hex((0, 0, 0)), '#000000')
        self.assertEqual(rgb_to_hex((255, 87, 51)), '#ff5733')

    def test_calculate_luminance(self):
        """Test luminance calculation."""
        # Black should have 0 luminance
        self.assertAlmostEqual(calculate_luminance((0, 0, 0)), 0.0, places=4)
        # White should have 1 luminance
        self.assertAlmostEqual(calculate_luminance((255, 255, 255)), 1.0, places=4)
        # Gray should have intermediate luminance
        self.assertTrue(0 < calculate_luminance((128, 128, 128)) < 1)

    def test_calculate_contrast_ratio(self):
        """Test contrast ratio calculation."""
        # Black and white should have highest contrast ratio (21:1)
        self.assertAlmostEqual(calculate_contrast_ratio((0, 0, 0), (255, 255, 255)), 21.0, places=1)
        # Same colors should have lowest contrast ratio (1:1)
        self.assertAlmostEqual(calculate_contrast_ratio((128, 128, 128), (128, 128, 128)), 1.0, places=4)
        # Check specific colors
        self.assertTrue(4 < calculate_contrast_ratio((51, 51, 255), (255, 255, 255)) < 5)  # Blue on white

    def test_check_contrast_compliance(self):
        """Test contrast compliance checking."""
        # Black on white - should pass all levels
        self.assertTrue(check_contrast_compliance('#000000', '#ffffff', 'A'))
        self.assertTrue(check_contrast_compliance('#000000', '#ffffff', 'AA'))
        self.assertTrue(check_contrast_compliance('#000000', '#ffffff', 'AAA'))
        
        # Medium blue on white - should pass AA but not AAA
        self.assertTrue(check_contrast_compliance('#0000cc', '#ffffff', 'AA'))
        self.assertFalse(check_contrast_compliance('#0000cc', '#ffffff', 'AAA'))
        
        # Light gray on white - should fail all levels
        self.assertFalse(check_contrast_compliance('#cccccc', '#ffffff', 'A'))
        self.assertFalse(check_contrast_compliance('#cccccc', '#ffffff', 'AA'))
        self.assertFalse(check_contrast_compliance('#cccccc', '#ffffff', 'AAA'))

    def test_generate_alt_text(self):
        """Test alt text generation."""
        # Basic description
        self.assertEqual(generate_alt_text("A mountain landscape"), "A mountain landscape")
        
        # With context
        self.assertEqual(
            generate_alt_text("A mountain landscape", "Used in nature gallery"), 
            "A mountain landscape - Used in nature gallery"
        )
        
        # Strip redundant phrases
        self.assertEqual(generate_alt_text("image of a dog"), "a dog")
        
        # Long text should be truncated
        long_text = "This is a very long description that exceeds the recommended 125 character limit" * 3
        self.assertTrue(len(generate_alt_text(long_text)) <= 125)
        self.assertTrue(generate_alt_text(long_text).endswith("..."))

    def test_set_lang_attribute(self):
        """Test setting HTML lang attribute."""
        # Add lang attribute if missing
        html_without_lang = "<html><head><title>Test</title></head><body></body></html>"
        self.assertEqual(
            set_lang_attribute(html_without_lang, "en"),
            "<html lang=\"en\"><head><title>Test</title></head><body></body></html>"
        )
        
        # Replace existing lang attribute
        html_with_lang = "<html lang=\"fr\"><head><title>Test</title></head><body></body></html>"
        self.assertEqual(
            set_lang_attribute(html_with_lang, "es"),
            "<html lang=\"es\"><head><title>Test</title></head><body></body></html>"
        )

    def test_validate_form_accessibility(self):
        """Test form accessibility validation."""
        # Valid form field
        valid_field = [
            {
                'id': 'name',
                'name': 'name',
                'type': 'text',
                'label': 'Full Name',
                'required': True,
                'aria-required': 'true'
            }
        ]
        self.assertEqual(validate_form_accessibility(valid_field), [])
        
        # Invalid form fields
        invalid_fields = [
            {
                'name': 'email',  # Missing ID for label association
                'type': 'email',
                'label': 'Email'  # Has label but no ID
            },
            {
                'id': 'password',
                'name': 'password',
                'type': 'password',
                'placeholder': 'Enter password',  # Using placeholder as label
                'required': True  # Required but no aria-required
            }
        ]
        
        errors = validate_form_accessibility(invalid_fields)
        self.assertEqual(len(errors), 2)
        
        # Check first field errors
        self.assertEqual(errors[0]['field'], 'email')
        self.assertIn('unassociated_label', errors[0]['errors'])
        
        # Check second field errors
        self.assertEqual(errors[1]['field'], 'password')
        self.assertIn('missing_label', errors[1]['errors'])
        self.assertIn('placeholder_as_label', errors[1]['errors'])
        self.assertIn('missing_required_aria', errors[1]['errors'])

    def test_create_aria_attributes(self):
        """Test ARIA attributes creation."""
        # Button attributes
        self.assertEqual(
            create_aria_attributes('button', 'Submit'),
            {'aria-label': 'Submit'}
        )
        
        # Alert attributes
        self.assertEqual(
            create_aria_attributes('alert'),
            {'role': 'alert', 'aria-live': 'assertive'}
        )
        
        # Dialog attributes
        self.assertEqual(
            create_aria_attributes('dialog', 'dialog-title'),
            {'role': 'dialog', 'aria-modal': 'true', 'aria-labelledby': 'dialog-title'}
        )

    def test_accessibility_audit(self):
        """Test accessibility audit functionality."""
        # HTML with accessibility issues
        problematic_html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <h2>Missing H1</h2>
            <img src="logo.png">
            <a href="#"></a>
            <input type="text" id="name">
        </body>
        </html>
        """
        
        issues = accessibility_audit(problematic_html)
        
        # Check for expected issues
        self.assertIn("Image without alt attribute found", issues['images'])
        self.assertIn("Empty link found without accessible text", issues['links'])
        self.assertIn("Input field with id 'name' has no associated label", issues['forms'])
        self.assertIn("No H1 heading found", issues['headings'])
        self.assertIn("Missing lang attribute on html element", issues['general'])
        self.assertIn("Missing ARIA landmarks or HTML5 semantic elements", issues['landmarks'])
        
        # HTML with better accessibility
        good_html = """
        <html lang="en">
        <head><title>Test Page</title></head>
        <body>
            <header role="banner">
                <h1>Main Heading</h1>
            </header>
            <nav role="navigation">
                <a href="#" aria-label="Home">Home</a>
            </nav>
            <main id="main-content">
                <img src="logo.png" alt="Company Logo">
                <label for="name">Name:</label>
                <input type="text" id="name">
            </main>
            <footer role="contentinfo">
                <p>&copy; 2023</p>
            </footer>
        </body>
        </html>
        """
        
        issues = accessibility_audit(good_html)
        
        # Check that issues are resolved
        self.assertEqual(len(issues['images']), 0)
        self.assertEqual(len(issues['links']), 0)
        self.assertEqual(len(issues['forms']), 0)
        self.assertEqual(len(issues['headings']), 0)
        self.assertEqual(len(issues['general']), 0)
        self.assertEqual(len(issues['landmarks']), 0)


if __name__ == '__main__':
    unittest.main()