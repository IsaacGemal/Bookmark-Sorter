document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('bookmark-file');
    const fileName = document.getElementById('file-name');
    const organizeButton = document.getElementById('organize-bookmarks');
    const downloadSection = document.getElementById('download-section');
    const downloadButton = document.getElementById('download-json');
    const spinner = document.getElementById('spinner');

    let processedBookmarks = null;

    fileInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            fileName.textContent = file.name;
            organizeButton.disabled = false;
        } else {
            fileName.textContent = '';
            organizeButton.disabled = true;
        }
    });
    
    organizeButton.addEventListener('click', () => {
        const file = fileInput.files[0];
        if (file) {
            spinner.style.display = 'block';
            organizeButton.disabled = true;
            downloadSection.style.display = 'none';

            const formData = new FormData();
            formData.append('file', file);

            fetch('/process_and_organize', {
                method: 'POST',
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                processedBookmarks = data;
                spinner.style.display = 'none';
                downloadSection.style.display = 'block';
                console.log('Organized bookmarks:', data);
            })
            .catch((error) => {
                console.error('Error:', error);
                spinner.style.display = 'none';
                organizeButton.disabled = false;
                alert('An error occurred while processing the bookmarks. Please try again.');
            });
        }
    });

    downloadButton.addEventListener('click', () => {
        if (processedBookmarks) {
            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(processedBookmarks, null, 2));
            const downloadAnchorNode = document.createElement('a');
            downloadAnchorNode.setAttribute("href", dataStr);
            downloadAnchorNode.setAttribute("download", "organized_bookmarks.json");
            document.body.appendChild(downloadAnchorNode);
            downloadAnchorNode.click();
            downloadAnchorNode.remove();
        }
    });
});