// Configuration - Updated with deployed AWS resources
const CONFIG = {
    region: 'eu-west-3',
    userPoolId: 'eu-west-3_duJT0eq8g',
    clientId: 'k9oqa9c137pknttb5fdsjsis',
    apiEndpoint: 'https://vsb559um7e.execute-api.eu-west-3.amazonaws.com/dev'
};

// Global state
let currentUser = null;
let userPool = null;
let idToken = null;

// Initialize Cognito User Pool
function initializeCognito() {
    const poolData = {
        UserPoolId: CONFIG.userPoolId,
        ClientId: CONFIG.clientId
    };
    userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);
}

// Check if user is already logged in
function checkSession() {
    const cognitoUser = userPool.getCurrentUser();
    
    if (cognitoUser) {
        cognitoUser.getSession((err, session) => {
            if (err) {
                console.error('Session error:', err);
                showAuthContainer();
                return;
            }
            
            if (session.isValid()) {
                idToken = session.getIdToken().getJwtToken();
                currentUser = {
                    username: cognitoUser.getUsername(),
                    email: session.getIdToken().payload.email
                };
                showAppContainer();
                loadMovies();
            } else {
                showAuthContainer();
            }
        });
    } else {
        showAuthContainer();
    }
}

// Login handler
function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const errorElement = document.getElementById('login-error');
    
    errorElement.textContent = '';
    errorElement.classList.remove('show');
    
    const authenticationData = {
        Username: username,
        Password: password
    };
    
    const authenticationDetails = new AmazonCognitoIdentity.AuthenticationDetails(authenticationData);
    
    const userData = {
        Username: username,
        Pool: userPool
    };
    
    const cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);
    
    cognitoUser.authenticateUser(authenticationDetails, {
        onSuccess: (session) => {
            idToken = session.getIdToken().getJwtToken();
            currentUser = {
                username: cognitoUser.getUsername(),
                email: session.getIdToken().payload.email
            };
            showAppContainer();
            loadMovies();
        },
        onFailure: (err) => {
            console.error('Login error:', err);
            errorElement.textContent = err.message || 'Échec de la connexion. Veuillez réessayer.';
            errorElement.classList.add('show');
        }
    });
}

// Logout handler
function handleLogout() {
    const cognitoUser = userPool.getCurrentUser();
    if (cognitoUser) {
        cognitoUser.signOut();
    }
    currentUser = null;
    idToken = null;
    showAuthContainer();
}

// Show/hide containers
function showAuthContainer() {
    document.getElementById('auth-container').style.display = 'flex';
    document.getElementById('app-container').style.display = 'none';
}

function showAppContainer() {
    document.getElementById('auth-container').style.display = 'none';
    document.getElementById('app-container').style.display = 'block';
    document.getElementById('user-email').textContent = currentUser.email || currentUser.username;
}

// API call helper
async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Authorization': idToken,
            'Content-Type': 'application/json'
        }
    };
    
    if (body) {
        options.body = JSON.stringify(body);
    }
    
    const response = await fetch(`${CONFIG.apiEndpoint}${endpoint}`, options);
    
    if (response.status === 401) {
        // Token expired, logout
        handleLogout();
        throw new Error('Session expirée. Veuillez vous reconnecter.');
    }
    
    if (response.status === 204) {
        return null; // No content
    }
    
    const data = await response.json();
    
    if (!response.ok) {
        throw new Error(data.error || `HTTP ${response.status}`);
    }
    
    return data;
}

// Load movies
async function loadMovies() {
    const loadingElement = document.getElementById('movies-loading');
    const errorElement = document.getElementById('movies-error');
    const emptyElement = document.getElementById('movies-empty');
    const listElement = document.getElementById('movies-list');
    
    loadingElement.style.display = 'block';
    errorElement.textContent = '';
    errorElement.classList.remove('show');
    emptyElement.style.display = 'none';
    listElement.innerHTML = '';
    
    try {
        const movies = await apiCall('/movies');
        loadingElement.style.display = 'none';
        
        if (movies.length === 0) {
            emptyElement.style.display = 'block';
        } else {
            renderMovies(movies);
        }
    } catch (error) {
        console.error('Error loading movies:', error);
        loadingElement.style.display = 'none';
        errorElement.textContent = error.message || 'Échec du chargement des films';
        errorElement.classList.add('show');
    }
}

