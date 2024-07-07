import logging
from urllib.parse import urlparse
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from sklearn.manifold import TSNE

model = None

def load_model():
    global model
    if model is None:
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")  # Small model for testing
        # model = SentenceTransformer("Salesforce/SFR-Embedding-Mistral")  # Big production model, commented for later
        model = model.to('cuda')  # Move model to GPU
    return model

def generate_embeddings(texts):
    model = load_model()
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