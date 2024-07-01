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
            organizeButton.disabled = true;
            downloadSection.style.display = 'none';
            processedBookmarksContainer.style.display = 'none';
            processedBookmarksList.innerHTML = '';

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
                bookmarkCounter.style.display = 'none';
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