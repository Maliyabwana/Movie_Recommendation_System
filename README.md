# Movie Recommendation System

A collaborative filtering-based movie recommendation web application built with Flask, SVD dimensionality reduction, and The Movie Database (TMDB) API integration. Users can search and select movies, filter by genre, and receive personalized recommendations based on user ratings data.

![Movie Recommendation System Demo](/img/demo.png) <!-- Replace with a screenshot if you have one -->

## Features

- **Movie Search & Selection**: Search through a catalog of movies and select one as a starting point for recommendations.
- **Genre Filtering**: Narrow recommendations by specific genres (e.g., Action, Drama, Comedy).
- **SVD-Based Recommendations**: Uses Truncated Singular Value Decomposition (SVD) on a user-movie rating matrix for efficient similarity computation.
- **TMDB Integration**: Fetches movie posters and overviews dynamically via the TMDB API.
- **Recommendation History**: Tracks and displays past recommendations with deduplication to avoid redundancy.
- **Responsive UI**: Clean, card-based layout for displaying movie details and recommendations.

## Tech Stack

- **Backend**: Python 3.x, Flask (web framework), Pandas & NumPy (data processing), scikit-learn (SVD decomposition), SQLite (persistent storage).
- **Frontend**: HTML, CSS and JavaScript.
- **APIs**: The Movie Database (TMDB) API for movie metadata.
- **Data**: Processed MovieLens dataset (filtered movies and ratings).

## Prerequisites

- Python 3.8+ (with pip).
- A TMDB API key (free from [themoviedb.org](https://www.themoviedb.org/)).
- Git (for cloning the repo).

## Installation

To run:
```bash
 git clone https://github.com/Maliyabwana/Movie_Recommendation_System.git
```
```bash
 cd Movie_Recommendation_System
```
```bash
 python app.py
```
