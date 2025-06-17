📊 Prediction Model Project 🚀
Welcome to the Prediction Model Project! This project is a Flask-based web application designed to process sales data, generate forecasts, and provide total quantity calculations for companies based on uploaded data. It supports multiple file formats and provides a user-friendly interface for data analysis and predictions. 🎉
📋 Project Overview
This application allows users to:

Upload sales data in various formats (Excel, CSV, JSON, XML, SQL, TXT) 📂
Calculate total quantities for specific companies within a date range 📈
Generate forecasts (daily, weekly, or monthly) using a Random Forest model 🧠
View and interact with data through a web interface 🌐

The project is built using Python, Flask, and Pandas, with machine learning powered by Scikit-learn. It includes robust error handling, data validation, and preprocessing to ensure reliable results. 💻
🛠️ Features

File Upload: Supports multiple file formats with validation for required fields (company name, date, quantity) 📥
Data Processing: Cleans and preprocesses data for analysis and forecasting 🧹
Total Quantity Calculation: Computes total quantities for a specified company and date range 📊
Forecasting: Generates predictions using a Random Forest model with customizable frequency (Daily, Weekly, Monthly) 🔮
Web Interface: Interactive UI for uploading data and viewing results 🌍
Error Handling: Comprehensive logging and error messages for debugging 🔍

📁 Project Structure
📦 Prediction_model
├── 📂 excels                # Directory for output Excel files
├── 📂 upload                # Directory for uploaded data
├── 📂 static                # Static files (CSS, JS, etc.)
├── 📂 templates             # HTML templates for the web interface
├── 📜 main.py              # Main Flask application
├── 📜 data_processing.py    # Data processing and forecasting logic
└── 📜 README.md            # Project documentation

🛠️ Setup Instructions
Prerequisites

Python 3.8+ 🐍
pip (Python package manager) 📦

Installation

Clone the Repository:
git clone <repository-url>
cd Prediction_model


Install Dependencies:
pip install -r requirements.txt

Required packages include:

flask 🌐
pandas 📊
scikit-learn 🧠
numpy 🔢
sqlparse 🗄️
openpyxl 📑
xml.etree.ElementTree 📄


Set Up Directories:Ensure the excels and upload directories exist in the project root:
mkdir excels upload


Run the Application:
python main.py

The app will run in debug mode at http://localhost:5000 by default. 🌐


🚀 Usage

Access the Web Interface:

Navigate to http://localhost:5000 in your browser.
Use the interface to upload data files and view available companies. 🖥️


Upload Data:

Upload files in supported formats (.xlsx, .csv, .json, .xml, .sql, .txt).
The system validates required fields and processes the data. 📤


Get Total Quantity:

Use the /get_quantity endpoint (via web form or API) to calculate total quantities for a company within a date range. 📊


Forecast Data:

Use the /forecast endpoint to generate predictions for a company, specifying the date range and frequency (Daily, Weekly, Monthly). 🔮


API Endpoints:

/upload_dotnet_data (POST): Upload and process data files.
/get_quantity (GET/POST): Retrieve total quantity for a company and date range.
/forecast (GET/POST): Generate forecasts for a company.
/get_companies (GET): List all unique companies in the dataset.



📝 Example API Requests
Upload Data
curl -X POST -F "file=@data.xlsx" http://localhost:5000/upload_dotnet_data

Get Total Quantity
curl "http://localhost:5000/get_quantity?company=Acme&from_date=01-01-2023&to_date=31-12-2023"

Forecast
curl -X POST -H "Content-Type: application/json" -d '{"company":"Acme","from_date":"01-01-2023","to_date":"31-12-2023","frequency":"Monthly"}' http://localhost:5000/forecast

📊 Data Requirements
Uploaded data must include:

Company Name: Name of the company (e.g., "Acme Corp") 🏢
Date: Sale date in a recognizable format (e.g., DD-MM-YYYY) 📅
Quantity: Numeric quantity sold 📦
Item: Optional item name (defaults to "DefaultItem" if missing) 🛒

The system supports case-insensitive column names and handles variations like "Company", "CompanyName", "Qty", etc.
🐛 Debugging

Logs: Check console output for detailed debug messages. 📜
Errors: The application returns JSON error responses with descriptive messages for invalid inputs or processing issues. ⚠️
File Paths: Ensure the excels and upload directories are writable. 🗂️

🔮 Future Improvements

Add support for additional file formats 📄
Enhance forecasting model with more features or algorithms 🧠
Improve UI with interactive charts and visualizations 📉
Add authentication for secure data uploads 🔒

📜 License
This project is licensed under the MIT License. See the LICENSE file for details. 📝
🙌 Contributing
Contributions are welcome! Please submit a pull request or open an issue for bug reports or feature requests. 🚀
📧 Contact
For questions or support, reach out to the project maintainers at suruswork395@gmail.com. 📩
Happy forecasting! 🎉
