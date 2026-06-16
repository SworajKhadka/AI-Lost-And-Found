import axios from 'axios'

// All requests go to the FastAPI backend running locally
const api = axios.create({
  baseURL: 'http://localhost:8000',
})

export default api
