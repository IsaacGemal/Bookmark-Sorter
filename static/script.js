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
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');

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
            displayBookmarks(data.bookmarks);
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
                processedBookmarksContainer.style.display = 'block';
                displayBookmarks(processedBookmarks);

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
        if (processedBookmarks) {
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
            alert('No bookmarks to download. Please organize your bookmarks first.');
        }
    });

    // Function to display bookmarks
    function displayBookmarks(bookmarks) {
        processedBookmarksList.innerHTML = '';
        bookmarks.forEach(bookmark => {
            const li = document.createElement('li');
            li.innerHTML = `<strong>${bookmark.title}</strong> (${bookmark.category}): ${bookmark.description}`;
            processedBookmarksList.appendChild(li);
        });
    }

    // Function to filter bookmarks
    function filterBookmarks(searchTerm) {
        if (!processedBookmarks) return;

        const filteredBookmarks = processedBookmarks.filter(bookmark => 
            bookmark.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            bookmark.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
            bookmark.description.toLowerCase().includes(searchTerm.toLowerCase())
        );

        displayBookmarks(filteredBookmarks);
    }

    // Search button click event
    searchButton.addEventListener('click', () => {
        const searchTerm = searchInput.value.trim();
        filterBookmarks(searchTerm);
    });

    // Search input 'Enter' key press event
    searchInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            const searchTerm = searchInput.value.trim();
            filterBookmarks(searchTerm);
        }
    });
});