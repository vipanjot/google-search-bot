import { useAppContext } from '../store/AppContext';

export default function ViewToggle() {
  const { state, dispatch } = useAppContext();
  const savedCount = state.savedFilenames.size;
  const allCount = state.articles.length;
  const savedArticles = state.articles.filter(a => state.savedFilenames.has(a.filename));

  return (
    <div className="view-toggle-bar">
      <div className="view-tabs">
        <button
          className={`view-tab ${state.activeView === 'all' ? 'active' : ''}`}
          onClick={() => dispatch({ type: 'SET_VIEW', payload: 'all' })}
        >
          All Articles
          <span className="tab-count">{allCount}</span>
        </button>
        <button
          className={`view-tab ${state.activeView === 'saved' ? 'active' : ''}`}
          onClick={() => dispatch({ type: 'SET_VIEW', payload: 'saved' })}
        >
          Saved
          <span className={`tab-count ${savedCount > 0 ? 'accent' : ''}`}>
            {savedCount}
          </span>
        </button>
      </div>
    </div>
  );
}
