document.addEventListener('DOMContentLoaded', () => {
    const recommendForm = document.getElementById('recommend-form');
    const clearHistoryForm = document.getElementById('clear-history-form');
    const resultDiv = document.getElementById('result');
    const loadingSpinner = document.getElementById('loading-spinner');

    // Handle recommendation form submission
    recommendForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(recommendForm);

        // Show loading spinner
        loadingSpinner.style.display = 'block';
        resultDiv.innerHTML = '';

        try {
            const response = await fetch('/recommend', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (response.ok) {
                displayRecommendations(data);
            } else {
                resultDiv.innerHTML = `<p style="color: #e50914;">Error: ${data.error}</p>`;
            }
        } catch (error) {
            resultDiv.innerHTML = `<p style="color: #e50914;">Error: Failed to fetch recommendations.</p>`;
            console.error('Error:', error);
        } finally {
            loadingSpinner.style.display = 'none';
        }
    });

    // Handle clear history form submission
    clearHistoryForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        try {
            const response = await fetch('/clear_history', {
                method: 'POST'
            });
            const data = await response.json();

            if (response.ok) {
                // Reload the page to update the history section
                window.location.reload();
            } else {
                alert(`Error: ${data.error}`);
            }
        } catch (error) {
            alert('Error: Failed to clear history.');
            console.error('Error:', error);
        }
    });

    // Function to display recommendations
    function displayRecommendations(movies) {
        if (movies.length === 0) {
            resultDiv.innerHTML = '<p>No recommendations found.</p>';
            return;
        }

        const cardGrid = document.createElement('div');
        cardGrid.className = 'card-grid';

        movies.forEach(movie => {
            const card = document.createElement('div');
            card.className = 'card';

            const img = movie.poster_path
                ? `<img src="${movie.poster_path}" alt="${movie.title}">`
                : '<div class="no-poster">No Poster Available</div>';

            card.innerHTML = `
                ${img}
                <div class="card-overlay">
                    <h3>${movie.title}</h3>
                    <p><strong>Genres:</strong> ${movie.genres}</p>
                    <p>${movie.overview}</p>
                </div>
            `;

            cardGrid.appendChild(card);
        });

        resultDiv.innerHTML = '<h2>Recommended Movies</h2>';
        resultDiv.appendChild(cardGrid);
    }
});

// Filter movies based on search input (already included in index.html but repeated here for completeness)
function filterMovies() {
    const input = document.getElementById('movie_search').value.toLowerCase();
    const select = document.getElementById('movie_id');
    const options = select.getElementsByTagName('option');

    for (let i = 0; i < options.length; i++) {
        const text = options[i].text.toLowerCase();
        if (text.includes(input) || input === '') {
            options[i].style.display = '';
        } else {
            options[i].style.display = 'none';
        }
    }
}