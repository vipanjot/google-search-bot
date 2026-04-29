import { useEffect, useCallback } from 'react';
import { useAppContext } from './store/AppContext';
import Navbar from './components/Navbar';
import HeroSearch from './components/HeroSearch';
import ViewToggle from './components/ViewToggle';
import FilterBar from './components/FilterBar';
import ArticleGrid from './components/ArticleGrid';
import ArticleModal from './components/ArticleModal';
import StatusToast from './components/StatusToast';
import { fetchArticles, fetchSaved, fetchSearchStatus } from './api/client';

export default function App() {
  const { state, dispatch } = useAppContext();

  const loadArticles = useCallback(async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      const data = await fetchArticles(state.searchQuery, state.filterType);
      dispatch({ type: 'SET_ARTICLES', payload: data });
    } catch (e) {
      console.error('Failed to load articles:', e);
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [state.searchQuery, state.filterType, dispatch]);

  const loadSaved = useCallback(async () => {
    try {
      const data = await fetchSaved();
      dispatch({ type: 'SET_SAVED', payload: data });
    } catch (e) {
      console.error('Failed to load saved:', e);
    }
  }, [dispatch]);

  // Initial load
  useEffect(() => {
    loadArticles();
    loadSaved();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Debounced re-fetch on search/filter changes
  useEffect(() => {
    const t = setTimeout(loadArticles, 280);
    return () => clearTimeout(t);
  }, [state.searchQuery, state.filterType]); // eslint-disable-line react-hooks/exhaustive-deps

  // Poll bot search status
  useEffect(() => {
    if (!state.searchRunning) return;
    const interval = setInterval(async () => {
      try {
        const status = await fetchSearchStatus();
        dispatch({ type: 'SET_SEARCH_RUNNING', payload: status.running });
        dispatch({ type: 'SET_SEARCH_MESSAGE', payload: status.message });
        if (!status.running) {
          clearInterval(interval);
          loadArticles();
        }
      } catch {
        clearInterval(interval);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [state.searchRunning]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="app">
      <Navbar onRefresh={loadArticles} />
      <main className="main-content">
        <HeroSearch />
        <div className="content-section">
          <ViewToggle />
          <FilterBar />
          <ArticleGrid />
        </div>
      </main>
      <ArticleModal />
      <StatusToast />
    </div>
  );
}
