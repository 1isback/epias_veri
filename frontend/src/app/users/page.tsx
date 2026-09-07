'use client';
import React, { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/useAuthStore';
import { useRouter } from 'next/navigation';
import { authService } from '@/modules/auth/auth.service';
import { PendingUser } from '@/modules/auth/types';
import { AppShell } from '@/components/layout/AppShell';
import { Sidebar } from '@/components/layout/Sidebar';
import { PageHeader } from '@/components/layout/PageHeader';
import { ContentArea } from '@/components/layout/ContentArea';
import Link from 'next/link';

export default function UsersPage() {
  const user = useAuthStore((state) => state.user);
  const router = useRouter();
  const [pendingUsers, setPendingUsers] = useState<PendingUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }
    
    if (!user.is_admin) {
      router.push('/dashboard');
      return;
    }

    fetchPendingUsers();
  }, [user, router]);

  const fetchPendingUsers = async () => {
    try {
      setIsLoading(true);
      const users = await authService.getPendingUsers();
      setPendingUsers(users);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to fetch pending users.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async (userId: string) => {
    try {
      await authService.approveUser(userId);
      setPendingUsers(pendingUsers.filter(u => u.id !== userId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to approve user.');
    }
  };

  if (!user || !user.is_admin) {
    return null;
  }

  return (
    <AppShell sidebar={<Sidebar />}>
      <PageHeader 
        title="Pending Approvals" 
        description="Approve new user accounts to grant them access to the platform."
      >
        <Link href="/dashboard" className="px-4 py-2 bg-secondary text-secondary-foreground font-semibold text-sm rounded-md border border-border hover:bg-secondary/80 transition-colors">
          Back to Dashboard
        </Link>
      </PageHeader>
      
      <ContentArea>
        <div className="max-w-4xl mx-auto py-8">
          {isLoading ? (
            <div className="text-center text-muted-foreground p-12">Loading...</div>
          ) : errorMsg ? (
            <div className="p-4 bg-danger/10 text-danger rounded-md">{errorMsg}</div>
          ) : pendingUsers.length === 0 ? (
            <div className="text-center p-12 bg-card border border-border rounded-lg shadow-sm">
              <h3 className="text-lg font-medium text-foreground mb-2">No pending approvals</h3>
              <p className="text-muted-foreground">All registered users have been approved.</p>
            </div>
          ) : (
            <div className="bg-card border border-border rounded-lg shadow-sm overflow-hidden">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-muted/50 border-b border-border">
                    <th className="p-4 font-medium text-foreground text-sm">Name</th>
                    <th className="p-4 font-medium text-foreground text-sm">Email</th>
                    <th className="p-4 font-medium text-foreground text-sm">Registration Date</th>
                    <th className="p-4 font-medium text-foreground text-sm text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {pendingUsers.map(u => (
                    <tr key={u.id} className="hover:bg-muted/20 transition-colors">
                      <td className="p-4 text-sm font-medium text-foreground">{u.first_name} {u.last_name}</td>
                      <td className="p-4 text-sm text-muted-foreground">{u.email}</td>
                      <td className="p-4 text-sm text-muted-foreground">{new Date(u.created_at).toLocaleDateString()}</td>
                      <td className="p-4 text-right">
                        <button 
                          onClick={() => handleApprove(u.id)}
                          className="px-3 py-1.5 bg-emerald-600 text-white font-medium text-xs rounded-md hover:bg-emerald-700 transition-colors"
                        >
                          Approve
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </ContentArea>
    </AppShell>
  );
}
