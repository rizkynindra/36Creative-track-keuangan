# 36 Creative Financial Tracking System

A premium, mobile-responsive financial tracking web application built with Python (Flask) and Google Sheets. Designed specifically for ease of use across all generations.

## Features

- **Full CRUD**: Create, Read, Update, and Delete income and outcome transactions.
- **Premium UI**: Modern glassmorphic design with smooth animations.
- **Mobile First**: Optimized for smartphones with large touch targets and high readability.
- **Real-time Calculations**: Instant "Total Harga" calculation and live balance updates.
- **Google Sheets Integration**: Persistent data storage directly in your own Google Sheet.
- **Excel Export**: Export all records to `.xlsx` with an automated balance summary.
- **Success Notifications**: Instant visual feedback for every transaction addition.

## Quick Start

### 1. Prerequisites
- Python 3.12
- A Google Cloud Project with the **Google Sheets API** enabled.
- A **Service Account** with a downloaded JSON key named `credentials.json`.

### 2. Google Sheets Setup
1. Create a new Google Sheet named `Financial Tracker`.
2. Share the sheet with the `client_email` address found in your `credentials.json`.

### 3. Installation & Running
Activate the virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install flask gspread oauth2client pandas openpyxl
```

Run the application:
```bash
python app.py
```
Open `http://127.0.0.1:5000` in your browser.

## Tech Stack
- **Backend/Frontend**: Flask (Python)
- **Database**: Google Sheets (via `gspread`)
- **UI/UX**: HTML5, CSS3 (Glassmorphism), Vanilla JS
- **Export**: pandas & openpyxl

## Usage Tips
- Toggle **Jenis Transaksi** (Pemasukan/Pengeluaran) to color-code your entries.
- Use the **Export** button at the top of the history list to generate a summary report.
- The app is fully responsive—bookmark the URL on your phone for easy entry on the go.

---
Built by Rizkynindra for 36 Creative.
