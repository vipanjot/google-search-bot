import { useAppContext } from '../context/AppContext';
import { fetchArticle, saveArticle, unsaveArticle } from '../services/client';

function TypeBadge({ type }) {
  const labels = { concept: 'Concept', source: 'Source', synthesis: 'Synthesis' };
  return (
    <span className={`type-badge type-${type}`}>
      {labels[type] || type}
    </span>
  );
}

function safeHostname(url) {
  try {
    return new URL(url).hostname.replace('www.', '');
  } catch {
    return url.slice(0, 30);
  }
}

export default function ArticleCard({ article, index = 0 }) {
  const { state, dispatch } = useAppContext();
  const isSaved = state.savedFilenames.has(article.filename);

  const handleOpen = async () => {
    dispatch({ type: 'SET_ARTICLE_LOADING', payload: true });
    try {
      const data = await fetchArticle(article.filename);
      dispatch({ type: 'SET_ACTIVE_ARTICLE', payload: data });
    } catch (e) {
      console.error('Failed to load article:', e);
    } finally {
      dispatch({ type: 'SET_ARTICLE_LOADING', payload: false });
    }
  };

  const handleSaveToggle = async (e) => {
    e.stopPropagation();
    dispatch({ type: 'TOGGLE_SAVED', payload: article.filename });
    try {
      if (isSaved) {
        await unsaveArticle(article.filename);
      } else {
        await saveArticle(article.filename);
      }
    } catch {
      dispatch({ type: 'TOGGLE_SAVED', payload: article.filename });
    }
  };

  const delay = `${Math.min(index * 35, 350)}ms`;

  return (
    <article
      className={`article-card ${isSaved ? 'saved' : ''}`}
      style={{ animationDelay: delay }}
      onClick={handleOpen}
      role="button"
      tabIndex={0}
      onKeyDown={e => e.key === 'Enter' && handleOpen()}
    >
      <div className="card-header">
        <TypeBadge type={article.type} />
        <button
          className={`save-btn ${isSaved ? 'saved' : ''}`}
          onClick={handleSaveToggle}
          title={isSaved ? 'Remove from saved' : 'Save article'}
          aria-label={isSaved ? 'Remove from saved' : 'Save article'}
        >
          {isSaved ? '★' : '☆'}
        </button>
      </div>

      <h3 className="card-title">{article.title}</h3>

      {article.summary && (
        <p className="card-summary">
          {article.summary.length > 160
            ? article.summary.slice(0, 160) + '…'
            : article.summary}
        </p>
      )}

      <div className="card-footer">
        {article.date_created && (
          <span className="card-date">{article.date_created}</span>
        )}
        {article.tags && article.tags.length > 0 && (
          <div className="card-tags">
            {article.tags.slice(0, 3).map(tag => (
              <span key={tag} className="tag">#{tag}</span>
            ))}
          </div>
        )}
      </div>

      {article.url && (
        <div
          className="card-url"
          onClick={e => {
            e.stopPropagation();
            window.open(article.url, '_blank', 'noopener,noreferrer');
          }}
          role="button"
          tabIndex={0}
          onKeyDown={e => e.key === 'Enter' && window.open(article.url, '_blank')}
          title={article.url}
        >
          <span className="url-icon">↗</span>
          <span className="url-text">{safeHostname(article.url)}</span>
        </div>
      )}
    </article>
  );
}
