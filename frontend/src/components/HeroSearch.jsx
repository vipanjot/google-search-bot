import { useState } from 'react';
import { useAppContext } from '../context/AppContext';
import { triggerSearch } from '../services/client';

export default function HeroSearch() {
  const { state, dispatch } = useAppContext();
  const [botQuery, setBotQuery] = useState('');
  const [botNum, setBotNum] = useState(20);
  const [engine, setEngine] = useState('duckduckgo');
  const [showOptions, setShowOptions] = useState(false);
  const [googleKey, setGoogleKey] = useState('');
  const [googleCx, setGoogleCx] = useState('');

  const handleBotSearch = async () => {
    const q = botQuery.trim();
    if (!q || state.searchRunning) return;
    try {
      await triggerSearch(q, botNum, engine, {
        google_api_key: googleKey,
        google_cx: googleCx,
      });
      dispatch({ type: 'SET_SEARCH_RUNNING', payload: true });
      dispatch({ type: 'SET_SEARCH_MESSAGE', payload: `Searching: "${q}"` });
      setBotQuery('');
    } catch (e) {
      console.error('Search trigger failed:', e);
    }
  };

  return (
    <section className="hero">
      <div className="hero-content">
        <h1 className="hero-title">
          <span className="gradient-text">Search & Discover</span>
        </h1>
        <p className="hero-subtitle">
          Scrape the web, save articles, build your knowledge base
        </p>

        {/* Filter input */}
        <div className="search-bar-wrapper">
          <span className="search-icon">⌕</span>
          <input
            className="search-bar"
            type="text"
            placeholder="Filter saved articles by title, summary, or tag..."
            value={state.searchQuery}
            onChange={e => dispatch({ type: 'SET_SEARCH_QUERY', payload: e.target.value })}
          />
          {state.searchQuery && (
            <button
              className="search-clear"
              onClick={() => dispatch({ type: 'SET_SEARCH_QUERY', payload: '' })}
              aria-label="Clear filter"
            >
              ✕
            </button>
          )}
        </div>

        {/* Bot search */}
        <div className="bot-panel">
          <div className="bot-row">
            <input
              className="bot-input"
              type="text"
              placeholder="Search the web and scrape new articles..."
              value={botQuery}
              onChange={e => setBotQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleBotSearch()}
              disabled={state.searchRunning}
            />
            <button
              className={`bot-btn ${state.searchRunning ? 'running' : ''}`}
              onClick={handleBotSearch}
              disabled={!botQuery.trim() || state.searchRunning}
            >
              {state.searchRunning ? <span className="spinner-small" /> : 'Scrape Web'}
            </button>
            <button
              className="options-toggle"
              onClick={() => setShowOptions(v => !v)}
              aria-label="Toggle options"
            >
              {showOptions ? '▲' : '▼'} Options
            </button>
          </div>

          {showOptions && (
            <div className="bot-options">
              <label className="option-label">
                <span>Results</span>
                <input
                  type="number"
                  min={5}
                  max={100}
                  value={botNum}
                  onChange={e => setBotNum(Number(e.target.value))}
                  className="option-input number"
                />
              </label>
              <label className="option-label">
                <span>Engine</span>
                <select
                  value={engine}
                  onChange={e => setEngine(e.target.value)}
                  className="option-input"
                >
                  <option value="duckduckgo">DuckDuckGo</option>
                  <option value="google">Google API</option>
                </select>
              </label>
              {engine === 'google' && (
                <>
                  <label className="option-label wide">
                    <span>API Key</span>
                    <input
                      type="text"
                      placeholder="AIza..."
                      value={googleKey}
                      onChange={e => setGoogleKey(e.target.value)}
                      className="option-input"
                    />
                  </label>
                  <label className="option-label wide">
                    <span>CX ID</span>
                    <input
                      type="text"
                      placeholder="Search engine ID"
                      value={googleCx}
                      onChange={e => setGoogleCx(e.target.value)}
                      className="option-input"
                    />
                  </label>
                </>
              )}
            </div>
          )}

          {state.searchRunning && (
            <div className="bot-status">
              <span className="pulse-dot" />
              <span>{state.searchMessage}</span>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
