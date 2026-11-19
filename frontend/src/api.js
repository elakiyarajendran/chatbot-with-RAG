import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

export const createSession = () => api.post('/sessions');
export const deleteSession = (sessionId) => api.delete(`/sessions/${sessionId}`);
export const getMessages = (sessionId) => api.get(`/sessions/${sessionId}/messages`);

export const sendChat = (sessionId, question) =>
  api.post('/chat', { session_id: sessionId, question });

export const uploadDocument = (sessionId, file) => {
  const formData = new FormData();
  formData.append('session_id', sessionId);
  formData.append('file', file);
  return axios.post('/api/documents', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const pasteDocument = (sessionId, text, docName) =>
  api.post('/documents', { session_id: sessionId, pasted_text: text, doc_name: docName || 'Pasted Document' });

export const deleteDocument = (documentId) => api.delete(`/documents/${documentId}`);

export const getCollegePolicy = () => api.get('/college-policy');

export const resetToPolicy = (sessionId) =>
  api.post('/reset-to-policy', { session_id: sessionId });

export const submitFeedback = (messageId, rating, comment) =>
  api.post('/feedback', { message_id: messageId, rating, comment });

export default api;
