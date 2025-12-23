#!/usr/bin/env python3
"""
Script to convert HTML sample documents to PDF format.

This script converts all HTML financial documents to PDF format for testing
with Azure Document Intelligence.

Requirements:
    pip install weasyprint

Usage:
    python convert_to_pdf.py
"""

import os
from pathlib import Path

def convert_html_to_pdf():
    """Convert all HTML files in sample_data subdirectories to PDF."""
    try:
        from weasyprint import HTML
    except ImportError:
        print("WeasyPrint not installed. Install with: pip install weasyprint")
        print("\nAlternatively, you can manually convert HTML files to PDF:")
        print("1. Open each HTML file in a web browser")
        print("2. Press Ctrl+P (or Cmd+P on Mac)")
        print("3. Select 'Save as PDF' as the destination")
        print("4. Save with the same filename but .pdf extension")
        return

    sample_data_dir = Path(__file__).parent
    
    # Find all HTML files
    html_files = list(sample_data_dir.rglob("*.html"))
    
    if not html_files:
        print("No HTML files found to convert.")
        return
    
    print(f"Found {len(html_files)} HTML files to convert:\n")
    
    for html_file in html_files:
        pdf_file = html_file.with_suffix('.pdf')
        print(f"Converting: {html_file.name} -> {pdf_file.name}")
        
        try:
            HTML(filename=str(html_file)).write_pdf(str(pdf_file))
            print(f"  ✓ Created: {pdf_file}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n✓ Conversion complete!")


def list_sample_documents():
    """List all available sample documents."""
    sample_data_dir = Path(__file__).parent
    
    print("=" * 60)
    print("SAMPLE FINANCIAL DOCUMENTS FOR E2E TESTING")
    print("=" * 60)
    
    categories = {
        "bank_statements": "Bank Statements",
        "invoices": "Invoices",
        "financial_statements": "Financial Statements (P&L, Balance Sheet)",
        "receipts": "Receipts",
        "policy": "Lending Policy Documents"
    }
    
    for folder, description in categories.items():
        folder_path = sample_data_dir / folder
        if folder_path.exists():
            files = list(folder_path.iterdir())
            print(f"\n📁 {description} ({folder}/)")
            for f in files:
                size = f.stat().st_size / 1024  # KB
                print(f"   - {f.name} ({size:.1f} KB)")
        else:
            print(f"\n📁 {description} ({folder}/) - Not found")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("HTML to PDF Converter for Sample Documents")
    print("=" * 60 + "\n")
    
    list_sample_documents()
    
    print("\n" + "-" * 60)
    print("Starting conversion...")
    print("-" * 60 + "\n")
    
    convert_html_to_pdf()
