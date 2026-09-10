/**
 * API client for communicating with the FastAPI backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || '';

/**
 * Upload an image and run the full transliteration pipeline.
 * @param {File} file - Image file to process.
 * @param {function} onProgress - Optional progress callback.
 * @returns {Promise<object>} TransliterationResponse
 */
export async function transliterateImage(file, onProgress) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/api/transliterate`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Server error: ${response.status}`);
  }

  return response.json();
}

/**
 * Check backend health status.
 * @returns {Promise<object>} HealthResponse
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) {
    throw new Error('Backend is not responding');
  }
  return response.json();
}

/**
 * Convert a base64 string to a data URL for <img> src.
 * @param {string} base64 - Base64-encoded image data.
 * @param {string} mimeType - MIME type (default: image/jpeg).
 * @returns {string} Data URL
 */
export function base64ToDataUrl(base64, mimeType = 'image/jpeg') {
  return `data:${mimeType};base64,${base64}`;
}
