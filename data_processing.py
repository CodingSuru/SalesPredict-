import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score
import os
import re  # Add this import for the re.sub function

# Global variables
combined_df = None
le_item = None
le_company = None
model = None
company_mapping = None

# Define directories
OUTPUT_DIR = r"M:\Project\Predication_model\excels"
UPLOAD_DIR = r"M:\Project\Predication_model\upload"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

def load_excel_data():
    """Load data from Uploaded Data.xlsx with error handling"""
    try:
        file_path = os.path.join(UPLOAD_DIR, "Uploaded Data.xlsx")
        if os.path.exists(file_path):
            print(f"Loading data from {file_path}")
            df = pd.read_excel(file_path)
            # Normalize column names
            df.columns = df.columns.str.strip().str.title()
            print(f"Loaded data with columns: {list(df.columns)}")
            print(f"Data shape: {df.shape}")
            # Clean company names by removing non-breaking spaces and extra whitespace
            if 'Company' in df.columns:
                df['Company'] = df['Company'].str.strip().replace(r'\s+', ' ', regex=True)
                print(f"Company values after cleaning: {df['Company'].unique()}")
            # Remove duplicates based on key columns
            df = df.drop_duplicates(subset=['Company', 'Sale Date', 'Item', 'Qty'], keep='last')
            print(f"Data shape after removing duplicates: {df.shape}")
            return df
        else:
            print(f"Warning: File not found at {file_path}")
            return pd.DataFrame(columns=['Sale Date', 'Item', 'Qty', 'Company'])
    except Exception as e:
        print(f"Error loading Excel data: {str(e)}")
        return pd.DataFrame(columns=['Sale Date', 'Item', 'Qty', 'Company'])

