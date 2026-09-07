'use client';
import React, { useState } from 'react';
import Link from 'next/link';
import { useMutation } from '@tanstack/react-query';
import { authService } from '@/modules/auth/auth.service';
import { RegisterCredentials } from '@/modules/auth/types';

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: ''
  });
  const [successMsg, setSuccessMsg] = useState('');

  const { mutate: register, isPending, isError, error } = useMutation<
    { msg: string }, Error, RegisterCredentials
  >({
    mutationFn: (credentials) => authService.register(credentials),
    onSuccess: (data) => {
      setSuccessMsg(data.msg);
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMsg('');
    register(formData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="flex h-screen w-full items-center justify-center bg-background">
      <div className="w-full max-w-md p-8 bg-card border border-border rounded-xl shadow-lg">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Request Access</h1>
          <p className="text-sm text-muted-foreground mt-2">Sign up for Energy Intelligence</p>
        </div>
        
        {successMsg ? (
          <div className="space-y-6">
            <div className="p-4 text-sm text-emerald-800 bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400 rounded-md text-center">
              {successMsg}
            </div>
            <Link 
              href="/login"
              className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none bg-[var(--color-primary)] text-white hover:opacity-90 h-10 px-4 py-2 w-full"
            >
              Return to Sign In
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">First Name</label>
                <input 
                  type="text" 
                  name="first_name"
                  placeholder="John" 
                  value={formData.first_name}
                  onChange={handleChange}
                  required
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Last Name</label>
                <input 
                  type="text" 
                  name="last_name"
                  placeholder="Doe" 
                  value={formData.last_name}
                  onChange={handleChange}
                  required
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Work Email</label>
              <input 
                type="email" 
                name="email"
                placeholder="user@epias.com.tr" 
                value={formData.email}
                onChange={handleChange}
                required
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]"
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Password</label>
              <input 
                type="password" 
                name="password"
                placeholder="••••••••" 
                value={formData.password}
                onChange={handleChange}
                required
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]"
              />
            </div>

            {isError && (
              <div className="p-3 text-sm text-white bg-[var(--color-danger)] rounded-md">
                {(error as any)?.response?.data?.detail || "An error occurred during registration."}
              </div>
            )}

            <button 
              type="submit" 
              disabled={isPending} 
              className="mt-2 inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none bg-[var(--color-primary)] text-white hover:opacity-90 h-10 px-4 py-2 w-full disabled:opacity-50"
            >
              {isPending ? 'Submitting...' : 'Sign Up'}
            </button>
          </form>
        )}

        <div className="mt-6 text-center text-sm text-muted-foreground">
          Already have an account? <Link href="/login" className="text-[var(--color-primary)] hover:underline font-medium">Sign In</Link>
        </div>
      </div>
    </div>
  );
}
