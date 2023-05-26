var currentDatasetFilename = localStorage.getItem('currentDatasetFilename');

// These variables are used in both the onchange event and showPlot3
var firstConditionDropdown = document.getElementById('conditionsDropdown');
var secondConditionDropdown = document.getElementById('secondConditionDropdown');
var parametersDropdown = document.getElementById('parametersDropdown');
var normalizationDropdown = document.getElementById('normalizationDropdown');

axios.get('/get_parameter_names_backward_1')
    .then((response) => {
        response.data.condition_cols.forEach((col) => {
            var option = document.createElement('option');
            option.text = col;
            firstConditionDropdown.add(option);
        });
        response.data.column_names.forEach((col) => {
            var option = document.createElement('option');
            option.text = col;
            parametersDropdown.add(option);
        });

        // Attach onchange event after firstConditionDropdown is populated
        firstConditionDropdown.onchange = function() {
            // Clear the secondConditionDropdown options
            secondConditionDropdown.innerHTML = '';
            
            // Add the 'none' option
            var noneOption = document.createElement('option');
            noneOption.value = 'none';
            noneOption.text = 'None';
            secondConditionDropdown.add(noneOption);
        
            // Populate secondConditionDropdown based on the selected option in the firstConditionDropdown
            for (var i = 0; i < firstConditionDropdown.length; i++) {
                if (firstConditionDropdown[i].value !== this.value) {
                    var option = document.createElement('option');
                    option.value = firstConditionDropdown[i].value;
                    option.text = firstConditionDropdown[i].text;
                    secondConditionDropdown.add(option);
                }
            }
        };

        // Automatically select the first option in the firstConditionDropdown
        firstConditionDropdown.selectedIndex = 0;
        // Trigger the onchange event manually
        firstConditionDropdown.dispatchEvent(new Event('change'));
    })
    .catch((error) => {
        console.log(error);
    });



function showPlot3() {
    // Display loading message
    document.getElementById('loadingMessage').style.display = 'block';
   
    // These values are read fresh each time showPlot3 is called
    var percentageInput = document.getElementById('percentageInput').value;
    var yMinInput = document.getElementById('yMin').value || null; 
    var yMaxInput = document.getElementById('yMax').value || null; 
    var rangeStartInput = document.getElementById('rangeStart');
    var rangeEndInput = document.getElementById('rangeEnd');
    var rangeStart = rangeStartInput.value;
    var rangeEnd = rangeEndInput.value;
    var thresholdInput = parseFloat(document.getElementById('thresholdInput').value);

    var selectedCondition = firstConditionDropdown.options[firstConditionDropdown.selectedIndex].value;
    var selectedSecondCondition = secondConditionDropdown.options[secondConditionDropdown.selectedIndex].value;
    var selectedParameter = parametersDropdown.options[parametersDropdown.selectedIndex].value;
    var selectedNormalization = normalizationDropdown.options[normalizationDropdown.selectedIndex].value;

    
    axios.post('/plot3', { condition: selectedCondition, secondCondition: selectedSecondCondition, parameter: selectedParameter, percentage: percentageInput, yMin: yMinInput, yMax: yMaxInput, normalization: selectedNormalization, range_start: rangeStart, range_end: rangeEnd, threshold: thresholdInput })
    .then((response) => {
        const plotArea3 = document.getElementById('plotArea3');
        // // Clear out the old images
        plotArea3.innerHTML = '';
        response.data.plot_urls_backward.forEach(plotUrl3 => {
            const img = document.createElement('img');
            img.src = plotUrl3;
            plotArea3.appendChild(img);
        });
        plotArea3.style.display = 'block';
        document.getElementById('loadingMessage').style.display = 'none';
    })
    .catch((error) => {
        console.log(error);
    });
}
    
// This function shows or hides the custom range inputs depending on the selected normalization method.
document.getElementById('normalizationDropdown').addEventListener('change', function() {
    var customRange = document.getElementById('customRange');
    if (this.value === 'custom') {
        customRange.style.display = 'block';
    } else {
        customRange.style.display = 'none';
    }
});
    
