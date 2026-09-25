var currentDatasetFilename = localStorage.getItem('currentDatasetFilename');

// These variables are used in both the onchange event and showPlot3
var firstConditionDropdown = document.getElementById('conditionsDropdown');
var secondConditionDropdown = document.getElementById('secondConditionDropdown');
var parametersDropdown = document.getElementById('parametersDropdown');
var normalizationDropdown = document.getElementById('normalizationDropdown');
var secondClassParamDropdown = document.getElementById('secondClassParamDropdown');
var thirdConditionDropdown = document.getElementById('thirdConditionDropdown');
var fixedThirdConditionValueDropdown = document.getElementById('fixedThirdConditionValueDropdown');

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
        // Populate the optional 2nd classification parameter dropdown with the same parameters
        response.data.column_names.forEach((col) => {
            var option = document.createElement('option');
            option.text = col;
            secondClassParamDropdown.add(option);
        });

        // Attach onchange event after firstConditionDropdown is populated
        firstConditionDropdown.onchange = function() {
            // Clear the secondConditionDropdown and thirdConditionDropdown options
            secondConditionDropdown.innerHTML = '';
            thirdConditionDropdown.innerHTML = '';

            // Add the 'none' option
            var noneOption = document.createElement('option');
            noneOption.value = 'none';
            noneOption.text = 'None';
            secondConditionDropdown.add(noneOption);
            thirdConditionDropdown.add(noneOption.cloneNode(true));

            // Populate secondConditionDropdown based on the selected option in the firstConditionDropdown
            for (var i = 0; i < firstConditionDropdown.length; i++) {
                if (firstConditionDropdown[i].value !== this.value) {
                    var option = document.createElement('option');
                    option.value = firstConditionDropdown[i].value;
                    option.text = firstConditionDropdown[i].text;
                    secondConditionDropdown.add(option);
                    thirdConditionDropdown.add(option.cloneNode(true));
                }
            }
        };

        // Show/populate the fixed-value dropdown when the Fix checkbox is toggled
        document.getElementById('fixedThirdCondition').onchange = function() {
            if (this.checked) {
                var selectedThirdCondition = thirdConditionDropdown.value;
                if (!selectedThirdCondition || selectedThirdCondition === 'none') {
                    alert('Please select a third condition before fixing it.');
                    this.checked = false;
                    return;
                }
                fixedThirdConditionValueDropdown.style.display = 'inline';
                fixedThirdConditionValueDropdown.innerHTML = '';  // clear the options
                axios.post('/get_third_condition_values', { condition: selectedThirdCondition })
                    .then((response) => {
                        response.data.unique_values.forEach((val) => {
                            var option = document.createElement('option');
                            option.value = val;
                            option.text = val;
                            fixedThirdConditionValueDropdown.add(option);
                        });
                    })
                    .catch((error) => {
                        console.log(error);
                    });
            } else {
                fixedThirdConditionValueDropdown.style.display = 'none';
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

    // Optional class-2 threshold (3-class mode) and optional 2nd classification parameter
    var threshold2Raw = document.getElementById('thresholdInput2').value;
    var threshold2 = threshold2Raw === '' ? null : parseFloat(threshold2Raw);
    var secondClassParameter = secondClassParamDropdown.value === 'none' ? null : secondClassParamDropdown.value;
    var thresholdB1Raw = document.getElementById('thresholdInputB1').value;
    var thresholdB1 = thresholdB1Raw === '' ? null : parseFloat(thresholdB1Raw);
    var thresholdB2Raw = document.getElementById('thresholdInputB2').value;
    var thresholdB2 = thresholdB2Raw === '' ? null : parseFloat(thresholdB2Raw);

    if (secondClassParameter !== null && thresholdB1 === null) {
        alert('Please provide a threshold for the 2nd classification parameter (or set it back to None).');
        document.getElementById('loadingMessage').style.display = 'none';
        return;
    }

    var selectedCondition = firstConditionDropdown.options[firstConditionDropdown.selectedIndex].value;
    var selectedSecondCondition = secondConditionDropdown.options[secondConditionDropdown.selectedIndex].value;
    var selectedThirdCondition = thirdConditionDropdown.value === 'none' ? null : thirdConditionDropdown.value;
    var fixedThirdCondition = document.getElementById('fixedThirdCondition').checked;
    var fixedThirdConditionValue = fixedThirdCondition ? fixedThirdConditionValueDropdown.value : null;
    var selectedParameter = parametersDropdown.options[parametersDropdown.selectedIndex].value;
    var selectedNormalization = normalizationDropdown.options[normalizationDropdown.selectedIndex].value;

    if (fixedThirdCondition && selectedThirdCondition === null) {
        alert('Third condition is fixed but no third condition was selected. Please select one or uncheck Fix.');
        document.getElementById('loadingMessage').style.display = 'none';
        return;
    }

    axios.post('/plot3', { condition: selectedCondition, secondCondition: selectedSecondCondition, thirdCondition: selectedThirdCondition, fixedThirdCondition: fixedThirdCondition, fixedThirdConditionValue: fixedThirdConditionValue, parameter: selectedParameter, percentage: percentageInput, yMin: yMinInput, yMax: yMaxInput, normalization: selectedNormalization, range_start: rangeStart, range_end: rangeEnd, threshold: thresholdInput, threshold2: threshold2, secondClassParameter: secondClassParameter, thresholdB1: thresholdB1, thresholdB2: thresholdB2 })
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
        // Now call loadClasses after updating plotArea3
        loadClasses();
    })
    .catch((error) => {
        console.log(error);
        document.getElementById('loadingMessage').style.display = 'none';
        if (error.response && error.response.status === 400) {
            alert(error.response.data.message);
        }
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

// These variables are used in both the onchange event and showPlot4
var firstConditionDropdown2 = document.getElementById('conditionsDropdown2');
var secondConditionDropdown2 = document.getElementById('secondConditionDropdown2');
var thirdConditionDropdown2 = document.getElementById('thirdConditionDropdown2');
var fixedThirdConditionValueDropdown2 = document.getElementById('fixedThirdConditionValueDropdown2');
var parametersDropdown2 = document.getElementById('parametersDropdown2');
var normalizationDropdown2 = document.getElementById('normalizationDropdown2');

function loadClasses() {
        axios.get('/get_parameter_names_backward_2')
            .then((response) => {
                // Clear the dropdowns before populating them
                firstConditionDropdown2.innerHTML = '';
                secondConditionDropdown2.innerHTML = '';
                thirdConditionDropdown2.innerHTML = '';
                parametersDropdown2.innerHTML = '';

                response.data.condition_cols.forEach((col) => {
                    var option = document.createElement('option');
                    option.text = col;
                    firstConditionDropdown2.add(option);
                });
                response.data.column_names.forEach((col) => {
                    var option = document.createElement('option');
                    option.text = col;
                    parametersDropdown2.add(option);
                });

                // Attach onchange event after firstConditionDropdown is populated
                firstConditionDropdown2.onchange = function() {
                    // Clear the secondConditionDropdown and thirdConditionDropdown options
                    secondConditionDropdown2.innerHTML = '';
                    thirdConditionDropdown2.innerHTML = '';

                    // Add the 'none' option
                    var noneOption = document.createElement('option');
                    noneOption.value = 'none';
                    noneOption.text = 'None';
                    secondConditionDropdown2.add(noneOption);
                    thirdConditionDropdown2.add(noneOption.cloneNode(true));

                    // Populate secondConditionDropdown based on the selected option in the firstConditionDropdown
                    for (var i = 0; i < firstConditionDropdown2.length; i++) {
                        if (firstConditionDropdown2[i].value !== this.value) {
                            var option = document.createElement('option');
                            option.value = firstConditionDropdown2[i].value;
                            option.text = firstConditionDropdown2[i].text;
                            secondConditionDropdown2.add(option);
                            thirdConditionDropdown2.add(option.cloneNode(true));
                        }
                    }
                };

                // Show/populate the fixed-value dropdown when the Fix checkbox is toggled
                document.getElementById('fixedThirdCondition2').onchange = function() {
                    if (this.checked) {
                        var selectedThirdCondition2 = thirdConditionDropdown2.value;
                        if (!selectedThirdCondition2 || selectedThirdCondition2 === 'none') {
                            alert('Please select a third condition before fixing it.');
                            this.checked = false;
                            return;
                        }
                        fixedThirdConditionValueDropdown2.style.display = 'inline';
                        fixedThirdConditionValueDropdown2.innerHTML = '';  // clear the options
                        axios.post('/get_third_condition_values', { condition: selectedThirdCondition2 })
                            .then((response) => {
                                response.data.unique_values.forEach((val) => {
                                    var option = document.createElement('option');
                                    option.value = val;
                                    option.text = val;
                                    fixedThirdConditionValueDropdown2.add(option);
                                });
                            })
                            .catch((error) => {
                                console.log(error);
                            });
                    } else {
                        fixedThirdConditionValueDropdown2.style.display = 'none';
                    }
                };

                // Automatically select the first option in the firstConditionDropdown
                firstConditionDropdown2.selectedIndex = 0;
                // Trigger the onchange event manually
                firstConditionDropdown2.dispatchEvent(new Event('change'));
            })
            .catch((error) => {
                console.log(error);
            });
}

function showPlot4() {
    // Display loading message
    document.getElementById('loadingMessage2').style.display = 'block';
   
    // These values are read fresh each time showPlot4 is called
    var percentageInput2 = document.getElementById('percentageInput2').value;
    var yMinInput2 = document.getElementById('yMin2').value || null; 
    var yMaxInput2 = document.getElementById('yMax2').value || null; 
    var rangeStartInput = document.getElementById('rangeStart2');
    var rangeEndInput = document.getElementById('rangeEnd2');
    var rangeStart2 = rangeStartInput.value;
    var rangeEnd2 = rangeEndInput.value;

    var selectedCondition2 = firstConditionDropdown2.options[firstConditionDropdown2.selectedIndex].value;
    var selectedSecondCondition2 = secondConditionDropdown2.options[secondConditionDropdown2.selectedIndex].value;
    var selectedThirdCondition2 = thirdConditionDropdown2.value === 'none' ? null : thirdConditionDropdown2.value;
    var fixedThirdCondition2 = document.getElementById('fixedThirdCondition2').checked;
    var fixedThirdConditionValue2 = fixedThirdCondition2 ? fixedThirdConditionValueDropdown2.value : null;
    var selectedParameter2 = parametersDropdown2.options[parametersDropdown2.selectedIndex].value;
    var selectedNormalization2 = normalizationDropdown2.options[normalizationDropdown2.selectedIndex].value;
    var selectedPlotStyle = document.querySelector('input[name="plotStyle"]:checked').value;

    if (fixedThirdCondition2 && selectedThirdCondition2 === null) {
        alert('Third condition is fixed but no third condition was selected. Please select one or uncheck Fix.');
        document.getElementById('loadingMessage2').style.display = 'none';
        return;
    }

    axios.post('/plot4', { condition: selectedCondition2, secondCondition: selectedSecondCondition2, thirdCondition: selectedThirdCondition2, fixedThirdCondition: fixedThirdCondition2, fixedThirdConditionValue: fixedThirdConditionValue2, parameter: selectedParameter2, percentage: percentageInput2, yMin: yMinInput2, yMax: yMaxInput2, normalization: selectedNormalization2, range_start: rangeStart2, range_end: rangeEnd2, plotStyle: selectedPlotStyle })
    .then((response) => {
        // Wait for a brief moment before scrolling
        setTimeout(() => {
            const plotArea4 = document.getElementById('plotArea4');
            plotArea4.scrollIntoView({ behavior: 'smooth' });
        }, 100);  // Wait for 100 milliseconds
    
    
        // const plotArea4 = document.getElementById('plotArea4');
        // // After the plot is displayed, scroll to make it visible
        // plotArea4.scrollIntoView({ behavior: 'smooth' });
    
        // // Clear out the old images
        plotArea4.innerHTML = '';
        response.data.plot_urls_backward.forEach(plotUrl4 => {
            const img = document.createElement('img');
            img.src = plotUrl4;
            plotArea4.appendChild(img);
        });
        plotArea4.style.display = 'block';
        document.getElementById('loadingMessage2').style.display = 'none';
    })
    .catch((error) => {
        console.log(error);
    });
}
    
// This function shows or hides the custom range inputs depending on the selected normalization method.
document.getElementById('normalizationDropdown2').addEventListener('change', function() {
    var customRange = document.getElementById('customRange2');
    if (this.value === 'custom') {
        customRange.style.display = 'block';
    } else {
        customRange.style.display = 'none';
    }
});