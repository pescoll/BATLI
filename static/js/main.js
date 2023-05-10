async function loadDataset() {
    const fileInput = document.getElementById('fileInput');
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
    document.getElementById('elapsedTime').textContent = '';
    document.getElementById('loadingMessage').style.display = 'block';
    document.getElementById('plotImage').src = '';


    // Display loading message
    document.getElementById('loadingMessage').style.display = 'block';

    // Delay fetch request by 100ms
    setTimeout(async () => {
        try {
            const response = await fetch('/load_dataset', {
                method: 'POST',
                body: formData
            });

            // Hide loading message
            document.getElementById('loadingMessage').style.display = 'none';

            if (response.ok) {
                const data = await response.json();
                alert(data.message);
                document.getElementById('plateName').textContent = `Plate Name: ${data.database_info['Plate Name']}`;
                document.getElementById('measurement').textContent = `Measurement: ${data.database_info['Measurement']}`;
                document.getElementById('evaluation').textContent = `Evaluation: ${data.database_info['Evaluation']}`;
                document.getElementById('population').textContent = `Population: ${data.database_info['Population']}`;
                document.getElementById('numberOfWells').textContent = `Number of Wells: ${data.number_of_wells}`;
                document.getElementById('numberOfTimepoints').textContent = `Number of Timepoints: ${data.number_of_timepoints}`;
                document.getElementById('numberOfCells').textContent = `Number of Unique Tracked Cells: ${data.number_of_cells}`;
                document.getElementById('elapsedTime').textContent = `Dataset loaded, cleaned and pre-processed in ${data.elapsed_time}`;
                document.getElementById('plotImage').src = data.plot_url; // Assuming the URL of the plot is returned in 'plot_url' attribute.
                document.getElementById('plotArea').style.display = 'block'; // Show the plot area.
            }
             else {
                alert('Error loading dataset');
            }

        } catch (error) {
            // Hide loading message in case of error
            document.getElementById('loadingMessage').style.display = 'none';
            console.error('Error:', error);
        }
    }, 100);
}

async function loadCleanedDataset() {
    const fileInput = document.getElementById('cleanedFileInput');
    if (fileInput.files.length === 0) {
        alert('Please select a file');
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

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
                document.getElementById('plateName').textContent = `Plate Name: ${data.database_info['Plate Name']}`;
                // ... rest of the code is the same as the previous function
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
