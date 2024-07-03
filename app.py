import os
import json
import logging
import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
from anthropic import Anthropic
from io import BytesIO

# Updated imports
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from sklearn.manifold import TSNE
from urllib.parse import urlparse
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
        organized_bookmarks = organize_bookmarks_in_chunks(bookmarks)
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

def parse_bookmarks(file):
    content = file.read().decode('utf-8')
    bookmark_pattern = re.compile(r'<DT><A HREF="(.*?)" ADD_DATE="(\d+)"[^>]*>(.*?)</A>', re.DOTALL)
    icon_pattern = re.compile(r'ICON="data:image/\w+;base64,(.*?)"')
    
    bookmarks = []
    for match in bookmark_pattern.finditer(content):
        url = match.group(1)
        add_date = match.group(2)
        title = match.group(3)
        
        # Find the icon data for this bookmark
        icon_match = icon_pattern.search(content, match.start(), match.end())
        icon_data = icon_match.group(1) if icon_match else None
        
        bookmark = {
            "url": url,
            "add_date": add_date,
            "title": title,
            "icon_data": icon_data
        }
        bookmarks.append(bookmark)
    return bookmarks

def organize_bookmarks_in_chunks(bookmarks, chunk_size=25):
    organized_bookmarks = []
    total_processed = 0
    for i in range(0, len(bookmarks), chunk_size):
        chunk = bookmarks[i:i + chunk_size]
        logging.info(f'Processing chunk {i // chunk_size + 1} with {len(chunk)} bookmarks')
        organized_chunk = organize_bookmarks(chunk)
        organized_bookmarks.extend(organized_chunk)
        total_processed += len(organized_chunk)
        socketio.emit('bookmark_update', {'count': total_processed, 'bookmarks': organized_chunk})
    return organized_bookmarks

def organize_bookmarks(bookmarks):
    logging.info(f'Sending {len(bookmarks)} bookmarks to Anthropic API for organization')
    
    # Create a version of bookmarks without icon_data for the API request
    bookmarks_for_api = [{k: v for k, v in bookmark.items() if k != 'icon_data'} for bookmark in bookmarks]
    
    message = f"""Here is a list of bookmarks:

{json.dumps(bookmarks_for_api, indent=2)}

Please organize these bookmarks into categories. For each bookmark, assign a category and provide a brief description. Return the result as a JSON string with the following structure:

[
    {{
        "url": "original url",
        "add_date": "original add_date",
        "title": "original title",
        "category": "assigned category",
        "description": "brief description"
    }},
    ...
]
"""
    # Log the JSON content being sent to Anthropic
    logging.info(f'JSON content sent to Anthropic API:\n{json.dumps(bookmarks_for_api, indent=2)}')
    
    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=3000,
            messages=[
                {"role": "user", "content": message}
            ]
        )
        
        ai_response = response.content[0].text
        start_index = ai_response.find('[')
        end_index = ai_response.rfind(']') + 1
        json_response = ai_response[start_index:end_index]
        
        organized_bookmarks = json.loads(json_response)
        
        # Add back the icon_data to the organized bookmarks
        for org_bookmark, orig_bookmark in zip(organized_bookmarks, bookmarks):
            org_bookmark['icon_data'] = orig_bookmark['icon_data']
        
        logging.info(f'Successfully organized {len(organized_bookmarks)} bookmarks')
        return organized_bookmarks
    except Exception as e:
        logging.error(f'Error organizing bookmarks: {str(e)}')
        raise

def json_to_html_bookmarks(json_data):
    # Parse JSON data
    bookmarks = json_data  # The data is already parsed in Flask

    # Create a dictionary to group bookmarks by category
    categories = {}
    for bookmark in bookmarks:
        category = bookmark.get('category', 'Uncategorized')
        if category not in categories:
            categories[category] = []
        categories[category].append(bookmark)

    # Generate HTML content
    html_content = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3 ADD_DATE="{current_timestamp}" LAST_MODIFIED="{current_timestamp}" PERSONAL_TOOLBAR_FOLDER="true">Favorites bar</H3>
    <DL><p>
