var currentDatasetFilename = localStorage.getItem('currentDatasetFilename');

function showPlot2() {
    // Hide the button
    document.getElementById('showPlot2Button').style.display = 'none';

    // Make a GET request to the /plot2 endpoint
    axios.get('/plot2')
        .then((response) => {
            // Update the plot image
            document.getElementById('plotImage2').src = response.data.plot_url;

            // Show the plot area
            document.getElementById('plotArea2').style.display = 'block';
        })
        .catch((error) => {
            console.log(error);
        });
}