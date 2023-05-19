var currentDatasetFilename = localStorage.getItem('currentDatasetFilename');
var conditionsDropdown = document.getElementById('conditionsDropdown');
var parametersDropdown = document.getElementById('parametersDropdown');

axios.get('/get_parameter_names')
    .then((response) => {
        response.data.condition_cols.forEach((col) => {
            var option = document.createElement('option');
            option.text = col;
            conditionsDropdown.add(option);
        });
        response.data.column_names.forEach((col) => {
            var option = document.createElement('option');
            option.text = col;
            parametersDropdown.add(option);
        });
    })
    .catch((error) => {
        console.log(error);
    });


function showPlot2() {
    // Display loading message
    document.getElementById('loadingMessage').style.display = 'block';

    var conditionsDropdown = document.getElementById('conditionsDropdown');
    var parametersDropdown = document.getElementById('parametersDropdown');
    
    var percentageInput = document.getElementById('percentageInput').value;

    var selectedCondition = conditionsDropdown.options[conditionsDropdown.selectedIndex].value;
    var selectedParameter = parametersDropdown.options[parametersDropdown.selectedIndex].value;

    axios.post('/plot2', { condition: selectedCondition, parameter: selectedParameter, percentage: percentageInput })
    .then((response) => {
        const plotArea2 = document.getElementById('plotArea2');
        // Clear out the old images
        plotArea2.innerHTML = '';
        response.data.plot_urls.forEach(plotUrl => {
            const img = document.createElement('img');
            img.src = plotUrl;
            plotArea2.appendChild(img);
        });
        plotArea2.style.display = 'block';
        document.getElementById('loadingMessage').style.display = 'none';
    })
    .catch((error) => {
        console.log(error);
    });
}
