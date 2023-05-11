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
    document.getElementById('plotArea').style.display = 'none';
   
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

async function getFirstRows(filename) {
    const response = await fetch(`/get_first_rows?filename=${encodeURIComponent(filename)}`);
    const data = await response.json();

    const table = document.getElementById('firstRowsTable');
    const tbody = document.createElement('tbody');

    data.first_rows.forEach((row) => {
        const tr = document.createElement('tr');

        for (const key in row) {
            const td = document.createElement('td');
            td.textContent = row[key];
            tr.appendChild(td);
        }

        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
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
    document.getElementById('plotArea').style.display = 'none';

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
                document.getElementById('measurement').textContent = `Measurement: ${data.database_info['Measurement']}`;
                document.getElementById('evaluation').textContent = `Evaluation: ${data.database_info['Evaluation']}`;
                document.getElementById('population').textContent = `Population: ${data.database_info['Population']}`;
                document.getElementById('numberOfWells').textContent = `Number of Wells: ${data.number_of_wells}`;
                document.getElementById('numberOfTimepoints').textContent = `Number of Timepoints: ${data.number_of_timepoints}`;
                document.getElementById('numberOfCells').textContent = `Number of Unique Tracked Cells: ${data.number_of_cells}`;
                document.getElementById('elapsedTime').textContent = `Dataset loaded, cleaned and pre-processed in ${data.elapsed_time}`;
                document.getElementById('plotImage').src = data.plot_url; // Assuming the URL of the plot is returned in 'plot_url' attribute.
                document.getElementById('plotArea').style.display = 'block'; // Show the plot area.

                // Fetch and display the first 5 rows of the DataFrame
                await getFirstRows(file.name);
            
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





// async function loadCleanedDataset() {
//     const fileInput = document.getElementById('cleanedFileInput');
//     if (fileInput.files.length === 0) {
//         alert('Please select a file');
//         return;
//     }

//     const file = fileInput.files[0];
//     const formData = new FormData();
//     formData.append('file', file);

//     // Reset the content of the HTML elements
//     document.getElementById('plateName').textContent = '';
//     document.getElementById('measurement').textContent = '';
//     document.getElementById('evaluation').textContent = '';
//     document.getElementById('population').textContent = '';
//     document.getElementById('numberOfWells').textContent = '';
//     document.getElementById('numberOfTimepoints').textContent = '';
//     document.getElementById('numberOfCells').textContent = '';
//     document.getElementById('elapsedTime').textContent = '';
//     document.getElementById('loadingMessage').style.display = 'block';
//     document.getElementById('plotImage').src = '';
//     document.getElementById('plotArea').style.display = 'block';
    
//     // Display loading message
//     document.getElementById('loadingMessage').style.display = 'block';

//     // Delay fetch request by 100ms
//     setTimeout(async () => {
//         try {
//             const response = await fetch('/load_cleaned_dataset', {
//                 method: 'POST',
//                 body: formData
//             });

//             // Hide loading message
//             document.getElementById('loadingMessage').style.display = 'none';

//             if (response.ok) {
//                 const data = await response.json();
//                 alert(data.message);
//                 document.getElementById('plateName').textContent = `Plate Name: ${data.database_info['Plate Name']}`;
//                 document.getElementById('measurement').textContent = `Measurement: ${data.database_info['Measurement']}`;
//                 document.getElementById('evaluation').textContent = `Evaluation: ${data.database_info['Evaluation']}`;
//                 document.getElementById('population').textContent = `Population: ${data.database_info['Population']}`;
//                 document.getElementById('numberOfWells').textContent = `Number of Wells: ${data.number_of_wells}`;
//                 document.getElementById('numberOfTimepoints').textContent = `Number of Timepoints: ${data.number_of_timepoints}`;
//                 document.getElementById('numberOfCells').textContent = `Number of Unique Tracked Cells: ${data.number_of_cells}`;
//                 document.getElementById('elapsedTime').textContent = `Dataset loaded, cleaned and pre-processed in ${data.elapsed_time}`;
//                 document.getElementById('plotImage').src = data.plot_url; // Assuming the URL of the plot is returned in 'plot_url' attribute.
//                 document.getElementById('plotArea').style.display = 'block'; // Show the plot area.
//                 document.getElementById('firstRowsTable').style.display = 'block'; // Show the table.
            
//             } else {
//                 alert('Error loading dataset');
//             }

//         } catch (error) {
//             // Hide loading message in case of error
//             document.getElementById('loadingMessage').style.display = 'none';
//             console.error('Error:', error);
//         }
//     }, 100);
// }

// function getFirstRows(filename) {
//     $.get('/get_first_rows', {filename: filename}, function(response) {
//         var first_rows = response['first_rows'];
//         var table = $('#firstRowsTable'); // Assuming you have a table with id 'my-table'
//         for (var i = 0; i < first_rows.length; i++) {
//             var row = first_rows[i];
//             var tr = $('<tr>');
//             for (var key in row) {
//                 $('<td>').text(row[key]).appendTo(tr);
//             }
//             tr.appendTo(table);
//         }
//     });
// }

// $('#my-form').on('submit', function(e) {
//     e.preventDefault();
//     var formData = new FormData(this);
//     $.ajax({
//         type: 'POST',
//         url: '/load_cleaned_dataset',
//         data: formData,
//         contentType: false,
//         processData: false,
//         success: function(response) {
//             var filename = response['database_info']['Plate Name'] + '_' + response['database_info']['Measurement'] + '_' + response['database_info']['Evaluation'] + '_' + response['database_info']['Population'];
//             filename = filename.replace(' ', '_') + '.csv';
//             getFirstRows(filename);
//             $('#plot').attr('src', response['plot_url']); // Assuming you have an image tag with id 'plot'
//         }
//     });
// });

// function loadCleanedDataset() {
//     var fileInput = document.querySelector('#cleaned-dataset-input');
//     var formData = new FormData();
//     formData.append('file', fileInput.files[0]);

//     fetch('/load_cleaned_dataset', {
//         method: 'POST',
//         body: formData
//     })
//     .then(response => response.json())
//     .then(data => {
//         // Display the response from the server
//         console.log(data);

//         // Fetch the first 5 rows of the dataset
//         fetchFirstRows(fileInput.files[0].name);
//     })
//     .catch(error => console.error(error));
// }

// function fetchFirstRows(filename) {
//     fetch('/get_first_rows?filename=' + encodeURIComponent(filename))
//     .then(response => response.json())
//     .then(data => {
//         // Display the first 5 rows
//         var tableBody = document.querySelector('#first-rows-table tbody');
//         tableBody.innerHTML = '';

//         data.first_rows.forEach(row => {
//             var tr = document.createElement('tr');

//             for (var key in row) {
//                 var td = document.createElement('td');
//                 td.textContent = row[key];
//                 tr.appendChild(td);
//             }

//             tableBody.appendChild(tr);
//         });
//     })
//     .catch(error => console.error(error));
// }

// document.querySelector('#load-cleaned-dataset-button').addEventListener('click', loadCleanedDataset);



// function showFirstRows(filename) {
//     // Generate the URL
//     const url = '/get_first_rows?filename=' + encodeURIComponent(filename);

//     // Log the URL
//     console.log(url);

//     // Use fetch to get the data from your server
//     fetch('/get_first_rows?filename=' + filename)
//         .then(response => response.json())
//         .then(data => {
//             // Get the table div
//             let tableDiv = document.getElementById('firstRowsTable');

//             // Create a table
//             let table = document.createElement('table');

//             // Add data to the table
//             for (let row of data.first_rows) {
//                 let tr = document.createElement('tr');
//                 for (let key in row) {
//                     let td = document.createElement('td');
//                     td.textContent = row[key];
//                     tr.appendChild(td);
//                 }
//                 table.appendChild(tr);
//             }

//             // Add the table to the div
//             tableDiv.innerHTML = '';
//             tableDiv.appendChild(table);
//         })
//         .catch(error => console.error('Error:', error));
// }
