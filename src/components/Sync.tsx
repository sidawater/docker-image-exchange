import React from 'react';

export default function Sync({ status }: { status: any }) {
  return (
    <div data-tab="sync" className="tab-content">
      <h2>LDAP 同步状态</h2>
      {status ? (
        <pre>{JSON.stringify(status, null, 2)}</pre>
      ) : (
        <p>正在加载同步状态...</p>
      )}
    </div>
  );
}
