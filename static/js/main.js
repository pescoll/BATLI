async function loadDataset() {
    const fileInput = document.getElementById('fileInput');
    if (fileInput.files.length === 0) {
        alert('Please select a file');
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/load_dataset', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            alert('Dataset successfully loaded and cleaned');
        } else {
            alert('Error loading dataset');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}
