var currentDatasetFilename = localStorage.getItem('currentDatasetFilename');


async function loadCleanedDataset() {
    const fileInput = document.getElementById('cleanedFileInput');
    if (fileInput.files.length === 0) {
        alert('Please select a file');
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    // Reset the content of the HTML elements
    document.getElementById('plateName').textContent = '';
    document.getElementById('measurement').textContent = '';
    document.getElementById('evaluation').textContent = '';
    document.getElementById('population').textContent = '';
    document.getElementById('numberOfWells').textContent = '';
    document.getElementById('numberOfTimepoints').textContent = '';
    document.getElementById('numberOfCells').textContent = '';
    document.getElementById('loadingMessage').style.display = 'block';
    document.getElementById('plotImage').src = '';
    document.getElementById('plotArea').style.display = 'none';
    document.getElementById('first-rows-table').style.display = 'none';
    // Display loading message
    document.getElementById('loadingMessage').style.display = 'block';

    // Delay fetch request by 100ms
    setTimeout(async () => {
        try {
            const response = await fetch('/load_cleaned_dataset', {
                method: 'POST',
                body: formData
            });

            // Hide loading message
            document.getElementById('loadingMessage').style.display = 'none';

            if (response.ok) {
                const data = await response.json();
                alert(data.message);

                // Update HTML elements and filename
                let filename = file.name;
                
                // Save the filename to localStorage
                localStorage.setItem('currentDatasetFilename', filename);
                
                // Update the HTML element to display the filename
                let filenameElement = document.getElementById('currentDataset');
                filenameElement.textContent = `${filename}`;


                document.getElementById('plateName').textContent = `Plate Name: ${data.database_info['Plate Name']}`;
                document.getElementById('measurement').textContent = `Measurement: ${data.database_info['Measurement']}`;
                document.getElementById('evaluation').textContent = `Evaluation: ${data.database_info['Evaluation']}`;
                document.getElementById('population').textContent = `Population: ${data.database_info['Population']}`;
                document.getElementById('numberOfWells').textContent = `Number of Wells: ${data.number_of_wells}`;
                document.getElementById('numberOfTimepoints').textContent = `Number of Timepoints: ${data.number_of_timepoints}`;
                document.getElementById('numberOfCells').textContent = `Number of Unique Tracked Cells: ${data.number_of_cells}`;
                document.getElementById('plotImage').src = data.plot1_url; 
                document.getElementById('plotArea').style.display = 'block'; // Show the plot area.
                document.getElementById('first-rows-table').style.display = 'table';

                // Fetch and display the first 5 rows of the DataFrame
                //await getFirstRows(file.name);
                const firstRows = await getFirstRows(file.name);
                const tableBody = document.getElementById('first-rows-table').getElementsByTagName('tbody')[0];
                tableBody.innerHTML = '';  // Clear the table body
                createTable(firstRows);

                // Log the filename in the console
                console.log(`Current dataset filename: ${filename}`);             

            } else {
                alert('Error loading dataset');
            }

        } catch (error) {
            // Hide loading message in case of error
            document.getElementById('loadingMessage').style.display = 'none';
            console.error('Error:', error);
        }
    }, 100);
}

async function getFirstRows() {
    let filename = localStorage.getItem('currentDatasetFilename');
    const response = await fetch(`/get_first_rows?filename=${encodeURIComponent(filename)}`);
    const responseText = await response.text();
    console.log(responseText);
    const data = JSON.parse(responseText);
    return {
        headers: data.headers,
        rows: data.first_rows
    };
}

function createTable(data) {
    var table = document.getElementById('first-rows-table');
    table.innerHTML = '';  // Clear the table

    var csvHeaders = data.headers;

    // Add headers
    var thead = document.createElement('thead');
    var headerRow = document.createElement('tr');
    for (var i = 0; i < csvHeaders.length; i++) {
        var th = document.createElement('th');
        th.textContent = csvHeaders[i];
        headerRow.appendChild(th);
    }
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Add data
    var tbody = document.createElement('tbody');
    for (var i = 0; i < data.rows.length; i++) {
        var row = document.createElement('tr');
        for (var j = 0; j < csvHeaders.length; j++) {
            var key = csvHeaders[j];
            var td = document.createElement('td');
            td.textContent = data.rows[i][key];
            row.appendChild(td);
        }
        tbody.appendChild(row);
    }
    table.appendChild(tbody);
}

