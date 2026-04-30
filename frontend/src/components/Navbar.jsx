import { useAppContext } from '../context/AppContext';
import { exportZipUrl } from '../services/client';

export default function Navbar({ onRefresh, onOpenSettings }) {
  const { state, dispatch } = useAppContext();
  const savedCount = state.savedFilenames.size;

  return (
    <nav className="navbar">
      <div className="nav-inner">
        <div className="nav-logo">
          <span className="nav-logo-icon">⬡</span>
          <span className="nav-logo-text">SearchBot</span>
        </div>

        <div className="nav-actions">
          <button
            className={`nav-btn ${state.activeView === 'all' ? 'active' : ''}`}
            onClick={() => dispatch({ type: 'SET_VIEW', payload: 'all' })}
          >
            All Articles
          </button>
          <button
            className={`nav-btn ${state.activeView === 'saved' ? 'active' : ''}`}
            onClick={() => dispatch({ type: 'SET_VIEW', payload: 'saved' })}
          >
            Saved
            {savedCount > 0 && (
              <span className="saved-badge">{savedCount}</span>
            )}
          </button>
          <a
            href={exportZipUrl()}
            className="nav-btn"
            title="Download all articles as ZIP"
            download
          >
            ↓ Export
          </a>
          <button
            className="nav-refresh-btn"
            onClick={onRefresh}
            title="Refresh articles"
            aria-label="Refresh"
          >
            ↻
          </button>
          <button
            className="nav-refresh-btn"
            onClick={onOpenSettings}
            title="Settings"
            aria-label="Settings"
          >
            ⚙
          </button>
        </div>
      </div>
    </nav>
  );
}
