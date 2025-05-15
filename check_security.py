#!/usr/bin/env python3
"""
Security Checking Script

This script performs security checks on the GA4 Analytics Dashboard codebase.
It checks for:
1. Credentials and sensitive keys accidentally committed
2. Vulnerabilities in dependencies
3. Common security pitfalls in the code

Usage:
    python check_security.py

Note: This is a simple script for demonstration purposes.
For production, consider using professional security scanning tools.
"""

import os
import re
import sys
import glob
import json
import logging
from typing import List, Dict, Any, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Patterns that might indicate security issues
SENSITIVE_PATTERNS = [
    r'password\s*=\s*[\'"][^\'"]+[\'"]',
    r'secret\s*=\s*[\'"][^\'"]+[\'"]',
    r'key\s*=\s*[\'"][^\'"]+[\'"]',
    r'token\s*=\s*[\'"][^\'"]+[\'"]',
    r'-----BEGIN (\w+) PRIVATE KEY-----',
    r'AIza[0-9A-Za-z-_]{35}',  # Google API Key
    r'ya29\.[0-9A-Za-z\-_]+',  # Google OAuth Access Token
]

# Files and directories to exclude
EXCLUDE_PATHS = [
    '.git',
    'venv',
    'env',
    '.venv',
    '.env',
    'node_modules',
    '.pytest_cache',
    '__pycache__',
    'keys',  # This directory should contain .gitignore directives
    'tests',  # Skip tests that might have dummy credentials
]

def check_for_sensitive_data() -> List[Dict[str, Any]]:
    """
    Check for sensitive data in the codebase.
    
    Returns:
        List of findings (file path, line number, pattern matched)
    """
    logger.info("Checking for sensitive data in code...")
    findings = []
    
    # Get all Python and JSON files
    files = glob.glob('**/*.py', recursive=True) + glob.glob('**/*.json', recursive=True)
    
    # Filter out excluded paths
    files = [f for f in files if not any(exclude in f for exclude in EXCLUDE_PATHS)]
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    for pattern in SENSITIVE_PATTERNS:
                        if re.search(pattern, line):
                            findings.append({
                                'file': file_path,
                                'line': i,
                                'pattern': pattern,
                                'content': line.strip()
                            })
        except Exception as e:
            logger.warning(f"Error reading {file_path}: {e}")
    
    return findings

def check_dependencies() -> List[Dict[str, Any]]:
    """
    Check dependencies for known vulnerabilities.
    
    Returns:
        List of vulnerable dependencies
    """
    logger.info("Checking dependencies for vulnerabilities...")
    vulnerabilities = []
    
    # In a real implementation, this would use a security database API
    # For this example, we'll just check against a dummy list
    known_vulnerable = {
        'flask': ['0.12.0', '0.12.1', '0.12.2'],
        'django': ['1.8.0', '1.9.0', '2.0.0'],
        'requests': ['2.3.0', '2.4.0', '2.5.0'],
    }
    
    # Check requirements.txt
    if os.path.exists('requirements.txt'):
        try:
            with open('requirements.txt', 'r') as f:
                for line in f:
                    # Parse requirement line
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Simple parsing - would need more robust parsing in real implementation
                        parts = re.split(r'[=<>]', line)
                        if len(parts) >= 2:
                            package = parts[0].strip().lower()
                            version = parts[1].strip()
                            
                            # Check if in known vulnerable list
                            if package in known_vulnerable and version in known_vulnerable[package]:
                                vulnerabilities.append({
                                    'package': package,
                                    'version': version,
                                    'severity': 'HIGH',
                                    'recommendation': 'Update to latest version'
                                })
        except Exception as e:
            logger.warning(f"Error checking dependencies: {e}")
    
    return vulnerabilities

