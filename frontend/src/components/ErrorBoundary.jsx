import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary caught error]:', error, errorInfo);
    this.setState({ errorInfo });
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return typeof this.props.fallback === 'function'
          ? this.props.fallback(this.state.error, this.handleReset)
          : this.props.fallback;
      }

      return (
        <div style={{
          padding: '1.5rem',
          margin: '1rem 0',
          borderRadius: '8px',
          border: '1px solid var(--danger-border, #fca5a5)',
          backgroundColor: 'var(--danger-bg, #fef2f2)',
          color: 'var(--danger-text, #991b1b)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.75rem' }}>
            <AlertTriangle size={22} color="#dc2626" />
            <h4 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700 }}>
              {this.props.title || 'Component Error Encountered'}
            </h4>
          </div>
          <p style={{ margin: '0 0 1rem 0', fontSize: '0.88rem', lineHeight: 1.5, color: 'var(--text-primary, #374151)' }}>
            {this.props.message || 'An unexpected rendering error occurred in this view. Navigation and other dashboard features remain operational.'}
          </p>
          {this.state.error && (
            <div style={{
              background: 'rgba(0,0,0,0.04)',
              padding: '0.5rem 0.75rem',
              borderRadius: '4px',
              fontSize: '0.78rem',
              fontFamily: 'monospace',
              marginBottom: '1rem',
              wordBreak: 'break-all'
            }}>
              {this.state.error.message || String(this.state.error)}
            </div>
          )}
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button
              onClick={this.handleReset}
              className="btn btn-primary"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.5rem 1rem',
                fontSize: '0.85rem',
                cursor: 'pointer'
              }}
            >
              <RefreshCw size={14} /> Retry View
            </button>
            {this.props.onDismiss && (
              <button
                onClick={this.props.onDismiss}
                className="btn btn-outline"
                style={{ padding: '0.5rem 1rem', fontSize: '0.85rem', cursor: 'pointer' }}
              >
                Dismiss
              </button>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
