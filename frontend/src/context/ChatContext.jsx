import { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';
import toast from 'react-hot-toast';
import {
  createSession,
  deleteSession,
  getMessages,
  sendChat,
  uploadDocument,
  pasteDocument,
  deleteDocument,
  resetToPolicy,
  submitFeedback,
} from '../api';

const ChatContext = createContext(null);
export const useChatContext = () => useContext(ChatContext);

export function ChatProvider({ children }) {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [activeDoc, setActiveDoc] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [starterQuestions, setStarterQuestions] = useState([]);
  const initialized = useRef(false);

  const initSession = useCallback(async () => {
    if (initialized.current) return;
    initialized.current = true;
    try {
      setIsInitializing(true);
      const res = await createSession();
      setSessionId(res.data.session_id);
      setActiveDoc(res.data.active_document);
    } catch (e) {
      toast.error('Failed to connect to server. Is Django running?');
    } finally {
      setIsInitializing(false);
    }
  }, []);

  useEffect(() => { initSession(); }, [initSession]);

  const loadHistory = useCallback(async (sid) => {
    try {
      const res = await getMessages(sid);
      setMessages(res.data.messages.map(m => ({
        id: m.message_id,
        role: m.role,
        text: m.text,
        status: m.status,
        citations: m.citations || [],
        missingInfo: m.missing_info,
        createdAt: m.created_at,
      })));
    } catch {}
  }, []);

  const ask = useCallback(async (question) => {
    if (!sessionId || !question.trim()) return;
    setIsLoading(true);

    const userMsg = { id: `u-${Date.now()}`, role: 'user', text: question };
    setMessages(prev => [...prev, userMsg]);

    try {
      const res = await sendChat(sessionId, question);
      const d = res.data;
      setMessages(prev => [...prev, {
        id: d.message_id,
        role: 'bot',
        text: d.answer,
        status: d.status,
        citations: d.citations || [],
        missingInfo: d.missing_info,
        createdAt: d.created_at,
      }]);
    } catch (err) {
      const errText = err.response?.data?.error || err.message || 'Server error.';
      setMessages(prev => [...prev, {
        id: `err-${Date.now()}`,
        role: 'bot',
        text: `❌ ${errText}`,
        status: 'ERROR',
        citations: [],
      }]);
      toast.error('Failed to get response');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const uploadDoc = useCallback(async (file) => {
    if (!sessionId) return;
    setIsLoading(true);
    try {
      const res = await uploadDocument(sessionId, file);
      setActiveDoc(res.data);
      setMessages([]);
      toast.success(`"${res.data.name}" loaded! (${res.data.page_count} pages, ${res.data.mode} mode)`);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Upload failed');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const pasteDoc = useCallback(async (text, name) => {
    if (!sessionId) return;
    setIsLoading(true);
    try {
      const res = await pasteDocument(sessionId, text, name);
      setActiveDoc(res.data);
      setMessages([]);
      toast.success(`Document loaded! (${res.data.page_count} page(s))`);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to load pasted text');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const resetToDefaultPolicy = useCallback(async () => {
    if (!sessionId) return;
    setIsLoading(true);
    try {
      const res = await resetToPolicy(sessionId);
      setActiveDoc(res.data.document);
      setMessages([]);
      toast.success('Reset to Meridian College Policy Handbook!');
    } catch (err) {
      toast.error('Failed to reset document');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const clearSession = useCallback(async () => {
    if (!sessionId) return;
    try {
      await deleteSession(sessionId);
      setMessages([]);
      setActiveDoc(null);
      setSessionId(null);
      initialized.current = false;
      toast.success('Session cleared');
      await initSession();
    } catch {}
  }, [sessionId, initSession]);

  const rateBotMessage = useCallback(async (messageId, rating) => {
    try {
      await submitFeedback(messageId, rating, '');
      toast.success(rating === 'up' ? '👍 Thanks for the feedback!' : '👎 Noted, we\'ll improve!');
    } catch {}
  }, []);

  return (
    <ChatContext.Provider value={{
      sessionId, messages, activeDoc, isLoading, isInitializing,
      starterQuestions, setStarterQuestions,
      ask, uploadDoc, pasteDoc, resetToDefaultPolicy, clearSession, rateBotMessage,
    }}>
      {children}
    </ChatContext.Provider>
  );
}
