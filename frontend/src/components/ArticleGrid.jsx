import { useAppContext } from '../store/AppContext';
import ArticleCard from './ArticleCard';

function SkeletonCard() {
  return (
    <div className="article-card skeleton">
      <div className="skeleton-row">
        <div className="skeleton-block badge" />
        <div className="skeleton-block icon" />
      </div>
      <div className="skeleton-block title" />
      <div className="skeleton-block line" />
      <div className="skeleton-block line short" />
      <div className="skeleton-block footer" />
    </div>
  );
}

export default function ArticleGrid() {
  const { state } = useAppContext();

  const displayed =
    state.activeView === 'saved'
      ? state.articles.filter(a => state.savedFilenames.has(a.filename))
      : state.articles;

  if (state.loading) {
    return (
      <div className="articles-grid">
        {Array.from({ length: 9 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (!displayed.length) {
    return (
      <div className="empty-state">
        <span className="empty-icon">
          {state.activeView === 'saved' ? '⭐' : '📄'}
        </span>
        <p>
          {state.activeView === 'saved'
            ? 'No saved articles yet. Click the star on any article to save it.'
            : state.searchQuery
            ? `No articles match "${state.searchQuery}".`
            : 'No articles found. Run a web search above to scrape articles.'}
        </p>
      </div>
    );
  }

  return (
    <div className="articles-grid">
      {displayed.map((article, i) => (
        <ArticleCard key={article.filename} article={article} index={i} />
      ))}
    </div>
  );
}
