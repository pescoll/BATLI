let cleaned_dataset_file;

var currentDatasetFilename = localStorage.getItem('currentDatasetFilename');

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
                
                // Save the filename to localStorage
                localStorage.setItem('currentDatasetFilename', filename);

                // Update the HTML element to display the filename
                let filenameElement = document.getElementById('currentDataset');
                filenameElement.textContent = `Current dataset: ${filename}`;

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
    // Get the current dataset filename from localStorage
    let currentDatasetFilename = localStorage.getItem('currentDatasetFilename');
    try {
        const response = await fetch('/get_column_names', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({filename: currentDatasetFilename})
        });
        
        if (response.ok) {
            const data = await response.json();  // rename columnNames to data
            console.log(data);  // check what is returned from server
            console.log(`Filename: ${currentDatasetFilename}`);

            if (!Array.isArray(data)) {  // check if data is an array
                console.error('Data returned from server is not an array');
                return;
            }

            let renameFieldsDiv = document.getElementById('renameFields');

            for (let colName of data) {
                let fieldRow = document.createElement('div');
            
                let oldNameLabel = document.createElement('label');
                oldNameLabel.textContent = colName + ' ---- ';
                oldNameLabel.className = 'oldNameLabel';
                fieldRow.appendChild(oldNameLabel);
            
                let oldNameInput = document.createElement('input');
                oldNameInput.type = 'hidden';
                oldNameInput.name = colName;
                oldNameInput.value = colName;
                fieldRow.appendChild(oldNameInput);
            
                let newNameInput = document.createElement('input');
                newNameInput.name = colName;
                newNameInput.className = 'newNameInput';
                fieldRow.appendChild(newNameInput);
            
                let deleteCheckbox = document.createElement('input');
                deleteCheckbox.type = 'checkbox';
                deleteCheckbox.id = 'delete_' + colName.replace(/[^a-zA-Z0-9]/g, "_");
                deleteCheckbox.className = 'deleteCheckbox';
                deleteCheckbox.title = 'remove this parameter';
                console.log(deleteCheckbox);
                fieldRow.appendChild(deleteCheckbox);

                renameFieldsDiv.appendChild(fieldRow);
            }
            
        } else {
            console.error('Error:', response.statusText);
        }

    } catch (error) {
        console.error('Error:', error);
    }
}

async function renameColumns(event) {
    event.preventDefault();

    // Get the current dataset filename from localStorage
    let currentDatasetFilename = localStorage.getItem('currentDatasetFilename');

    let renameForm = document.getElementById('renameForm');

    let columnMappings = {};  // Create an object to store column name mappings
    let columnDeletes = [];  // Create an array to store column names to delete

    let isValid = true;
    let validationMessage = '';

    // Iterate over the form elements in pairs (old name, new name)
    for (let i = 0; i < renameForm.elements.length - 1; i += 3) {
        let oldName = renameForm.elements[i].value; // old name is in the hidden input
        let newName = renameForm.elements[i + 1].value || oldName; // new name is in the next input, if no value given, leave old name
        let isChecked = renameForm.elements[i + 2].checked; // checkbox is the next element
        // if checkbox is checked, add old name to columnDeletes
        if (isChecked) {
            columnDeletes.push(oldName);
        } else {
            if (!/^[a-zA-Z0-9_]+$/.test(newName)) {
                isValid = false;
                validationMessage += `New name for column "${oldName}" is invalid. It should only contain alphanumeric characters and underscores.\n`;
                continue;
            }
            columnMappings[oldName] = newName;
        }
    }
    
    
    // for (let i = 0; i < renameForm.elements.length - 1; i += 3) {
    //     let oldName = renameForm.elements[i].value; // old name is in the hidden input
    //     let newName = renameForm.elements[i + 1].value || oldName; // new name is in the next input, if no value given, leave old name
    //     let isChecked = renameForm.elements[i + 2].checked; // checkbox is the next element

    //     // if checkbox is not checked, add old and new name pair to columnMappings
    //     if (!isChecked) {
    //         // // check for valid newName
    //         // if (newName.length > 20) {
    //         //     isValid = false;
    //         //     validationMessage += `New name for column "${oldName}" is too long. It should be no more than 20 characters.\n`;
    //         //     continue;
    //         // }

    //         if (!/^[a-zA-Z0-9_]+$/.test(newName)) {
    //             isValid = false;
    //             validationMessage += `New name for column "${oldName}" is invalid. It should only contain alphanumeric characters and underscores.\n`;
    //             continue;
    //         }

    //         columnMappings[oldName] = newName;
    //     }
    // }

    if (!isValid) {
        alert(validationMessage);
        return;
    }

    // Convert the column name mappings to a JSON string
    let jsonMappings = JSON.stringify({
        filename: currentDatasetFilename,
        mappings: columnMappings,
        deletes: columnDeletes
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