def parse_date(date):
    """Parse date with multiple format attempts"""
    for fmt in ['%d-%m-%Y', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
        try:
            return pd.to_datetime(date, format=fmt, errors='coerce')
        except:
            continue
    return pd.NaT

def preprocess_data():
    global combined_df, le_company, le_item, model, company_mapping
    
    # Reload the data to ensure we have the latest
    try:
        combined_df = load_excel_data()
    except Exception as e:
        print(f"Error reloading data during preprocessing: {str(e)}")
    
    if combined_df.empty:
        print("No data available for preprocessing")
        return
    
    # Check if required columns exist
    required_columns = ['Sale Date', 'Item', 'Qty', 'Company']
    missing_columns = [col for col in required_columns if col not in combined_df.columns]
    if missing_columns:
        print(f"Error: Missing columns in data: {missing_columns}")
        print(f"Available columns: {list(combined_df.columns)}")
        return

    # Validate data types
    if not pd.to_numeric(combined_df['Qty'], errors='coerce').notnull().all():
        print("Error: Qty column contains non-numeric values")
        return
    
    # Convert Sale Date to datetime with multiple format attempts
    try:
        combined_df['Sale Date'] = combined_df['Sale Date'].apply(parse_date)
        if combined_df['Sale Date'].isnull().any():
            invalid_dates = combined_df[combined_df['Sale Date'].isnull()]['Sale Date'].index.tolist()
            invalid_data = combined_df.loc[invalid_dates, ['Sale Date']].to_dict()
            print(f"Error: Invalid Sale Date values at rows: {invalid_dates}")
            print(f"Invalid Sale Date data: {invalid_data}")
            return
    except Exception as e:
        print(f"Error parsing Sale Date: {str(e)}")
        return

    # Store clean company names for comparison later
    company_mapping = combined_df['Company'].unique().tolist()
    print(f"Found companies: {company_mapping}")

    combined_df['Month'] = combined_df['Sale Date'].dt.month
    combined_df['Day'] = combined_df['Sale Date'].dt.day
    combined_df['Year'] = combined_df['Sale Date'].dt.year
    combined_df['DayOfWeek'] = combined_df['Sale Date'].dt.dayofweek
    combined_df['Quarter'] = combined_df['Sale Date'].dt.quarter

    combined_df = combined_df.sort_values('Sale Date')
    combined_df['Lag1'] = combined_df.groupby(['Item', 'Company'])['Qty'].shift(1).fillna(0)
    combined_df['Lag7'] = combined_df.groupby(['Item', 'Company'])['Qty'].shift(7).fillna(0)

    le_company = LabelEncoder()
    le_item = LabelEncoder()

    combined_df['Company_Encoded'] = le_company.fit_transform(combined_df['Company'])
    combined_df['Item_Encoded'] = le_item.fit_transform(combined_df['Item'])

    features = ['Item_Encoded', 'Company_Encoded', 'Month', 'Day', 'Year', 'DayOfWeek', 'Quarter', 'Lag1', 'Lag7']
    X = combined_df[features]
    y = combined_df['Qty']

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_squared_error')
    print(f"Cross-validation MSE: {-cv_scores.mean():.2f} (+/- {cv_scores.std() * 2:.2f})")
    model.fit(X, y)
    print("Model training complete")

# Initial data load and preprocessing
try:
    combined_df = load_excel_data()
    if not combined_df.empty:
        preprocess_data()
except Exception as e:
    print(f"Error during initial data load: {str(e)}")
    combined_df = pd.DataFrame(columns=['Sale Date', 'Item', 'Qty', 'Company'])

# DATA FETCHER FUNCTIONS
def get_total_quantity(company, from_date, to_date):
    try:
        # Ensure we have the latest data
        global combined_df
        combined_df = load_excel_data()
            
        if combined_df.empty:
            print("Warning: No data available for quantity calculation")
            # Create an empty result and save it
            result = {
                'Company Name': company,
                'From Date': pd.to_datetime(from_date).strftime('%Y-%m-%d'),
                'To Date': pd.to_datetime(to_date).strftime('%Y-%m-%d'),
                'Total Quantity': 0
            }
            df_result = pd.DataFrame([result])
            
            # Save to data_fetched.xlsx
            file_path = os.path.join(OUTPUT_DIR, 'data_fetched.xlsx')
            df_result.to_excel(file_path, index=False)
            print(f"Empty result saved to {file_path}")
            
            return 0
        
        # Check if Company column exists
        if 'Company' not in combined_df.columns:
            print(f"Error: 'Company' column not found. Available columns: {list(combined_df.columns)}")
            return "Error: 'Company' column not found in the data"
        
        # Parse input dates
        from_date = pd.to_datetime(from_date)
        to_date = pd.to_datetime(to_date)
        
        print(f"DEBUG - Input: company={company}, from_date={from_date}, to_date={to_date}")
        print(f"DEBUG - combined_df shape: {combined_df.shape}")
        print(f"DEBUG - company values: {combined_df['Company'].unique()}")
        
        # Ensure 'Sale Date' is in datetime format
        if 'Sale Date' not in combined_df.columns:
            print(f"Error: 'Sale Date' column not found. Available columns: {list(combined_df.columns)}")
            return "Error: 'Sale Date' column not found in the data"
        
        combined_df['Sale Date'] = combined_df['Sale Date'].apply(parse_date)
        
        # Check for null values in the date column
        if combined_df['Sale Date'].isnull().any():
            print("Warning: Some dates could not be parsed properly")
            combined_df = combined_df.dropna(subset=['Sale Date'])
        
        if combined_df.empty:
            print("Warning: No valid data after cleaning")
            return 0
            
        print(f"DEBUG - Data date range: {combined_df['Sale Date'].min()} to {combined_df['Sale Date'].max()}")

        # Clean company parameter to match data format - FIXED THIS LINE
        clean_company = company.strip().replace('\xa0', ' ')
        clean_company = re.sub(r'\s+', ' ', clean_company)  # Use re.sub instead of string replace with regex
        print(f"DEBUG - Cleaned input company name: '{clean_company}'")
        
        # Compare company names by normalized strings (case-insensitive, normalized spaces)
        company_match = combined_df['Company'].str.lower().str.strip() == clean_company.lower().strip()
        
        # If no exact match, try fuzzy matching
        if company_match.sum() == 0:
            print(f"WARNING: No exact match for company '{clean_company}'. Available companies: {combined_df['Company'].unique()}")
            # Try to find the closest match
            for comp in combined_df['Company'].unique():
                if clean_company.lower().strip() in comp.lower().strip() or comp.lower().strip() in clean_company.lower().strip():
                    print(f"Found approximate match: '{comp}' for '{clean_company}'")
                    company_match = combined_df['Company'] == comp
                    break
        
        date_min_match = combined_df['Sale Date'] >= from_date
        date_max_match = combined_df['Sale Date'] <= to_date
        
        print(f"DEBUG - Records matching company '{clean_company}': {company_match.sum()}")
        print(f"DEBUG - Records on or after {from_date}: {date_min_match.sum()}")
        print(f"DEBUG - Records on or before {to_date}: {date_max_match.sum()}")
        
        filtered_data = combined_df[company_match & date_min_match & date_max_match]
        
        print(f"DEBUG - Filtered data shape: {filtered_data.shape}")
        if not filtered_data.empty:
            print(f"DEBUG - Filtered data sample:\n{filtered_data[['Sale Date', 'Item', 'Qty']].head().to_string()}")
        
        if filtered_data.empty:
            print(f"DEBUG - No data found for company '{clean_company}' between {from_date} and {to_date}")
            total_qty = 0
        else:
            total_qty = filtered_data['Qty'].sum()
            print(f"DEBUG - Raw total quantity: {total_qty}")
            
            total_qty = total_qty if not pd.isna(total_qty) else 0
            total_qty = int(total_qty) if isinstance(total_qty, (int, float, np.number)) else 0
            
            print(f"DEBUG - Final total quantity (Python type {type(total_qty)}): {total_qty}")
        
        # Create result dataframe
        result = {
            'Company Name': company,
            'From Date': from_date.strftime('%Y-%m-%d'),
            'To Date': to_date.strftime('%Y-%m-%d'),
            'Total Quantity': total_qty
        }
        df_result = pd.DataFrame([result])
        
        # Save to data_fetched.xlsx
        file_path = os.path.join(OUTPUT_DIR, 'data_fetched.xlsx')
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Check if file exists to append or create new
        if os.path.exists(file_path):
            try:
                existing_df = pd.read_excel(file_path)
                # Check for duplicate based on Company Name, From Date, and To Date
                existing_df['From Date'] = pd.to_datetime(existing_df['From Date']).dt.strftime('%Y-%m-%d')
                existing_df['To Date'] = pd.to_datetime(existing_df['To Date']).dt.strftime('%Y-%m-%d')
                is_duplicate = existing_df[
                    (existing_df['Company Name'].str.strip() == company.strip()) &
                    (existing_df['From Date'] == from_date.strftime('%Y-%m-%d')) &
                    (existing_df['To Date'] == to_date.strftime('%Y-%m-%d'))
                ]
                if not is_duplicate.empty:
                    print(f"Duplicate record found for {company} from {from_date} to {to_date}, skipping append")
                    return total_qty
                df_result = pd.concat([existing_df, df_result], ignore_index=True)
            except Exception as e:
                print(f"Error reading existing file, creating new one: {str(e)}")
        else:
            print(f"Creating new file: {file_path}")
        
        # Save the result
        try:
            df_result.to_excel(file_path, index=False)
            print(f"Total quantity data saved to {file_path}")
        except Exception as e:
            print(f"Error saving total quantity data: {str(e)}")
        
        return total_qty
    except Exception as e:
        import traceback
        print(f"ERROR in get_total_quantity: {str(e)}")
        print(traceback.format_exc())
        return f"Error: {str(e)}"

# FORECASTER FUNCTIONS
def forecast_quantity(company, from_date, to_date, frequency):
    try:
        from_date = pd.to_datetime(from_date)
        to_date = pd.to_datetime(to_date)
        daily_range = pd.date_range(start=from_date, end=to_date, freq='D')
        
        if model is None or le_item is None or le_company is None:
            return "Error: Model not trained. Please upload data first."
            
        if combined_df.empty:
            return "Error: No data available for forecasting."
        
        # Normalize company names before checking - ALSO FIX THIS LINE FOR CONSISTENCY
        company = company.strip()
        company = re.sub(r'\s+', ' ', company.replace('\xa0', ' '))

        # Find the matching company in the encoder
        matched_company = None
        for cname in le_company.classes_:
            if cname.strip() == company:
                matched_company = cname
                break

        if matched_company is None:
            return f"Error: Company '{company}' not found in trained data."

        company = matched_company  # use the correct company name from trained data

        unique_items = combined_df['Item'].unique()
        item_predictions = {item: {} for item in unique_items}
        item_results = []

        # Generate daily predictions
        for item in unique_items:
            last_data_item = combined_df[
                (combined_df['Item'] == item) &
                (combined_df['Company'].str.strip() == company.strip())
            ].sort_values('Sale Date').tail(7)
            lag1_item = last_data_item['Qty'].iloc[-1] if not last_data_item.empty else 0
            lag7_item = last_data_item['Qty'].iloc[-7] if len(last_data_item) >= 7 else 0
            
            for date in daily_range:
                input_data = pd.DataFrame({
                    'Item_Encoded': [le_item.transform([item])[0]],
                    'Company_Encoded': [le_company.transform([company])[0]],
                    'Month': [date.month],
                    'Day': [date.day],
                    'Year': [date.year],
                    'DayOfWeek': [date.dayofweek],
                    'Quarter': [date.quarter],
                    'Lag1': [lag1_item],
                    'Lag7': [lag7_item]
                })
                pred = model.predict(input_data)[0]
                item_predictions[item][date] = round(pred, 2)
                lag7_item = lag1_item
                lag1_item = pred

            # Process results based on frequency
            daily_data = pd.Series(item_predictions[item]).reset_index()
            daily_data.columns = ['Date', 'Qty']
            daily_data['Date'] = pd.to_datetime(daily_data['Date'])

            if frequency == 'Daily':
                item_result = [(item, company, qty, date.strftime('%d-%b-%Y')) 
                              for date, qty in item_predictions[item].items()]
            elif frequency == 'Weekly':
                weekly_data = daily_data.copy()
                weekly_data['Week'] = weekly_data['Date'].dt.isocalendar().week
                weekly_data['Year'] = weekly_data['Date'].dt.year
                weekly_data = weekly_data.groupby(['Year', 'Week']).agg({'Qty': 'sum', 'Date': 'last'})
                item_result = [(item, company, round(qty, 2), 
                               f"{last_date.strftime('%d-%b-%Y')} (Week {week})")
                              for (year, week), (qty, last_date) in weekly_data.iterrows()]
            elif frequency == 'Monthly':
                monthly_data = daily_data.copy()
                monthly_data['Month'] = daily_data['Date'].dt.month
                monthly_data['Year'] = daily_data['Date'].dt.year
                monthly_data = monthly_data.groupby(['Year', 'Month']).agg({'Qty': 'sum', 'Date': 'last'})
                item_result = [(item, company, round(qty, 2), 
                               f"{last_date.strftime('%d-%b-%Y')} (Month {month})")
                              for (year, month), (qty, last_date) in monthly_data.iterrows()]
            else:
                return "Error: Invalid frequency"
            item_results.extend(item_result)
        
        # Save forecast result to Excel
        df_forecast = pd.DataFrame(item_results, columns=['Item', 'Company Name', 'Forecasted Quantity', 'Date'])

        # Determine filename based on frequency
        file_map = {
            'Daily': 'forecasting_daily.xlsx',
            'Weekly': 'forecasting_weekly.xlsx',
            'Monthly': 'forecasting_monthly.xlsx'
        }
        filename = file_map.get(frequency, 'forecasting_output.xlsx')
        file_path = os.path.join(OUTPUT_DIR, filename)

        # Create directory if not exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Save the forecast to Excel
        try:
            df_forecast.to_excel(file_path, index=False)
            print(f"Forecasting result saved to {file_path}")
        except Exception as e:
            print(f"Error saving forecast data: {str(e)}")

        return item_results

    except Exception as e:
        import traceback
        print(f"ERROR in forecast_quantity: {str(e)}")
        print(traceback.format_exc())
        return f"Error: {str(e)}"