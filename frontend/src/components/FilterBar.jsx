import { useAppContext } from '../context/AppContext';

const TYPES = [
  { value: '', label: 'All Types' },
  { value: 'concept', label: 'Concept' },
  { value: 'source', label: 'Source' },
  { value: 'synthesis', label: 'Synthesis' },
];

export default function FilterBar() {
  const { state, dispatch } = useAppContext();

  return (
    <div className="filter-bar">
      {TYPES.map(t => (
        <button
          key={t.value}
          className={`filter-chip ${state.filterType === t.value ? 'active' : ''}`}
          onClick={() => dispatch({ type: 'SET_FILTER_TYPE', payload: t.value })}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
