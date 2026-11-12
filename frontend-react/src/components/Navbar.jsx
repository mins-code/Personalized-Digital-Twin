import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const links = [
  { to: '/dashboard', label: 'Pulse' },
  { to: '/log',       label: 'Log Entry' },
  { to: '/quiz-check',label: 'Learn' },
  { to: '/simulator', label: 'Simulator' },
  { to: '/analytics', label: 'Analytics' },
];

export default function Navbar() {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <NavLink to="/" className="navbar-brand">CogniSync</NavLink>

        {isAuthenticated && (
          <nav className="navbar-links" style={{ flexWrap: 'wrap' }}>
            {links.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
              >
                {label}
              </NavLink>
            ))}
          </nav>
        )}

        <div className="flex gap-4 items-center">
          {isAuthenticated
            ? <button className="nav-logout" onClick={handleLogout}>Logout</button>
            : (
              <>
                <NavLink to="/login" className="nav-link">Sign In</NavLink>
                <NavLink to="/register" className="nav-link">Register</NavLink>
              </>
            )
          }
        </div>
      </div>
    </header>
  );
}

