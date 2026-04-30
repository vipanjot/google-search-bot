import { useEffect, useState } from 'react';
import { useAppContext } from '../context/AppContext';

export default function StatusToast() {
  const { state } = useAppContext();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!state.searchMessage) return;
    setVisible(true);
    if (!state.searchRunning) {
      const t = setTimeout(() => setVisible(false), 3500);
      return () => clearTimeout(t);
    }
  }, [state.searchMessage, state.searchRunning]);

  if (!state.searchMessage) return null;

  return (
    <div
      className={`status-toast ${visible ? 'visible' : ''} ${state.searchRunning ? 'running' : 'done'}`}
      role="status"
      aria-live="polite"
    >
      {state.searchRunning ? (
        <span className="spinner-small" />
      ) : (
        <span className="toast-check">✓</span>
      )}
      <span className="toast-message">{state.searchMessage}</span>
    </div>
  );
}
