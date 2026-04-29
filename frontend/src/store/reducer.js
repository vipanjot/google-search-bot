export const initialState = {
  articles: [],
  savedFilenames: new Set(),
  activeArticle: null,
  articleLoading: false,
  searchQuery: '',
  filterType: '',
  activeView: 'all',
  loading: false,
  searchRunning: false,
  searchMessage: '',
};

export function reducer(state, action) {
  switch (action.type) {
    case 'SET_ARTICLES':
      return { ...state, articles: action.payload };

    case 'SET_SAVED':
      return { ...state, savedFilenames: new Set(action.payload) };

    case 'TOGGLE_SAVED': {
      const next = new Set(state.savedFilenames);
      if (next.has(action.payload)) next.delete(action.payload);
      else next.add(action.payload);
      return { ...state, savedFilenames: next };
    }

    case 'SET_ACTIVE_ARTICLE':
      return { ...state, activeArticle: action.payload };

    case 'CLEAR_ACTIVE_ARTICLE':
      return { ...state, activeArticle: null, articleLoading: false };

    case 'SET_ARTICLE_LOADING':
      return { ...state, articleLoading: action.payload };

    case 'SET_SEARCH_QUERY':
      return { ...state, searchQuery: action.payload };

    case 'SET_FILTER_TYPE':
      return { ...state, filterType: action.payload };

    case 'SET_VIEW':
      return { ...state, activeView: action.payload };

    case 'SET_LOADING':
      return { ...state, loading: action.payload };

    case 'SET_SEARCH_RUNNING':
      return { ...state, searchRunning: action.payload };

    case 'SET_SEARCH_MESSAGE':
      return { ...state, searchMessage: action.payload };

    default:
      return state;
  }
}
