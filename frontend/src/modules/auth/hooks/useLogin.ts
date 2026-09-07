import { useMutation } from '@tanstack/react-query';
import { authService } from '../auth.service';
import { LoginCredentials, AuthResponse } from '../types';
import { useAuthStore } from '@/store/useAuthStore';
import { useRouter } from 'next/navigation';

export function useLogin() {
  const setToken = useAuthStore((state) => state.setToken);
  const setUser = useAuthStore((state) => state.setUser);
  const router = useRouter();

  return useMutation<AuthResponse, Error, LoginCredentials>({
    mutationFn: (credentials) => authService.login(credentials),
    onSuccess: (data) => {
      // Save token and navigate
      setToken(data.access_token);
      setUser(data.user);
      
      // We also need to set it in cookies so middleware can see it
      document.cookie = `token=${data.access_token}; path=/; max-age=86400; samesite=lax`;
      
      router.push('/dashboard');
    },
  });
}
