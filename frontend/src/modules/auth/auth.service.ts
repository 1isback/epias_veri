import { apiClient } from '@/lib/api-client/apiClient';
import { IAuthService, LoginCredentials, RegisterCredentials, AuthResponse, PendingUser } from './types';

class AuthService implements IAuthService {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiClient.post<unknown, AuthResponse>('/auth/login', credentials);
    return response;
  }

  async register(credentials: RegisterCredentials): Promise<{ msg: string }> {
    const response = await apiClient.post<unknown, { msg: string }>('/auth/register', credentials);
    return response;
  }

  async logout(): Promise<void> {
    // Client side logout will just clear tokens.
  }

  async verifyToken(): Promise<boolean> {
    try {
      await apiClient.get('/auth/me');
      return true;
    } catch {
      return false;
    }
  }
  
  async getPendingUsers(): Promise<PendingUser[]> {
    const response = await apiClient.get<unknown, PendingUser[]>('/users/pending');
    return response;
  }
  
  async approveUser(userId: string): Promise<{ msg: string }> {
    const response = await apiClient.post<unknown, { msg: string }>(`/users/${userId}/approve`);
    return response;
  }
}

export const authService = new AuthService();
