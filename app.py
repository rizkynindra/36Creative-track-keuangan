import os
import uuid
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import io
from flask import send_file, send_from_directory


app = Flask(__name__)

@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js', mimetype='application/javascript')

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}), 200

# Google Sheets Setup
# NOTE: User needs to provide credentials.json and share the sheet with the service account email
SHEET_NAME = "Financial Tracker"

def get_sheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Try Loading from Env Var first (for Render deployment)
        google_creds_json = os.environ.get("GOOGLE_CREDENTIALS")
        
        if google_creds_json:
            creds_dict = json.loads(google_creds_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
            
        client = gspread.authorize(creds)
        
        try:
            sh = client.open(SHEET_NAME)
            sheet = sh.sheet1
            
            # Check if header exists, if not add it
            header = sheet.row_values(1)
            expected_header = ["id", "date", "type", "detail", "price", "qty", "total_price"]
            if not header or header != expected_header:
                sheet.insert_row(expected_header, 1)
            return sheet
        except gspread.SpreadsheetNotFound:
            sh = client.create(SHEET_NAME)
            sheet = sh.sheet1
            sheet.append_row(["id", "date", "type", "detail", "price", "qty", "total_price"])
            return sheet
    except Exception as e:
        print(f"Google Sheets Error: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    sheet = get_sheet()
    if not sheet:
        return jsonify({"transactions": [], "error": "Could not connect to Google Sheets"}), 500
    
    try:
        # We use expected headers to ensure keys are always correct even if sheet is messy
        expected_keys = ["id", "date", "type", "detail", "price", "qty", "total_price"]
        all_values = sheet.get_all_values()
        
        if len(all_values) <= 1:
            return jsonify({"transactions": [], "total_balance": 0})
            
        all_rows = all_values[1:]
        transactions = []
        total_balance = 0
        
        for row in all_rows:
            # Pad row if columns are missing
            while len(row) < len(expected_keys):
                row.append("")
            
            t = dict(zip(expected_keys, row))
            # Convert numeric strings to numbers
            try:
                t['price'] = float(t['price']) if t['price'] else 0
                t['qty'] = float(t['qty']) if t['qty'] else 0
                t['total_price'] = float(t['total_price']) if t['total_price'] else 0
                
                # Update balance
                if t['type'] == 'income':
                    total_balance += t['total_price']
                else:
                    total_balance -= t['total_price']
            except ValueError:
                t['price'] = 0
                t['qty'] = 0
                t['total_price'] = 0
                
            transactions.append(t)
            
        return jsonify({
            "transactions": list(reversed(transactions)),
            "total_balance": total_balance
        })
    except Exception as e:
        print(f"Error fetching records: {e}")
        return jsonify({"transactions": [], "error": str(e)}), 500

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    data = request.json
    sheet = get_sheet()
    if not sheet:
        return jsonify({"error": "Could not connect to Google Sheets"}), 500
    
    new_transaction = [
        str(uuid.uuid4()),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data.get('type'),
        data.get('detail'),
        data.get('price'),
        data.get('qty'),
        data.get('total_price')
    ]
    sheet.append_row(new_transaction)
    return jsonify({"status": "success"}), 201

@app.route('/api/transactions/<id>', methods=['GET'])
def get_transaction(id):
    sheet = get_sheet()
    if not sheet:
        return jsonify({"error": "Could not connect"}), 500
    
    cell = sheet.find(id)
    if not cell:
        return jsonify({"error": "Not found"}), 404
    
    row_data = sheet.row_values(cell.row)
    headers = sheet.row_values(1)
    transaction = dict(zip(headers, row_data))
    return jsonify(transaction)

@app.route('/api/transactions/<id>', methods=['PUT'])
def update_transaction(id):
    data = request.json
    sheet = get_sheet()
    if not sheet:
        return jsonify({"error": "Could not connect"}), 500
    
    cell = sheet.find(id)
    if not cell:
        return jsonify({"error": "Not found"}), 404
    
    # Update row (keep ID and DATE)
    row_idx = cell.row
    sheet.update_cell(row_idx, 3, data.get('type'))
    sheet.update_cell(row_idx, 4, data.get('detail'))
    sheet.update_cell(row_idx, 5, data.get('price'))
    sheet.update_cell(row_idx, 6, data.get('qty'))
    sheet.update_cell(row_idx, 7, data.get('total_price'))
    
    return jsonify({"status": "updated"})

@app.route('/api/transactions/<id>', methods=['DELETE'])
def delete_transaction(id):
    sheet = get_sheet()
    if not sheet:
        return jsonify({"error": "Could not connect"}), 500
    
    cell = sheet.find(id)
    if not cell:
        return jsonify({"error": "Not found"}), 404
    
    sheet.delete_rows(cell.row)
    return jsonify({"status": "deleted"})

@app.route('/api/export', methods=['GET'])
def export_transactions():
    sheet = get_sheet()
    if not sheet:
        return jsonify({"error": "Could not connect"}), 500
    
    try:
        all_values = sheet.get_all_values()
        if len(all_values) <= 1:
            return jsonify({"error": "No data to export"}), 400
            
        df = pd.DataFrame(all_values[1:], columns=all_values[0])
        
        # Calculate Balance
        df['total_price'] = pd.to_numeric(df['total_price'], errors='coerce').fillna(0)
        income = df[df['type'] == 'income']['total_price'].sum()
        outcome = df[df['type'] == 'outcome']['total_price'].sum()
        balance = income - outcome
        
        # Create an Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Transactions')
            
            # Add Summary at the bottom
            workbook = writer.book
            worksheet = writer.sheets['Transactions']
            last_row = len(df) + 3
            
            worksheet.cell(row=last_row, column=1, value="RINGKASAN")
            worksheet.cell(row=last_row+1, column=1, value="Total Pemasukan")
            worksheet.cell(row=last_row+1, column=2, value=income)
            
            worksheet.cell(row=last_row+2, column=1, value="Total Pengeluaran")
            worksheet.cell(row=last_row+2, column=2, value=outcome)
            
            worksheet.cell(row=last_row+3, column=1, value="Saldo Akhir")
            worksheet.cell(row=last_row+3, column=2, value=balance)
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'transactions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
    except Exception as e:
        print(f"Export Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=3636, host='0.0.0.0')
