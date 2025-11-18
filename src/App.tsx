import React, { useEffect, useState } from 'react';
import './App.css';
import { api } from './api';
import { removeToken } from './utils/auth';
import Dashboard from './components/Dashboard';
import Users from './components/Users';
import Clients from './components/Clients';
import Sync from './components/Sync';
import Metrics from './components/Metrics';

type User = {
  id: string;
  username: string;
};

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [metrics, setMetrics] = useState<any>(null);
  const [users, setUsers] = useState<any[] | null>(null);
  const [clients, setClients] = useState<any[] | null>(null);
  const [syncStatus, setSyncStatus] = useState<any>(null);

  useEffect(() => {
    checkAuth();
    loadMetrics();
  }, []);

  useEffect(() => {
    loadTabData(activeTab);
  }, [activeTab]);

  const checkAuth = async () => {
    try {
      const me = await api.get<User>('/users/me');
      setUser(me);
    } catch (e) {
      window.location.href = '/oauth/static/login.html';
    }
  };

  const loadMetrics = async () => {
    try {
      const m = await api.get('/admin/metrics');
      setMetrics(m);
    } catch (e) {
    }
  };

  const loadTabData = async (tabName: string) => {
    try {
      switch (tabName) {
        case 'users': {
          const u = await api.get<any[]>('/users?limit=50');
          setUsers(u);
          break;
        }
        case 'clients': {
          const c = await api.get<any[]>('/clients');
          setClients(c);
          break;
        }
        case 'sync': {
          const s = await api.get('/admin/sync/status');
          setSyncStatus(s);
          break;
        }
        case 'metrics': {
          await loadMetrics();
          break;
        }
        default:
          break;
      }
    } catch (e) {
    }
  };

  const logout = () => {
    removeToken();
    window.location.href = '/oauth/static/login.html';
  };

  return (
    <div className="app-root">
      <header className="header">
        <h1>OAuth2 + LDAP 管理面板</h1>
        <div className="user-info">
          <span>{user ? user.username : '未登录'}</span>
          <button onClick={logout}>退出</button>
        </div>
      </header>

      <main className="main-layout">
        <nav className="sidebar">
          <ul>
            <li>
              <a href="#dashboard" onClick={(e) => { e.preventDefault(); setActiveTab('dashboard'); }}>仪表板</a>
            </li>
            <li>
              <a href="#users" onClick={(e) => { e.preventDefault(); setActiveTab('users'); }}>用户管理</a>
            </li>
            <li>
              <a href="#clients" onClick={(e) => { e.preventDefault(); setActiveTab('clients'); }}>客户端管理</a>
            </li>
            <li>
              <a href="#sync" onClick={(e) => { e.preventDefault(); setActiveTab('sync'); }}>LDAP 同步</a>
            </li>
            <li>
              <a href="#metrics" onClick={(e) => { e.preventDefault(); setActiveTab('metrics'); }}>系统指标</a>
            </li>
          </ul>
        </nav>

        <section className="content">
          {activeTab === 'dashboard' && <Dashboard metrics={metrics} />}
          {activeTab === 'users' && <Users users={users} />}
          {activeTab === 'clients' && <Clients clients={clients} />}
          {activeTab === 'sync' && <Sync status={syncStatus} />}
          {activeTab === 'metrics' && <Metrics metrics={metrics} />}
        </section>
      </main>
    </div>
  );
}

export default App;
