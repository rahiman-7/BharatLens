import { apiClient } from '../api/client';
import type { User, AuthResponse, LoginCredentials, RegisterCredentials } from './authTypes';


export async function loginApi(credentials: LoginCredentials): Promise<AuthResponse> {
  return apiClient<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(credentials),
  });
}

export async function registerApi(credentials: RegisterCredentials): Promise<User> {
  return apiClient<User>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(credentials),
  });
}

export async function getMeApi(): Promise<User> {
  return apiClient<User>('/auth/me');
}
