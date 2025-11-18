import React from 'react';

export default function Dashboard({ metrics }: { metrics: any }) {
  return (
    <div data-tab="dashboard" className="tab-content">
      <h2>系统概览</h2>
      {metrics ? (
        <div className="stats-grid">
          <pre>{JSON.stringify(metrics, null, 2)}</pre>
        </div>
      ) : (
        <p>正在加载指标...</p>
      )}
    </div>
  );
}
