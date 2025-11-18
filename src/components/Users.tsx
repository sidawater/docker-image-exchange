import React from 'react';

export default function Users({ users }: { users: any[] | null }) {
  return (
    <div data-tab="users" className="tab-content">
      <h2>用户管理</h2>
      {users ? (
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>用户名</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.id}</td>
                <td>{u.username || u.name || u.email}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>正在加载用户列表...</p>
      )}
    </div>
  );
}
