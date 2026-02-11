import { describe, it, expect } from 'vitest';
import { googleLogin, getMe, logout } from './auth';

describe('Auth API', () => {
  describe('googleLogin', () => {
    it('should login with Google credential', async () => {
      const user = await googleLogin('mock-google-credential');

      expect(user).toHaveProperty('id');
      expect(user).toHaveProperty('email');
      expect(user).toHaveProperty('name');
      expect(user.email).toBe('test@example.com');
    });
  });

  describe('getMe', () => {
    it('should return current user', async () => {
      const user = await getMe();

      expect(user.id).toBe('user-123');
      expect(user.email).toBe('test@example.com');
      expect(user.name).toBe('Test User');
    });
  });

  describe('logout', () => {
    it('should logout successfully', async () => {
      await expect(logout()).resolves.toBeUndefined();
    });
  });
});
