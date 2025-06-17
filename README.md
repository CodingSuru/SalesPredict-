📊 #Sales Predict 🚀

Welcome to Sales Predict! A Flask-based web app for processing sales data, generating forecasts, and calculating total quantities. Supports multiple file formats and offers a user-friendly interface for data analysis and predictions. 🎉

📋 #Overview

Upload sales data (Excel, CSV, JSON, XML, SQL, TXT) 📂
Calculate total quantities for companies in a date range 📈
Forecast sales (Daily, Weekly, Monthly) using Random Forest 🧠
Interactive web interface 🌐

Built with Python, Flask, Pandas, and Scikit-learn, with robust error handling and data validation. 💻

🛠️ #Features

File Upload: Supports various formats with validation 📥
Data Processing: Cleans and preprocesses data 🧹
Quantity Calculation: Totals for a company and date range 📊
Forecasting: Daily, Weekly, or Monthly predictions 🔮
Web UI: Easy data upload and results viewing 🌍
Error Handling: Detailed logs and error messages 🔍

📁 #Structure
📦 SalesPredict
├── 📂 excels          # Output Excel files
├── 📂 upload          # Uploaded data
├── 📂 static          # CSS, JS files
├── 📂 templates       # HTML templates
├── 📜 main.py         # Flask app
├── 📜 data_processing.py  # Data processing & forecasting
└── 📜 README.md       # Documentation

🛠️ #Setup
Prerequisites

Python 3.8+ 🐍
pip 📦

Installation

Clone the repo:
git clone <repository-url>
cd SalesPredict


Install dependencies:
pip install flask pandas scikit-learn numpy sqlparse openpyxl


Create directories:
mkdir excels upload


Run the app:
python main.py

Access at http://localhost:5000. 🌐


🚀 #Usage

Web Interface: Visit http://localhost:5000 to upload files and view companies. 🖥️
Upload Data: Use supported formats (.xlsx, .csv, .json, .xml, .sql, .txt). 📤
Get Quantity: Use /get_quantity for totals. 📊
Forecast: Use /forecast for predictions (Daily, Weekly, Monthly). 🔮

API Endpoints

POST /upload_dotnet_data: Upload data files.
GET/POST /get_quantity: Get total quantity.
GET/POST /forecast: Generate forecasts.
GET /get_companies: List companies.

Example API Requests
# Upload Data
curl -X POST -F "file=@data.xlsx" http://localhost:5000/upload_dotnet_data

# Get Total Quantity
curl "http://localhost:5000/get_quantity?company=Acme&from_date=01-01-2023&to_date=31-12-2023"

# Forecast
curl -X POST -H "Content-Type: application/json" -d '{"company":"Acme","from_date":"01-01-2023","to_date":"31-12-2023","frequency":"Monthly"}' http://localhost:5000/forecast

📊 #Data Requirements

Company Name: e.g., "Acme Corp" 🏢
Date: e.g., DD-MM-YYYY 📅
Quantity: Numeric value 📦
Item: Optional, defaults to "Default Item" 🛒

Supports case-insensitive column names (e.g., "Company", "Qty").
🐛 #Debugging

Logs: Check console for debug messages. 📜
Errors: JSON responses for invalid inputs. ⚠️
Paths: Ensure excels and upload are writable. 🗂️

🔮 #Future Improvements

Support more file formats 📄
Enhance forecasting model 🧠
Add interactive charts 📉
Implement authentication 🔒

📜 #License
MIT License. See LICENSE for details. 📝

#🙌 Contributing
Submit pull requests or open issues for bugs/features. 🚀

#📧 Contact
Reach out at suruswork395@gmail.com. 📩
Happy forecasting! 🎉