// Render movies
function renderMovies(movies) {
    const listElement = document.getElementById('movies-list');
    const template = document.getElementById('movie-card-template');
    
    movies.forEach(movie => {
        const card = template.content.cloneNode(true);
        
        // Set movie data
        card.querySelector('.movie-title').textContent = movie.title;
        
        const statusBadge = card.querySelector('.movie-status-badge');
        statusBadge.textContent = movie.status;
        statusBadge.classList.add(movie.status);
        
        card.querySelector('.movie-created-by').textContent = `Créé par : ${movie.createdBy}`;
        card.querySelector('.movie-created-at').textContent = `Créé le : ${new Date(movie.createdAt * 1000).toLocaleDateString('fr-FR')}`;
        
        // Status toggle button
        const toggleStatusBtn = card.querySelector('.btn-toggle-status');
        toggleStatusBtn.textContent = movie.status === 'wishlist' ? 'Marquer comme téléchargé' : 'Remettre en liste';
        toggleStatusBtn.onclick = () => toggleMovieStatus(movie.movieId, movie.status);
        
        // Interest toggle button - hide if movie is downloaded
        const isInterested = movie.interestedUsers && movie.interestedUsers.includes(currentUser.username);
        const toggleInterestBtn = card.querySelector('.btn-toggle-interest');
        
        if (movie.status === 'downloaded') {
            // Hide the interest button for downloaded movies
            toggleInterestBtn.style.display = 'none';
        } else {
            toggleInterestBtn.textContent = isInterested ? 'Retirer mon intérêt' : 'Je veux ce film';
            toggleInterestBtn.onclick = () => toggleInterest(movie.movieId, isInterested);
        }
        
        // Delete button
        const deleteBtn = card.querySelector('.btn-delete');
        deleteBtn.onclick = () => deleteMovie(movie.movieId, movie.title);
        
        // Interested users
        const interestCount = card.querySelector('.interest-count');
        interestCount.textContent = movie.interestedUsers ? movie.interestedUsers.length : 0;
        
        const usersList = card.querySelector('.interested-users-list');
        if (movie.interestedUsers && movie.interestedUsers.length > 0) {
            movie.interestedUsers.forEach(userId => {
                const badge = document.createElement('span');
                badge.className = 'user-badge';
                if (userId === currentUser.username) {
                    badge.classList.add('current-user');
                }
                badge.textContent = userId;
                usersList.appendChild(badge);
            });
        }
        
        listElement.appendChild(card);
    });
}

// Add movie
async function handleAddMovie(event) {
    event.preventDefault();
    
    const titleInput = document.getElementById('movie-title');
    const errorElement = document.getElementById('add-movie-error');
    const successElement = document.getElementById('add-movie-success');
    
    const title = titleInput.value.trim();
    
    errorElement.textContent = '';
    errorElement.classList.remove('show');
    successElement.textContent = '';
    successElement.classList.remove('show');
    
    if (!title) {
        errorElement.textContent = 'Veuillez entrer un titre de film';
        errorElement.classList.add('show');
        return;
    }
    
    try {
        await apiCall('/movies', 'POST', { title });
        successElement.textContent = 'Film ajouté avec succès !';
        successElement.classList.add('show');
        titleInput.value = '';
        
        // Reload movies
        setTimeout(() => {
            successElement.classList.remove('show');
            loadMovies();
        }, 1500);
    } catch (error) {
        console.error('Error adding movie:', error);
        errorElement.textContent = error.message || 'Échec de l\'ajout du film';
        errorElement.classList.add('show');
    }
}

// Toggle movie status
async function toggleMovieStatus(movieId, currentStatus) {
    const newStatus = currentStatus === 'wishlist' ? 'downloaded' : 'wishlist';
    
    try {
        await apiCall(`/movies/${movieId}/status`, 'PATCH', { status: newStatus });
        loadMovies();
    } catch (error) {
        console.error('Error updating status:', error);
        alert(error.message || 'Échec de la mise à jour du statut');
    }
}

// Toggle interest
async function toggleInterest(movieId, isInterested) {
    try {
        if (isInterested) {
            await apiCall(`/movies/${movieId}/interest`, 'DELETE');
        } else {
            await apiCall(`/movies/${movieId}/interest`, 'POST');
        }
        loadMovies();
    } catch (error) {
        console.error('Error toggling interest:', error);
        alert(error.message || 'Échec de la mise à jour de l\'intérêt');
    }
}

// Delete movie
async function deleteMovie(movieId, title) {
    if (!confirm(`Êtes-vous sûr de vouloir supprimer "${title}" ?`)) {
        return;
    }
    
    try {
        await apiCall(`/movies/${movieId}`, 'DELETE');
        loadMovies();
    } catch (error) {
        console.error('Error deleting movie:', error);
        alert(error.message || 'Échec de la suppression du film');
    }
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeCognito();
    
    // Event listeners
    document.getElementById('login-form-element').addEventListener('submit', handleLogin);
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    document.getElementById('add-movie-form').addEventListener('submit', handleAddMovie);
    document.getElementById('refresh-btn').addEventListener('click', loadMovies);
    
    // Check session
    checkSession();
});
