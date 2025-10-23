import pandas as pd
import numpy as np
from sklearn.decomposition import TruncatedSVD
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import requests
import sqlite3
import os

# For the flask session
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# TMDB API configuration
TMDB_API_KEY = ''
TMDB_BASE_URL = 'https://api.themoviedb.org/3'

# Database setup
DB_PATH = 'database/database.db'

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS history (
            user_id INTEGER,
            movie_id INTEGER,
            title TEXT,
            genres TEXT,
            poster_path TEXT,
            overview TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')
        c.execute('INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)', (1, 'default_user'))
        conn.commit()

if not os.path.exists(DB_PATH):
    init_db()

# def load_data(max_ratings=1500000):
def load_data():
    try:
        movies_df = pd.read_csv('dataset/filtered_movies.csv')
        ratings_df = pd.read_csv('dataset/filtered_ratings.csv', usecols=['userId', 'movieId', 'rating']) #[:max_ratings]
        valid_movie_ids = ratings_df['movieId'].unique()
        movies_df = movies_df[movies_df['movieId'].isin(valid_movie_ids)]
        return movies_df, ratings_df
    except FileNotFoundError as e:
        print(f"Error: Data file not found - {e}")
        raise
    except Exception as e:
        print(f"Error loading data: {e}")
        raise

# Initialize data
try:
    movies_df, ratings_df = load_data()
except Exception as e:
    print(f"Failed to initialize data: {e}")
    exit(1)

# Extract unique genres
def get_unique_genres():
    return sorted(set(movies_df['genres'].str.split('|').explode()))

unique_genres = get_unique_genres()

# Create ratings matrix and perform SVD
ratings_matrix = ratings_df.pivot(index='userId', columns='movieId', values='rating').fillna(0)
if ratings_matrix.shape[1] == 0:
    print("Error: Ratings matrix has no movies. Check ratings data.")
    exit(1)

try:
    svd = TruncatedSVD(n_components=50, random_state=42)
    latent_matrix = svd.fit_transform(ratings_matrix)
    movie_latent_matrix = svd.components_.T
except Exception as e:
    print(f"Error during SVD: {e}")
    exit(1)

# TMDB API helper
def get_tmdb_details(title):
    try:
        url = f"{TMDB_BASE_URL}/search/movie?api_key={TMDB_API_KEY}&query={title}"
        response = requests.get(url)
        if response.status_code == 200:
            results = response.json().get('results', [])
            if results:
                movie = results[0]
                return {
                    'poster_path': f"https://image.tmdb.org/t/p/w200{movie['poster_path']}" if movie.get('poster_path') else None,
                    'overview': movie.get('overview', 'No description available.')
                }
        return {'poster_path': None, 'overview': 'Failed to fetch TMDB details.'}
    except Exception as e:
        print(f"Error fetching TMDB details for {title}: {e}")
        return {'poster_path': None, 'overview': 'Error contacting TMDB API.'}

@app.route('/')
def home():
    session.setdefault('recommendation_history', [])
    movies_list = movies_df[['movieId', 'title']].to_dict('records')
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Use DISTINCT on movie_id to remove duplicates
        c.execute('SELECT DISTINCT movie_id, title, genres, poster_path, overview, timestamp FROM history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10', (1,))
        history = [{'id': row[0], 'title': row[1], 'genres': row[2], 'poster_path': row[3], 'overview': row[4], 'timestamp': row[5]} for row in c.fetchall()]
    return render_template('index.html', movies=movies_list, genres=unique_genres, history=history)

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        movie_id = request.form.get('movie_id')
        selected_genre = request.form.get('genre')
        
        if not movie_id:
            return jsonify({"error": "Missing movie_id"}), 400
        
        movie_id = int(movie_id)
        if movie_id not in ratings_matrix.columns:
            return jsonify({"error": f"Movie ID {movie_id} not found"}), 400

        movie_idx = ratings_matrix.columns.get_loc(movie_id)
        movie_vector = movie_latent_matrix[movie_idx]
        movie_similarities = np.dot(movie_latent_matrix, movie_vector)
        
        # Sort by similarity scores
        similar_indices = np.argsort(movie_similarities)[::-1]
        
        recommended_movies = []
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            for idx in similar_indices:
                if len(recommended_movies) >= 10:
                    break
                rec_movie_id = ratings_matrix.columns[idx]
                movie = movies_df[movies_df['movieId'] == rec_movie_id].iloc[0]
                if selected_genre and selected_genre != 'All' and selected_genre not in movie['genres'].split('|'):
                    continue
                tmdb_details = get_tmdb_details(movie['title'])
                recommended_movie = {
                    'id': int(rec_movie_id),
                    'title': movie['title'],
                    'genres': movie['genres'],
                    'poster_path': tmdb_details['poster_path'],
                    'overview': tmdb_details['overview']
                }
                recommended_movies.append(recommended_movie)
                try:
                    c.execute('INSERT INTO history (user_id, movie_id, title, genres, poster_path, overview) VALUES (?, ?, ?, ?, ?, ?)',
                             (1, rec_movie_id, movie['title'], movie['genres'], 
                              tmdb_details['poster_path'], tmdb_details['overview']))
                    conn.commit()
                except sqlite3.Error as e:
                    print(f"SQLite error saving history: {e}")

        if not recommended_movies:
            return jsonify({"error": f"No recommendations found for genre: {selected_genre or 'Any'}"}), 404

        session['recommendation_history'] = recommended_movies + session.get('recommendation_history', [])[:5]
        session.modified = True
        return jsonify(recommended_movies)

    except Exception as e:
        print(f"Error in recommend: {str(e)}")
        return jsonify({"error": f"Recommendation failed: {str(e)}"}), 500

@app.route('/clear_history', methods=['POST'])
def clear_history():
    try:
        session['recommendation_history'] = []
        session.modified = True
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('DELETE FROM history WHERE user_id = ?', (1,))
            conn.commit()
        return jsonify({"message": "History cleared successfully"})
    except Exception as e:
        print(f"Error clearing history: {str(e)}")
        return jsonify({"error": "Failed to clear history"}), 500

if __name__ == '__main__':
    print(f"Ratings matrix shape: {ratings_matrix.shape}")
    print(f"Movie latent matrix shape: {movie_latent_matrix.shape}")
    app.run(debug=True)