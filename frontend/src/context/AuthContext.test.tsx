import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider, useAuth } from './AuthContext';
import { server } from '../test/server';
import { errorHandlers } from '../test/handlers';

// Test component that uses the auth context
const TestConsumer = () => {
  const { user, loading, login, logout } = useAuth();

  if (loading) {
    return <div data-testid="loading">Loading...</div>;
  }

  return (
    <div>
      {user ? (
        <>
          <div data-testid="user-name">{user.name}</div>
          <div data-testid="user-email">{user.email}</div>
          <button data-testid="logout-btn" onClick={logout}>
            Logout
          </button>
        </>
      ) : (
        <>
          <div data-testid="no-user">Not logged in</div>
          <button
            data-testid="login-btn"
            onClick={() => login('mock-credential')}
          >
            Login
          </button>
        </>
      )}
    </div>
  );
};

describe('AuthContext', () => {
  describe('Initial state', () => {
    it('should show loading state initially', () => {
      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      );

      expect(screen.getByTestId('loading')).toBeInTheDocument();
    });

    it('should load user on mount', async () => {
      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('user-name')).toHaveTextContent('Test User');
      });
    });

    it('should show user email after loading', async () => {
      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com');
      });
    });
  });

  describe('Authentication failed', () => {
    it('should show not logged in when auth fails', async () => {
      server.use(errorHandlers.authError);

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('no-user')).toBeInTheDocument();
      });
    });
  });

  describe('Login', () => {
    it('should login successfully', async () => {
      server.use(errorHandlers.authError); // Start logged out

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      );

      // Wait for initial auth check to complete
      await waitFor(() => {
        expect(screen.getByTestId('no-user')).toBeInTheDocument();
      });

      // Click login
      const user = userEvent.setup();
      await user.click(screen.getByTestId('login-btn'));

      // Should now show user
      await waitFor(() => {
        expect(screen.getByTestId('user-name')).toHaveTextContent('Test User');
      });
    });
  });

  describe('Logout', () => {
    it('should logout successfully', async () => {
      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      );

      // Wait for user to load
      await waitFor(() => {
        expect(screen.getByTestId('user-name')).toBeInTheDocument();
      });

      // Click logout
      const user = userEvent.setup();
      await user.click(screen.getByTestId('logout-btn'));

      // Should now show not logged in
      await waitFor(() => {
        expect(screen.getByTestId('no-user')).toBeInTheDocument();
      });
    });
  });

  describe('useAuth hook', () => {
    it('should provide default context when used outside provider', () => {
      // This tests that the default context values work
      const TestOutsideProvider = () => {
        const { user, loading } = useAuth();
        return (
          <div>
            <div data-testid="user-value">{user === null ? 'null' : 'exists'}</div>
            <div data-testid="loading-value">{loading ? 'true' : 'false'}</div>
          </div>
        );
      };

      render(<TestOutsideProvider />);

      expect(screen.getByTestId('user-value')).toHaveTextContent('null');
      expect(screen.getByTestId('loading-value')).toHaveTextContent('true');
    });
  });
});