""".format(current_timestamp=int(datetime.now().timestamp()))

    # Add bookmarks grouped by category
    for category, bookmarks in categories.items():
        html_content += f'        <DT><H3 ADD_DATE="{int(datetime.now().timestamp())}">{category}</H3>\n'
        html_content += '        <DL><p>\n'
        for bookmark in bookmarks:
            icon_attr = f' ICON="data:image/png;base64,{bookmark["icon_data"]}"' if bookmark.get("icon_data") else ''
            html_content += f'            <DT><A HREF="{bookmark["url"]}" ADD_DATE="{bookmark["add_date"]}"{icon_attr}>{bookmark["title"]}</A>\n'
        html_content += '        </DL><p>\n'

    # Close the HTML structure
    html_content += """    </DL><p>
</DL><p>
"""

    return html_content

def generate_embeddings(texts):
    # model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")  # Small model for testing
    model = SentenceTransformer("Salesforce/SFR-Embedding-Mistral")  # Big production model, save commented for later
    model = model.to('cuda')  # Move model to GPU
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings

def create_vector_db(embeddings):
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Use Inner Product for cosine similarity
    index.add(embeddings)
    return index

def get_domain(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    parts = domain.split('.')
    if len(parts) > 2:
        return '.'.join(parts[-2:])
    return domain

def visualize_embeddings_plotly(embeddings, labels, descriptions, urls):
    n_samples = len(embeddings)
    if n_samples < 5:
        logging.warning("Not enough samples to perform t-SNE. Skipping visualization.")
        return None

    perplexity = min(30, n_samples - 1)  # Adjust perplexity based on number of samples
    tsne = TSNE(n_components=2, random_state=0, perplexity=perplexity)
    
    try:
        reduced_embeddings = tsne.fit_transform(embeddings)
        
        # Create a color map for unique domains
        unique_domains = list(set(labels))
        color_map = {domain: f'rgb({hash(domain) % 256}, {(hash(domain) * 2) % 256}, {(hash(domain) * 3) % 256})' for domain in unique_domains}
        
        traces = []
        
        for domain in unique_domains:
            domain_indices = [i for i, label in enumerate(labels) if label == domain]
            traces.append(
                {
                    'x': reduced_embeddings[domain_indices, 0].tolist(),
                    'y': reduced_embeddings[domain_indices, 1].tolist(),
                    'mode': 'markers',
                    'name': domain,
                    'marker': {
                        'color': color_map[domain],
                        'size': 10,
                        'line': {'width': 1, 'color': 'DarkSlateGrey'}
                    },
                    'text': [f"Domain: {labels[i]}<br>Description: {descriptions[i]}<br>URL: {urls[i]}" for i in domain_indices],
                    'hoverinfo': 'text'
                }
            )
        
        return {
            'data': traces,
            'layout': {
                'title': "Interactive t-SNE visualization of bookmark embeddings",
                'xaxis': {'title': "t-SNE feature 1"},
                'yaxis': {'title': "t-SNE feature 2"},
                'hovermode': 'closest'
            }
        }
    except Exception as e:
        logging.error(f"Error during t-SNE visualization: {str(e)}")
        return None

def visualize_bookmarks(bookmarks):
    if not bookmarks:
        logging.warning("No bookmarks to visualize.")
        return None

    descriptions = [item['description'] for item in bookmarks]
    urls = [item['url'] for item in bookmarks]
    
    try:
        embeddings = generate_embeddings(descriptions)
        labels = [get_domain(url) for url in urls]
        
        vector_db = create_vector_db(embeddings)
        plot_data = visualize_embeddings_plotly(embeddings, labels, descriptions, urls)
        return plot_data
    except Exception as e:
        logging.error(f"Error during bookmark visualization: {str(e)}")
        return None

if __name__ == '__main__':
    app.run(debug=True)