document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('bookmark-file');
    const fileName = document.getElementById('file-name');
    const organizeButton = document.getElementById('organize-bookmarks');
    const downloadSection = document.getElementById('download-section');
    const downloadButton = document.getElementById('download-json');
    const spinner = document.getElementById('spinner');
    const bookmarkCounter = document.getElementById('bookmark-counter');
    const processedBookmarksContainer = document.getElementById('processed-bookmarks-container');
    const processedBookmarksList = document.getElementById('processed-bookmarks-list');
    const visualizationContainer = document.getElementById('visualization-container');
    const plotlyChart = document.getElementById('plotly-chart');

    let processedBookmarks = null;
    
    // Initialize Socket.IO
    const socket = io();

    socket.on('after_connect', (data) => {
        console.log(data.data);
    });

    socket.on('bookmark_update', (data) => {
        bookmarkCounter.style.display = 'block';
        bookmarkCounter.textContent = `Processed ${data.count} bookmarks`;
        if (data.bookmarks) {
            processedBookmarksContainer.style.display = 'block';
            data.bookmarks.forEach(bookmark => {
                const li = document.createElement('li');
                li.innerHTML = `<strong>${bookmark.title}</strong> (${bookmark.category}): ${bookmark.description}`;
                processedBookmarksList.appendChild(li);
            });
        }
    });

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
            // Reset and hide the bookmark counter
            bookmarkCounter.textContent = '';
            bookmarkCounter.style.display = 'none';

            spinner.style.display = 'block';
            spinner.textContent = 'Processing...'; // Add text to the spinner
            organizeButton.disabled = true;
            downloadSection.style.display = 'none';
            processedBookmarksContainer.style.display = 'none';
            processedBookmarksList.innerHTML = '';
            visualizationContainer.style.display = 'none';

            const formData = new FormData();
            formData.append('file', file);

            fetch('/process_and_organize', {
                method: 'POST',
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                processedBookmarks = data.bookmarks;
                spinner.style.display = 'none';
                spinner.textContent = ''; // Clear the spinner text
                downloadSection.style.display = 'block';
                console.log('Organized bookmarks:', data.bookmarks);

                // Display the Plotly chart
                if (data.plot_data) {
                    visualizationContainer.style.display = 'block';
                    Plotly.newPlot('plotly-chart', data.plot_data.data, data.plot_data.layout);
                }
            })
            .catch((error) => {
                console.error('Error:', error);
                spinner.style.display = 'none';
                spinner.textContent = ''; // Clear the spinner text
                bookmarkCounter.style.display = 'none';
                organizeButton.disabled = false;
                alert('An error occurred while processing the bookmarks. Please try again.');
            });
        }
    });

    downloadButton.addEventListener('click', () => {
        console.log('Download button clicked');
        if (processedBookmarks) {
            console.log('Processed bookmarks found, converting to HTML');
            fetch('/convert_to_html', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(processedBookmarks),
            })
            .then(response => response.blob())
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = 'organized_bookmarks.html';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            })
            .catch((error) => {
                console.error('Error during download:', error);
                alert('An error occurred while preparing the download. Please try again.');
            });
        } else {
            console.log('No processed bookmarks found');
            alert('No bookmarks to download. Please organize your bookmarks first.');
        }
    });
});