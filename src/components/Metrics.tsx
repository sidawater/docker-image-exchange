import React from 'react';

export default function Metrics({ metrics }: { metrics: any }) {
  return (
    <div data-tab="metrics" className="tab-content">
      <h2>系统指标</h2>
      {metrics ? (
        <pre>{JSON.stringify(metrics, null, 2)}</pre>
      ) : (
        <p>正在加载指标...</p>
      )}
    </div>
  );
}
