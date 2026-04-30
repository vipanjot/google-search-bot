import { useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useAppContext } from '../context/AppContext';
import { saveArticle, unsaveArticle } from '../services/client';

function stripWikilinks(text) {
  return text.replace(/\[\[([^\]]+)\]\]/g, '$1');
}

export default function ArticleModal() {
  const { state, dispatch } = useAppContext();
  const { activeArticle, articleLoading, savedFilenames } = state;

  const isOpen = activeArticle !== null || articleLoading;
  const isSaved = activeArticle ? savedFilenames.has(activeArticle.filename) : false;

  const close = useCallback(() => {
    dispatch({ type: 'CLEAR_ACTIVE_ARTICLE' });
  }, [dispatch]);

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e) => { if (e.key === 'Escape') close(); };
    document.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [isOpen, close]);

  const handleSaveToggle = async () => {
    if (!activeArticle) return;
    dispatch({ type: 'TOGGLE_SAVED', payload: activeArticle.filename });
    try {
      if (isSaved) await unsaveArticle(activeArticle.filename);
      else await saveArticle(activeArticle.filename);
    } catch {
      dispatch({ type: 'TOGGLE_SAVED', payload: activeArticle.filename });
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className={`modal-overlay ${isOpen ? 'active' : ''}`}
      onClick={close}
      role="dialog"
      aria-modal="true"
    >
      <div className="modal-container" onClick={e => e.stopPropagation()}>
        {articleLoading && !activeArticle ? (
          <div className="modal-loading">
            <div className="spinner" />
          </div>
        ) : (
          <>
            <div className="modal-header">
              <div className="modal-header-meta">
                {activeArticle?.meta?.type && (
                  <span className={`type-badge type-${activeArticle.meta.type}`}>
                    {activeArticle.meta.type}
                  </span>
                )}
                {activeArticle?.meta?.date_created && (
                  <span className="modal-date">{activeArticle.meta.date_created}</span>
                )}
              </div>
              <div className="modal-header-actions">
                <button
                  className={`modal-save-btn ${isSaved ? 'saved' : ''}`}
                  onClick={handleSaveToggle}
                >
                  {isSaved ? '★ Saved' : '☆ Save'}
                </button>
                {activeArticle?.url && (
                  <a
                    href={activeArticle.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="modal-source-btn"
                    onClick={e => e.stopPropagation()}
                  >
                    ↗ Source
                  </a>
                )}
                <button className="modal-close" onClick={close} aria-label="Close">
                  ✕
                </button>
              </div>
            </div>

            <h2 className="modal-title">{activeArticle?.title}</h2>

            <div className="modal-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {stripWikilinks(activeArticle?.body || '')}
              </ReactMarkdown>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
