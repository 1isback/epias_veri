export interface LoginCredentials {
  email: string;
  password?: string;
}

export interface RegisterCredentials {
  first_name: string;
  last_name: string;
  email: string;
  password?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    is_admin: boolean;
  };
}

export interface PendingUser {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  created_at: string;
}

export interface IAuthService {
  login(credentials: LoginCredentials): Promise<AuthResponse>;
  register(credentials: RegisterCredentials): Promise<{ msg: string }>;
  logout(): Promise<void>;
  verifyToken(): Promise<boolean>;
  getPendingUsers(): Promise<PendingUser[]>;
  approveUser(userId: string): Promise<{ msg: string }>;
}
