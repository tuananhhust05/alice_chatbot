import api from './client';
import { User } from '../types';

export const googleLogin = async (credential: string): Promise<User> => {
  const { data } = await api.post('/api/auth/google', { credential });
  return data;
};

export const getMe = async (): Promise<User> => {
  const { data } = await api.get('/api/auth/me');
  return data;
};

export const logout = async (): Promise<void> => {
  await api.post('/api/auth/logout');
};
