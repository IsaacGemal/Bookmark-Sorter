import os
import json
import logging
import re
from flask import Flask, render_template, request, jsonify
from anthropic import Anthropic
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)

# Set up logging
logging.basicConfig(filename='bookmark_organizer.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

anthropic_key = os.getenv('ANTHROPIC_API_KEY')
client = Anthropic(api_key=anthropic_key)

@app.route('/')
def index():
    return render_template('index.html')

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
        return jsonify(organized_bookmarks)

def parse_bookmarks(file):
    content = file.read().decode('utf-8')
    bookmark_pattern = re.compile(r'<DT><A HREF="(.*?)" ADD_DATE="(\d+)"[^>]*>(.*?)</A>|"url": ?"(.*?)",\s*"add_date": ?"(.*?)",\s*"title": ?"(.*?)"', re.DOTALL)
    
    bookmarks = []
    for match in bookmark_pattern.finditer(content):
        if match.group(1):  # HTML format
            bookmark = {
                "url": match.group(1),
                "add_date": match.group(2),
                "title": match.group(3)
            }
        else:  # JSON format
            bookmark = {
                "url": match.group(4),
                "add_date": match.group(5),
                "title": match.group(6)
            }
        bookmarks.append(bookmark)
    return bookmarks

def organize_bookmarks_in_chunks(bookmarks, chunk_size=25):
    organized_bookmarks = []
    for i in range(0, len(bookmarks), chunk_size):
        chunk = bookmarks[i:i + chunk_size]
        logging.info(f'Processing chunk {i // chunk_size + 1} with {len(chunk)} bookmarks')
        organized_chunk = organize_bookmarks(chunk)
        organized_bookmarks.extend(organized_chunk)
    return organized_bookmarks

def organize_bookmarks(bookmarks):
    logging.info(f'Sending {len(bookmarks)} bookmarks to Anthropic API for organization')
    message = f"""Here is a list of bookmarks:

{json.dumps(bookmarks, indent=2)}

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
        logging.info(f'Successfully organized {len(organized_bookmarks)} bookmarks')
        return organized_bookmarks
    except Exception as e:
        logging.error(f'Error organizing bookmarks: {str(e)}')
        raise

if __name__ == '__main__':
    app.run(debug=True)