def check_common_security_pitfalls() -> List[Dict[str, Any]]:
    """
    Check for common security pitfalls in code.
    
    Returns:
        List of potential security issues
    """
    logger.info("Checking for common security pitfalls...")
    issues = []
    
    # Patterns to check for
    pitfalls = {
        r'eval\s*\(': 'Use of eval() is potentially dangerous',
        r'exec\s*\(': 'Use of exec() is potentially dangerous',
        r'os\.system\s*\(': 'os.system() may be vulnerable to command injection',
        r'subprocess\.call\s*\(.*shell\s*=\s*True': 'shell=True can be vulnerable to command injection',
        r'flask.*debug\s*=\s*True': 'Debug mode should not be enabled in production',
        r'@app\.route.*methods=\[\'GET\',\s*\'POST\'\]': 'Consider using specific HTTP methods for routes',
        r'SECRET_KEY\s*=\s*[\'"][^\'"]{,32}[\'"]': 'SECRET_KEY might not be secure enough',
        r'render_template_string\s*\(': 'render_template_string can be vulnerable to SSTI',
        r'\.format\s*\(.*request': 'String formatting with request data can be dangerous',
        r'json\.loads\s*\(.*request': 'Parsing JSON from requests without validation',
        r'cursor\.execute\s*\(.*\+.*request': 'SQL injection risk in database query',
        r'\.save\s*\(.*request\.files': 'File upload without proper validation',
    }
    
    # Get all Python files
    python_files = glob.glob('**/*.py', recursive=True)
    
    # Filter out excluded paths
    python_files = [f for f in python_files if not any(exclude in f for exclude in EXCLUDE_PATHS)]
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                for pattern, description in pitfalls.items():
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        # Get line number
                        line_number = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': file_path,
                            'line': line_number,
                            'description': description,
                            'severity': 'MEDIUM'
                        })
        except Exception as e:
            logger.warning(f"Error checking {file_path}: {e}")
    
    return issues

def check_accessibility() -> List[Dict[str, Any]]:
    """
    Check for accessibility issues in templates.
    
    Returns:
        List of potential accessibility issues
    """
    logger.info("Checking for accessibility issues...")
    issues = []
    
    from app.utils.accessibility_utils import accessibility_audit
    
    # Get all HTML template files
    template_files = glob.glob('app/templates/**/*.html', recursive=True)
    
    for file_path in template_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Perform accessibility audit
                audit_results = accessibility_audit(content)
                
                # Record issues
                for category, category_issues in audit_results.items():
                    for issue in category_issues:
                        issues.append({
                            'file': file_path,
                            'category': category,
                            'description': issue,
                            'severity': 'MEDIUM'
                        })
        except Exception as e:
            logger.warning(f"Error checking {file_path}: {e}")
    
    return issues

def main() -> int:
    """
    Main function to run all security checks.
    
    Returns:
        Exit code (0 for success, non-zero for issues)
    """
    print("=" * 80)
    print("GA4 Analytics Dashboard Security Check")
    print("=" * 80)
    
    # Check for sensitive data
    sensitive_findings = check_for_sensitive_data()
    print(f"\nSensitive Data Findings: {len(sensitive_findings)}")
    for i, finding in enumerate(sensitive_findings, 1):
        print(f"  {i}. {finding['file']}:{finding['line']} - {finding['content']}")
    
    # Check dependencies
    vulnerabilities = check_dependencies()
    print(f"\nVulnerable Dependencies: {len(vulnerabilities)}")
    for i, vuln in enumerate(vulnerabilities, 1):
        print(f"  {i}. {vuln['package']} {vuln['version']} - {vuln['severity']}: {vuln['recommendation']}")
    
    # Check for common security pitfalls
    pitfalls = check_common_security_pitfalls()
    print(f"\nSecurity Pitfalls: {len(pitfalls)}")
    for i, issue in enumerate(pitfalls, 1):
        print(f"  {i}. {issue['file']}:{issue['line']} - {issue['description']} ({issue['severity']})")
    
    # Check for accessibility issues
    try:
        accessibility_issues = check_accessibility()
        print(f"\nAccessibility Issues: {len(accessibility_issues)}")
        for i, issue in enumerate(accessibility_issues, 1):
            print(f"  {i}. {issue['file']} - {issue['category']}: {issue['description']}")
    except ImportError:
        print("\nAccessibility checker not available")
    
    # Summary
    total_issues = len(sensitive_findings) + len(vulnerabilities) + len(pitfalls)
    print("\n" + "=" * 80)
    print(f"Total Issues: {total_issues}")
    print("=" * 80)
    
    # Return non-zero if issues found
    return 1 if total_issues > 0 else 0

if __name__ == '__main__':
    sys.exit(main())