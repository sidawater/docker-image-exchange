import React from 'react';

export default function Clients({ clients }: { clients: any[] | null }) {
  return (
    <div data-tab="clients" className="tab-content">
      <h2>客户端管理</h2>
      {clients ? (
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>名称</th>
            </tr>
          </thead>
          <tbody>
            {clients.map((c) => (
              <tr key={c.id || c.client_id}>
                <td>{c.id || c.client_id}</td>
                <td>{c.name || c.client_name}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>正在加载客户端列表...</p>
      )}
    </div>
  );
}
