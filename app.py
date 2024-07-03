import logging
from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
from anthropic import Anthropic
from io import BytesIO
import os

from bookmarks import parse_bookmarks, organize_bookmarks_in_chunks, json_to_html_bookmarks
from visualization import visualize_bookmarks

app = Flask(__name__)
socketio = SocketIO(app)

# Set up logging
logging.basicConfig(filename='bookmark_organizer.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

anthropic_key = os.getenv('ANTHROPIC_API_KEY')
client = Anthropic(api_key=anthropic_key)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('after_connect', {'data': 'Connected to bookmark processing'})

@app.route('/process_and_organize', methods=['POST'])
def process_and_organize():
    if 'file' not in request.files:
        logging.error('No file part in the request')
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        logging.error('No selected file')
        return jsonify({'error': 'No selected file'}), 400
    if file:
        logging.info(f'Processing file: {file.filename}')
        bookmarks = parse_bookmarks(file)
        logging.info(f'Parsed {len(bookmarks)} bookmarks')
        organized_bookmarks = organize_bookmarks_in_chunks(bookmarks, socketio)
        logging.info(f'Organized {len(organized_bookmarks)} bookmarks')
        
        # Generate embeddings and create plot data
        plot_data = visualize_bookmarks(organized_bookmarks)
        
        return jsonify({'bookmarks': organized_bookmarks, 'plot_data': plot_data})

@app.route('/convert_to_html', methods=['POST'])
def convert_to_html():
    json_data = request.json
    html_content = json_to_html_bookmarks(json_data)
    
    # Create a BytesIO object to hold the HTML content
    html_buffer = BytesIO(html_content.encode())
    
    # Send the file
    return send_file(html_buffer,
                     mimetype='text/html',
                     as_attachment=True,
                     download_name='organized_bookmarks.html')

if __name__ == '__main__':
    app.run(debug=True)