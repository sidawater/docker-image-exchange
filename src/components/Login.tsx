import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { setToken } from '../utils/auth';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const err = params.get('error');
    if (err) setError(decodeURIComponent(err));
  }, [location.search]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      const response = await fetch('/oauth/api/v1/oauth/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          grant_type: 'password',
          client_id: 'admin_ui',
          username,
          password,
        }),
      });

      const data: { access_token?: string; error_description?: string } =
        await response.json();

      if (response.ok && data.access_token) {
        setToken(data.access_token);
        const redirect =
          new URLSearchParams(location.search).get('redirect_uri') ||
          '/oauth/static/';
        window.location.href = redirect;
      } else {
        setError(data.error_description || '登录失败');
      }
    } catch {
      setError('网络错误，请稍后重试');
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-card">
          <h1>登录到系统</h1>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="username">用户名</label>
              <input
                type="text"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="password">密码</label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="login-button">
              登录
            </button>
          </form>
          {error && <div className="error-message">{error}</div>}
          <div className="login-footer">
            <p>使用您的 LDAP 凭证或本地账户登录</p>
          </div>
        </div>
      </div>
    </div>
  );
}