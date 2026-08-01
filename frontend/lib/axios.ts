import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8001',
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Prevent infinite loops
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const response = await axios.post('http://localhost:8001/api/token/refresh/', {
                refresh: refreshToken,
            });

            if (response.status === 200) {
                const { access } = response.data;
                localStorage.setItem('access_token', access);
                
                // Update header and retry original request
                originalRequest.headers.Authorization = `Bearer ${access}`;
                return api(originalRequest);
            }
        }
      } catch (refreshError) {
        // Refresh token failed or expired
        console.error('Refresh token failed', refreshError);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }
    
    // If error is 401 and we don't have a refresh token or it failed
    if (error.response?.status === 401) {
         localStorage.removeItem('access_token');
         localStorage.removeItem('refresh_token');
         window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);

export default api;
