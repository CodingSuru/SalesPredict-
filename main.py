from flask import Flask, request, jsonify, render_template, send_from_directory
import pandas as pd
import os
from datetime import datetime
import json
import traceback
import sqlparse
from data_processing import forecast_quantity, preprocess_data, get_total_quantity, load_excel_data
import csv
import xml.etree.ElementTree as ET

app = Flask(__name__)

# Directories
EXCEL_DIR = r"M:\Project\Predication_model\excels"
UPLOAD_DIR = r"M:\Project\Predication_model\upload"

# Ensure directories exist
os.makedirs(EXCEL_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Function to scan files for required fields
def scan_file_for_required_fields(data_df):
    """
    Scan DataFrame for required fields: company name, date, quantity
    Returns a list of missing required fields
    """
    # Define required field variants (case-insensitive search)
    required_fields = {
        'company_name': ['company name', 'company', 'companyname', 'company_name'],
        'date': ['sale date', 'date', 'saledate', 'sale_date'],
        'quantity': ['qty', 'quantity', 'amount']
    }
    
    missing_fields = []
    
    # Convert all column names to lowercase for case-insensitive comparison
    columns_lower = [col.lower() for col in data_df.columns]
    
    # Check for company name field
    has_company = any(col in columns_lower for col in required_fields['company_name'])
    if not has_company:
        missing_fields.append('company name')
    
    # Check for date field
    has_date = any(col in columns_lower for col in required_fields['date'])
    if not has_date:
        missing_fields.append('date')
    
    # Check for quantity field
    has_quantity = any(col in columns_lower for col in required_fields['quantity'])
    if not has_quantity:
        missing_fields.append('quantity')
    
    return missing_fields

# Routes for the web interface
@app.route('/')
def index():
    combined_df = load_excel_data()
    companies = sorted(combined_df['Company'].unique().tolist()) if not combined_df.empty else []
    return render_template('index.html', companies=companies)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Function to parse XML files
def parse_xml_to_dataframe(xml_content):
    try:
        root = ET.fromstring(xml_content)
        data = []
        
        # Try to extract rows from common XML formats
        rows = root.findall('.//row') or root.findall('.//item') or root.findall('.//*')
        
        if not rows:
            return None, "Could not identify row elements in XML"
        
        # Get column names from the first row's children
        first_row = rows[0]
        columns = [child.tag for child in first_row]
        
        # If no columns were found, use attribute names
        if not columns and first_row.attrib:
            columns = list(first_row.attrib.keys())
            # Extract data from attributes
            for row in rows:
                row_data = [row.attrib.get(col, '') for col in columns]
                data.append(row_data)
        else:
            # Extract data from child elements
            for row in rows:
                row_data = [child.text for child in row]
                data.append(row_data)
        
        if not data or not columns:
            return None, "Could not extract meaningful data from XML"
        
        return pd.DataFrame(data, columns=columns), None
    except Exception as e:
        return None, f"Error parsing XML: {str(e)}"

# Function to parse CSV files
def parse_csv_to_dataframe(csv_content):
    try:
        # Try to detect delimiter
        dialect = csv.Sniffer().sniff(csv_content[:1024])
        df = pd.read_csv(pd.StringIO(csv_content), sep=dialect.delimiter)
        return df, None
    except Exception as e:
        try:
            # Try common delimiters if sniffing fails
            for delimiter in [',', ';', '\t', '|']:
                try:
                    df = pd.read_csv(pd.StringIO(csv_content), sep=delimiter)
                    if len(df.columns) > 1:  # Successful parsing should have multiple columns
                        return df, None
                except:
                    continue
        except:
            pass
        return None, f"Error parsing CSV: {str(e)}"

# API endpoint for uploading data
@app.route('/upload_dotnet_data', methods=['POST'])
def upload_dotnet_data():
    try:
        dotnet_df = None
        # Check if the request contains a file
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                print("DEBUG: No file selected in request")
                return jsonify({'error': 'No file selected'}), 400
            
            # Handle different file types
            file_ext = os.path.splitext(file.filename)[1].lower()
            
            if file_ext == '.xlsx' or file_ext == '.xls':
                # Read Excel file
                dotnet_df = pd.read_excel(file)
                print(f"Loaded Excel file with columns: {list(dotnet_df.columns)}")
            
            elif file_ext == '.csv':
                # Read CSV file
                csv_content = file.read().decode('utf-8')
                dotnet_df, error = parse_csv_to_dataframe(csv_content)
                if error:
                    return jsonify({'error': error}), 400
                print(f"Loaded CSV file with columns: {list(dotnet_df.columns)}")
            
            elif file_ext == '.xml':
                # Read XML file
                xml_content = file.read().decode('utf-8')
                dotnet_df, error = parse_xml_to_dataframe(xml_content)
                if error:
                    return jsonify({'error': error}), 400
                print(f"Loaded XML file with columns: {list(dotnet_df.columns)}")
            
            elif file_ext == '.json':
                # Read JSON file
                json_content = file.read().decode('utf-8')
                try:
                    json_data = json.loads(json_content)
                    # Handle different JSON structures
                    if isinstance(json_data, list):
                        dotnet_df = pd.DataFrame(json_data)
                    elif isinstance(json_data, dict) and any(isinstance(json_data[k], list) for k in json_data):
                        # Find the first list in the JSON and use it
                        for k, v in json_data.items():
                            if isinstance(v, list):
                                dotnet_df = pd.DataFrame(v)
                                break
                    else:
                        # Single record as dict
                        dotnet_df = pd.DataFrame([json_data])
                except Exception as e:
                    return jsonify({'error': f'Error parsing JSON file: {str(e)}'}), 400
                print(f"Loaded JSON file with columns: {list(dotnet_df.columns)}")
            
            elif file_ext == '.sql':
                # Read SQL file content
                sql_content = file.read().decode('utf-8')
                print(f"Loaded SQL file content")
                # Parse SQL content to extract table data
                parsed = sqlparse.parse(sql_content)
                rows = []
                for statement in parsed:
                    if statement.get_type() == 'INSERT':
                        # Extract values from INSERT statements
                        tokens = statement.tokens
                        for token in tokens:
                            if isinstance(token, sqlparse.sql.Values):
                                # Extract values between parentheses
                                values = token.get_parameters()
                                for value_group in values:
                                    # Clean and extract values
                                    cleaned_values = []
                                    for val in value_group:
                                        if isinstance(val, sqlparse.sql.Token):
                                            val_str = str(val).strip("'\"")
                                            try:
                                                # Try to convert to appropriate type
                                                val_str = pd.to_numeric(val_str, errors='coerce')
                                                if pd.isna(val_str):
                                                    val_str = str(val).strip("'\"")
                                            except:
                                                val_str = str(val).strip("'\"")
                                            cleaned_values.append(val_str)
                                    rows.append(cleaned_values)
                if not rows:
                    print("DEBUG: No valid INSERT statements found in SQL file")
                    return jsonify({'error': 'No valid INSERT statements found in SQL file'}), 400
                
                # Get column names from the first INSERT statement
                columns = []
                for statement in parsed:
                    if statement.get_type() == 'INSERT':
                        for token in statement.tokens:
                            if isinstance(token, sqlparse.sql.Identifier):
                                table_name = token.get_name()
                                # Assume columns are specified in the INSERT statement
                                for t in statement.tokens:
                                    if isinstance(t, sqlparse.sql.Parenthesis):
                                        cols = t.get_parameters()
                                        columns = [col.get_name() for col in cols if col.get_name()]
                                        break
                        break
                
                if not columns:
                    print("DEBUG: Could not extract column names from SQL file")
                    return jsonify({'error': 'Could not extract column names from SQL file'}), 400
                
                # Create DataFrame from SQL data
                dotnet_df = pd.DataFrame(rows, columns=columns)
                print(f"Parsed SQL data into DataFrame with columns: {list(dotnet_df.columns)}")
            
            elif file_ext == '.txt':
                # Try to parse text file as CSV first
                txt_content = file.read().decode('utf-8')
                dotnet_df, error = parse_csv_to_dataframe(txt_content)
                if error:
                    # If CSV parsing fails, try JSON
                    try:
                        json_data = json.loads(txt_content)
                        if isinstance(json_data, list):
                            dotnet_df = pd.DataFrame(json_data)
                        else:
                            dotnet_df = pd.DataFrame([json_data])
                    except:
                        return jsonify({'error': 'Could not parse text file as CSV or JSON'}), 400
                print(f"Parsed text file with columns: {list(dotnet_df.columns)}")
            
            else:
                print(f"DEBUG: Unsupported file extension: {file_ext}")
                return jsonify({'error': 'Unsupported file format. Please upload .xlsx, .xls, .csv, .json, .xml, .sql, or .txt files'}), 400
        
        # Check if the request contains JSON data (.NET or JSON input)
        elif request.is_json:
            data = request.get_json()
            if not data:
                print("DEBUG: No JSON data provided")
                return jsonify({'error': 'No JSON data provided'}), 400
            dotnet_df = pd.DataFrame(data if isinstance(data, list) else [data])
            print(f"Loaded JSON data with columns: {list(dotnet_df.columns)}")
        
        else:
            form_data = request.form
            if form_data:
                print(f"Received form data: {form_data}")
                try:
                    # Try to parse form data as JSON
                    json_data = json.loads(next(iter(form_data)))
                    dotnet_df = pd.DataFrame(json_data if isinstance(json_data, list) else [json_data])
                    print(f"Parsed form data into DataFrame with columns: {list(dotnet_df.columns)}")
                except Exception as e:
                    print(f"DEBUG: Error parsing form data: {str(e)}")
                    return jsonify({'error': f'Invalid form data: {str(e)}'}), 400
            else:
                print("DEBUG: Invalid input, no JSON or file provided")
                return jsonify({'error': 'Invalid input: Provide JSON data, an Excel file, or a SQL file'}), 400

        # Normalize column names (case-insensitive)
        dotnet_df.columns = dotnet_df.columns.str.strip()
        print(f"Normalized columns: {list(dotnet_df.columns)}")

        # SCAN FOR REQUIRED FIELDS BEFORE PROCESSING
        missing_fields = scan_file_for_required_fields(dotnet_df)
        if missing_fields:
            warning_message = f"Missing required fields: {', '.join(missing_fields)}"
            print(f"DEBUG: {warning_message}")
            return jsonify({'warning': warning_message, 'missing_fields': missing_fields}), 400

        # Map common column names to standard names - case insensitive
        # First, create a lowercase mapping for comparison
        lc_mapping = {
            'company name': 'Company',
            'companyname': 'Company',
            'date': 'Sale Date',
            'saledate': 'Sale Date',
            'quantity': 'Qty',
            'amount': 'Qty'
        }
        
        # Create a case-preserving mapping for actual columns in dataframe
        column_mapping = {}
        for col in dotnet_df.columns:
            col_lower = col.lower()
            if col_lower in lc_mapping:
                column_mapping[col] = lc_mapping[col_lower]
        
        # Rename columns if they exist in the DataFrame
        if column_mapping:
            dotnet_df.rename(columns=column_mapping, inplace=True)
        
        # Standardize column names for processing
        dotnet_df.columns = dotnet_df.columns.str.title()
        print(f"Final columns for processing: {list(dotnet_df.columns)}")

        # Find Qty column (could be named 'Qty', 'Quantity', etc.)
        qty_col = None
        for possible_col in ['Qty', 'Quantity', 'Amount']:
            if possible_col in dotnet_df.columns:
                qty_col = possible_col
                break
                
        # Validate data types for Qty
        if qty_col:
            qty_invalid = pd.to_numeric(dotnet_df[qty_col], errors='coerce').isnull()
            if qty_invalid.any():
                invalid_qty_rows = dotnet_df[qty_invalid][[qty_col]].to_dict()
                print(f"DEBUG: Non-numeric Qty values found: {invalid_qty_rows}")
                return jsonify({'error': f'Quantity column contains non-numeric values: {invalid_qty_rows}'}), 400
            # Convert to numeric type to ensure consistency
            dotnet_df[qty_col] = pd.to_numeric(dotnet_df[qty_col], errors='coerce')
        
        # Find Date column (could be named 'Sale Date', 'Date', etc.)
        date_col = None
        for possible_col in ['Sale Date', 'Date', 'SaleDate']:
            if possible_col in dotnet_df.columns:
                date_col = possible_col
                break
                
        # Validate and convert Sale Date to datetime
        if date_col:
            try:
                dotnet_df[date_col] = pd.to_datetime(dotnet_df[date_col], errors='coerce')
                if dotnet_df[date_col].isnull().any():
                    invalid_dates = dotnet_df[dotnet_df[date_col].isnull()][date_col].index.tolist()
                    print(f"DEBUG: Invalid Date values at rows: {invalid_dates}")
                    return jsonify({'error': f'Invalid Date values at rows: {invalid_dates}'}), 400
                # Convert to DD-MM-YYYY string format for storage
                dotnet_df[date_col] = dotnet_df[date_col].dt.strftime('%d-%m-%Y')
                print(f"DEBUG: {date_col} successfully converted to DD-MM-YYYY")
            except Exception as e:
                print(f"DEBUG: Error parsing date column: {str(e)}")
                return jsonify({'error': f'Error parsing date column: {str(e)}'}), 400

        # Ensure all standard columns exist
        required_std_columns = ['Company', 'Sale Date', 'Item', 'Qty']
        for col in required_std_columns:
            if col not in dotnet_df.columns:
                if col == 'Company' and 'Company Name' in dotnet_df.columns:
                    dotnet_df.rename(columns={'Company Name': 'Company'}, inplace=True)
                elif col == 'Sale Date' and 'Date' in dotnet_df.columns:
                    dotnet_df.rename(columns={'Date': 'Sale Date'}, inplace=True)
                elif col == 'Qty' and 'Quantity' in dotnet_df.columns:
                    dotnet_df.rename(columns={'Quantity': 'Qty'}, inplace=True)
                elif col == 'Item' and dotnet_df.shape[1] > 0:
                    # If Item column is missing, add a default value
                    print(f"WARNING: Adding default 'Item' column")
                    dotnet_df['Item'] = 'DefaultItem'
        
        # Save the DataFrame to Uploaded Data.xlsx, overwriting existing file
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        excel_path = os.path.join(UPLOAD_DIR, "Uploaded Data.xlsx")
        dotnet_df.to_excel(excel_path, index=False)
        print(f"Data saved to {excel_path}")

        # Trigger preprocessing of the new data
        preprocess_data()

        return jsonify({'message': 'Data uploaded and processed successfully', 'row_count': len(dotnet_df)}), 200
    except Exception as e:
        print(f"Exception in /upload_dotnet_data:")
        print(traceback.format_exc())
        return jsonify({'error': f"An error occurred while processing the data: {str(e)}"}), 500

@app.route('/get_quantity', methods=['POST', 'GET'])
def api_get_quantity():
    try:
        # Handle both GET and POST methods
        if request.method == 'GET':
            # For GET requests, look for query parameters
            company = request.args.get('company')
            from_date = request.args.get('from_date')
            to_date = request.args.get('to_date')
        else:  # POST method
            # Try different ways to get the data
            try:
                # Try JSON data first
                if request.is_json:
                    data = request.get_json()
                    company = data.get('company')
                    from_date = data.get('from_date')
                    to_date = data.get('to_date')
                else:
                    # Try form data
                    company = request.form.get('company')
                    from_date = request.form.get('from_date')
                    to_date = request.form.get('to_date')
                    
                    # If not in form directly, maybe it's a JSON string in form data
                    if not (company and from_date and to_date):
                        try:
                            form_data = next(iter(request.form), None)
                            if form_data:
                                json_data = json.loads(form_data)
                                company = json_data.get('company')
                                from_date = json_data.get('from_date')
                                to_date = json_data.get('to_date')
                        except Exception as e:
                            print(f"Error parsing form data as JSON: {str(e)}")
            except Exception as e:
                print(f"Error extracting data from request: {str(e)}")
                return jsonify({'error': f'Could not parse request data: {str(e)}'}), 400
            
        # Validate inputs
        if not company or not from_date or not to_date:
            return jsonify({'error': 'Missing required parameters (company, from_date, to_date)'}), 400
        
        print(f"Processing get_quantity request: company={company}, from_date={from_date}, to_date={to_date}")
        
        # Call get_total_quantity function to process data and save to Excel
        total_quantity = get_total_quantity(company, from_date, to_date)
        
        # Check if an error was returned
        if isinstance(total_quantity, str) and total_quantity.startswith("Error:"):
            return jsonify({'error': total_quantity}), 500
        
        return jsonify({'total_quantity': int(total_quantity)})
            
    except Exception as e:
        print("Exception in /get_quantity:")
        print(traceback.format_exc())
        return jsonify({'error': f"Error processing quantity request: {str(e)}"}), 500

@app.route('/forecast', methods=['POST', 'GET'])
def api_forecast():
    try:
        # Handle both GET and POST methods
        if request.method == 'GET':
            # For GET requests, look for query parameters
            company = request.args.get('company')
            from_date = request.args.get('from_date')
            to_date = request.args.get('to_date')
            frequency = request.args.get('frequency')
        else:  # POST method
            # Try different ways to get the data
            if request.is_json:
                data = request.get_json()
                company = data.get('company')
                from_date = data.get('from_date')
                to_date = data.get('to_date')
                frequency = data.get('frequency')
            else:
                # Try form data
                company = request.form.get('company')
                from_date = request.form.get('from_date')
                to_date = request.form.get('to_date')
                frequency = request.form.get('frequency')
                
                # If not in form directly, maybe it's a JSON string in form data
                if not all([company, from_date, to_date, frequency]):
                    try:
                        form_data = next(iter(request.form), None)
                        if form_data:
                            json_data = json.loads(form_data)
                            company = json_data.get('company')
                            from_date = json_data.get('from_date')
                            to_date = json_data.get('to_date')
                            frequency = json_data.get('frequency')
                    except Exception as e:
                        print(f"Error parsing form data as JSON: {str(e)}")
        
        # Validate inputs
        if not all([company, from_date, to_date, frequency]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Normalize frequency to match expected values
        frequency = frequency.lower().capitalize()
        if frequency not in ['Daily', 'Weekly', 'Monthly']:
            return jsonify({'error': 'Invalid frequency, must be Daily, Weekly, or Monthly'}), 400
        
        print(f"Processing forecast request: company={company}, from_date={from_date}, to_date={to_date}, frequency={frequency}")
        
        # Call forecast function
        predictions = forecast_quantity(company, from_date, to_date, frequency)
        
        # Check if an error was returned
        if isinstance(predictions, str) and predictions.startswith("Error:"):
            return jsonify({'error': predictions}), 500
        
        # Format response to match web interface
        result = [
            {
                'Item': pred[0],
                'Company Name': pred[1],
                'Forecasted Quantity': float(pred[2]),  # Ensure JSON-serializable
                'Date': pred[3]
            }
            for pred in predictions
        ]
        
        return jsonify({'predictions': result})
        
    except Exception as e:
        print("Exception in /forecast:")
        print(traceback.format_exc())
        return jsonify({'error': f"Error forecasting data: {str(e)}"}), 500

@app.route('/get_companies', methods=['GET'])
def get_companies():
    try:
        combined_df = load_excel_data()
        companies = sorted(combined_df['Company'].unique().tolist()) if not combined_df.empty else []
        return jsonify({'companies': companies})
    except Exception as e:
        return jsonify({'error': f"Error retrieving companies: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)