let filename;

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
            
                // Populate the rename fields
                const renameFields = document.getElementById('renameFields');
                for (const columnName of Object.keys(data.database_info || {})) {
                    const input = document.createElement('input');
                    input.name = columnName;
                    input.placeholder = columnName;
                    input.pattern = "\\w{1,20}";
                    input.title = "Names should be less than 20 characters long, can have only underscores as symbols in the name, and should be only one word";
                    renameFields.appendChild(input);
                }

                getColumnNamesAndPopulateForm();
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
            body: JSON.stringify({filename: filename})
        });
        const columnNames = await response.json();
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