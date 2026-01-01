# Purchase Order Generator

A compact Python application for generating PDF purchase orders from product export CSV files.

## Features

- Load product data from CSV exports.
- Multi-select products to include in a single PO.
- Group items by product type with size-based quantity breakdowns.
- Maintain persistent settings for company, vendor, and shipping information.
- Save and select from a history of vendors.
- Generate professional PDF documents using ReportLab.
- Compact GUI for efficient workflow.

## Requirements

- Python 3.x
- reportlab

## Installation

Install the required dependencies:

```bash
pip install reportlab
```

## Usage

### GUI Version (Recommended)

Run the main application:

```bash
python3 main.py
```

1. Click "Load CSV File..." to select your orders data.
2. Select one or more products from the list.
3. Update your Company, Vendor, and Ship To details in the tabs below.
4. Click "Save" on each tab to persist your details.
5. Click "Generate" to create and save the PDF purchase order.

### Command-Line Version

A legacy CLI version is also available:

```bash
python3 generate_purchase_order.py
```

## Project Structure

- main.py: The primary GUI application.
- backend.py: Core business logic for CSV processing and PDF generation.
- generate_purchase_order.py: Command-line interface version.
- settings.json: Local storage for user settings and vendor history.
