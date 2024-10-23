import axios from 'axios';

// Function to test the TMDB API key
export const testTmdbApi = (apiKey) => {
    const tmdbApiUrl = `https://api.themoviedb.org/3/movie/550?api_key=${apiKey}`; // Movie ID 550 is Fight Club
    return axios.get(tmdbApiUrl);
};

// Function to test Jellyfin configuration
export const testJellyfinApi = (url, token) => {
    const jellyfinApiUrl = `${url}/Users`; // Endpoint to retrieve Jellyfin users
    return axios.get(jellyfinApiUrl, {
        headers: {
            'X-Emby-Token': token // Send Jellyfin API token in the header
        }
    });
};

// Function to test the Jellyseer/Overseer configuration and fetch users
export const testJellyseerApi = (url, token) => {
    return axios.post('http://localhost:5000/api/seer/get_users', {
        SEER_API_URL: url,
        SEER_TOKEN: token
    });
};

// Function to authenticate a user in Jellyseer/Overseer
export const authenticateUser = (url, token, userName, password) => {
    return axios.post('http://localhost:5000/api/seer/login', {
        SEER_API_URL: url,
        SEER_TOKEN: token,
        SEER_USER_NAME: userName,
        SEER_PASSWORD: password
    });
};

// Function to fetch Jellyfin libraries
export function fetchJellyfinLibraries(apiUrl, apiKey) {
    return axios.post(`/api/jellyfin/libraries`, {
        JELLYFIN_API_URL: apiUrl,
        JELLYFIN_TOKEN: apiKey
    });
}

// Function to fetch Plex libraries
export async function getPlexLibraries(plexUrl, plexToken) {
    const apiUrl = `http://localhost:5000/api/plex/libraries`;
    try {
        const response = await axios.post(apiUrl, {
            PLEX_API_URL: plexUrl,
            PLEX_TOKEN: plexToken,
        });
        
        if (response.status === 200) {
            return response.data;
        }
    } catch (error) {
        console.error('Error fetching Plex libraries:', error);
    }

    return { items: [] };
}
