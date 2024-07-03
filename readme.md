# Bookmark Organizer

Bookmark Organizer is a web application that helps you organize and visualize your browser bookmarks using AI-powered categorization and python data visualization.

## Features

- Parse and organize HTML bookmark files
- AI-powered categorization of bookmarks using Anthropic's Claude API
- Interactive visualization of bookmark relationships using t-SNE and Plotly
- Real-time processing updates via WebSocket
- Download organized bookmarks as an HTML file compatible with most browsers

## Tech Stack

- Backend: Flask, Flask-SocketIO
- Frontend: HTML, CSS, JavaScript
- AI: Anthropic Claude API
- Data Processing: NumPy, scikit-learn
- Visualization: Plotly
- Embedding Generation: Sentence Transformers
- Vector Database: FAISS

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/bookmark-organizer.git
   cd bookmark-organizer
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your Anthropic API key:
   - Sign up for an API key at [Anthropic's website](https://www.anthropic.com)
   - Set the environment variable:
     ```
     export ANTHROPIC_API_KEY='your_api_key_here'
     ```

4. Run the Flask application:
   ```
   python app.py
   ```

5. Open your web browser and navigate to `http://localhost:5000`

## Usage

1. Export your bookmarks from your browser as an HTML file.
2. On the Bookmark Organizer web interface, click "Choose File" and select your exported bookmark file.
3. Click "Organize Bookmarks" to start the processing.
4. Wait for the AI to categorize your bookmarks and generate the visualization.
5. Explore the interactive t-SNE visualization to see relationships between your bookmarks.
6. Click "Download Organized Bookmarks" to get your categorized bookmarks as an HTML file.

## Known Issues

1. Large bookmark files may take a considerable amount of time to process due to API rate limits and the complexity of embedding generation.
2. The application currently doesn't support incremental updates. Each time you process bookmarks, it starts from scratch.
3. The AI categorization will occasionally misclassify bookmarks, especially for niche or ambiguous websites.
4. Malformed or invalid URLs in the bookmark file will cause the application to crash.
5. This code was created for a hackathon, just keep that in mind.

## Contributing

Contributions are welcome, because I don't really know what I'm doing.

## Acknowledgements

- [Anthropic](https://www.anthropic.com) for their Claude AI API
- [Sentence Transformers](https://www.sbert.net/) for embedding generation
- [Plotly](https://plotly.com/) for interactive visualizations
- [FAISS](https://github.com/facebookresearch/faiss) for efficient similarity search

## Contact

- GitHub: [@isaacgemal](https://github.com/isaacgemal)
- Twitter: [@Aizkmusic](https://twitter.com/Aizkmusic)
