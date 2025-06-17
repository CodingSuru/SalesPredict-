function openTab(evt, tabName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].classList.remove("active");
    }
    tablinks = document.getElementsByClassName("tab-btn");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].classList.remove("active");
    }
    document.getElementById(tabName).classList.add("active");
    evt.currentTarget.classList.add("active");
}

function fetchQuantity() {
    var company = document.getElementById('fetchCompany').value;
    var fromDate = document.getElementById('fetchFromDate').value;
    var toDate = document.getElementById('fetchToDate').value;

    if (!company || !fromDate || !toDate) {
        alert('Please fill in all fields.');
        return;
    }

    // Show loading state
    document.getElementById('quantityResults').style.display = 'block';
    document.getElementById('quantityTable').classList.add('hidden');

    fetch('/get_quantity', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            company: company,
            from_date: fromDate,
            to_date: toDate
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data); // Debug log
        if (data.error) {
            alert('Error: ' + data.error);
            return;
        }
        
        if (data.total_quantity !== undefined) {
            // Show results
            document.getElementById('quantityTable').classList.remove('hidden');
            document.getElementById('resultCompany').innerText = company;
            document.getElementById('resultFromDate').innerText = fromDate;
            document.getElementById('resultToDate').innerText = toDate;
            document.getElementById('resultQuantity').innerText = data.total_quantity;
        } else {
            alert('No quantity data received');
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
        alert('An error occurred: ' + error.message);
    });
}

function forecast() {
    var company = document.getElementById('foreCompany').value;
    var fromDate = document.getElementById('foreFromDate').value;
    var toDate = document.getElementById('foreToDate').value;
    var frequency = document.getElementById('frequency').value;

    if (!company || !fromDate || !toDate || !frequency) {
        alert('Please fill in all fields.');
        return;
    }

    // Show loading and hide previous results
    document.getElementById('loadingIndicator').classList.remove('hidden');
    document.getElementById('forecastTable').classList.add('hidden');

    fetch('/forecast', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            company: company,
            from_date: fromDate,
            to_date: toDate,
            frequency: frequency
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        document.getElementById('loadingIndicator').classList.add('hidden');
        console.log('Forecast response data:', data); // Debug log
        
        if (data.error) {
            alert('Error: ' + data.error);
            return;
        }
        
        if (data.predictions && data.predictions.length > 0) {
            // Show results table
            document.getElementById('forecastTable').classList.remove('hidden');
            var tbody = document.getElementById('forecastResultsBody');
            tbody.innerHTML = ''; // Clear any existing rows
            
            data.predictions.forEach(prediction => {
                var row = document.createElement('tr');
                row.innerHTML = `
                    <td>${prediction.Item}</td>
                    <td>${prediction['Company Name']}</td>
                    <td>${prediction['Forecasted Quantity']}</td>
                    <td>${prediction.Date}</td>
                `;
                tbody.appendChild(row);
            });
        } else {
            alert('No forecast data received');
        }
    })
    .catch(error => {
        document.getElementById('loadingIndicator').classList.add('hidden');
        console.error('Forecast error:', error);
        alert('An error occurred: ' + error.message);
    });
}