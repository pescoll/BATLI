let cleaned_dataset_file;

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
                console.log(data);
                alert(data.message);

                // Update HTML elements and filename
                filename = data.filename;
                document.getElementById('plateName').textContent = `Plate Name: ${(data.database_info && data.database_info['Plate Name']) || ''}`;
                document.getElementById('measurement').textContent = `Measurement: ${(data.database_info && data.database_info['Measurement']) || ''}`;
                document.getElementById('evaluation').textContent = `Evaluation: ${(data.database_info && data.database_info['Evaluation']) || ''}`;
                document.getElementById('population').textContent = `Population: ${(data.database_info && data.database_info['Population']) || ''}`;
                document.getElementById('numberOfWells').textContent = `Number of Wells: ${data.number_of_wells || ''}`;
                document.getElementById('numberOfTimepoints').textContent = `Number of Timepoints: ${data.number_of_timepoints || ''}`;
                document.getElementById('numberOfCells').textContent = `Number of Unique Tracked Cells: ${data.number_of_cells || ''}`;
                document.getElementById('elapsedTime').textContent = `Dataset cleaned and pre-processed in ${data.elapsed_time || ''}`;

                // Get column names and populate form
                cleaned_dataset_file = data.cleaned_dataset_file; // Set the cleaned_dataset_file global variable
                getColumnNamesAndPopulateForm(); // Call the function to populate the form
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

async function getColumnNamesAndPopulateForm() {
    try {
        const response = await fetch('/get_column_names', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({filename: cleaned_dataset_file})
        });
        const data = await response.json();  // rename columnNames to data
        console.log(data);  // check what is returned from server
        console.log(`Filename: ${cleaned_dataset_file}`);

        if (!Array.isArray(data)) {  // check if data is an array
            console.error('Data returned from server is not an array');
            return;
        }

        const columnNames = data;  // if data is an array, assign it to columnNames

        const renameForm = document.getElementById('renameForm');

        for (let columnName of columnNames) {
            const oldNameLabel = document.createElement('label');
            oldNameLabel.textContent = 'Old Column Name:';
            const oldNameInput = document.createElement('input');
            oldNameInput.type = 'text';
            oldNameInput.value = columnName;
            oldNameInput.readOnly = true;

            const newNameLabel = document.createElement('label');
            newNameLabel.textContent = 'New Column Name:';
            const newNameInput = document.createElement('input');
            newNameInput.type = 'text';

            renameForm.appendChild(oldNameLabel);
            renameForm.appendChild(oldNameInput);
            renameForm.appendChild(newNameLabel);
            renameForm.appendChild(newNameInput);
        }

    } catch (error) {
        console.error('Error:', error);
    }
}

async function renameColumns(event) {
    event.preventDefault();

    let renameForm = document.getElementById('renameForm');
    console.log(renameForm);  // Print the form
    console.log(renameForm.elements);  // Print the form elements

    let columnMappings = {};  // Create an object to store column name mappings

    let isValid = true;
    let validationMessage = '';

    // Iterate over the form elements in pairs (old name, new name)
    for (let i = 0; i < renameForm.elements.length - 1; i += 2) {
        let oldName = renameForm.elements[i].value;
        let newName = renameForm.elements[i + 1].value;

        if (!newName) {
            newName = oldName; // If no new name provided, use the old name
        }

        // Check the length of the new name
        if (newName.length > 20) {
            isValid = false;
            validationMessage += `New name for column "${oldName}" is too long. It should be no more than 20 characters.\n`;
            continue;
        }

        // Check if the new name contains only alphanumeric characters and underscores
        if (!/^[a-zA-Z0-9_]+$/.test(newName)) {
            isValid = false;
            validationMessage += `New name for column "${oldName}" is invalid. It should only contain alphanumeric characters and underscores.\n`;
            continue;
        }

        // Check if the new name contains more than one word
        if (newName.split('_').length > 1) {
            isValid = false;
            validationMessage += `New name for column "${oldName}" should be one word. Underscores are the only valid symbols.\n`;
        }

        // Add the column name mapping to the object
        columnMappings[oldName] = newName;
    }

    if (!isValid) {
        alert(validationMessage);
        return;
    }

    // Convert the column name mappings to a JSON string
    let jsonMappings = JSON.stringify({
        filename: cleaned_dataset_file,
        mappings: columnMappings
    });

    console.log(jsonMappings);  // Print the JSON string

    try {
        const response = await fetch('/rename_columns', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: jsonMappings  // Send the JSON string to the server
        });

        if (response.ok) {
            const data = await response.json();
            console.log(data);
            alert(data.message);
            // TODO: Update the UI based on the response
        } else {
            console.error('Error:', response.statusText);
        }

    } catch (error) {
        console.error('Error:', error);
    }
}
