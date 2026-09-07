'use client';

import { ColDef } from 'ag-grid-community';
import { AxiosError } from 'axios';
import React, { FormEvent, useMemo, useState } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { Sidebar } from '@/components/layout/Sidebar';
import { ContentArea } from '@/components/layout/ContentArea';
import { PageHeader } from '@/components/layout/PageHeader';
import { EmptyState } from '@/components/states/EmptyState';
import { ErrorState } from '@/components/states/ErrorState';
import { LoadingState } from '@/components/states/LoadingState';
import { BaseDataTable } from '@/components/tables/BaseDataTable';
import { WidgetContainer } from '@/components/widgets/WidgetContainer';
import {
  useInjectionQuantityPowerplants,
  useInjectionQuantityRecords,
  useSyncInjectionQuantity,
  useSyncInjectionQuantityPowerplants,
} from '@/modules/injection-quantity';
import { InjectionQuantityRecord } from '@/modules/injection-quantity/types';

const today = new Date().toISOString().slice(0, 10);
const monthStart = `${today.slice(0, 8)}01`;

function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const detail = error.response?.data as { detail?: string } | undefined;
    return detail?.detail || 'EPİAŞ isteği tamamlanamadı.';
  }
  return 'Beklenmeyen bir hata oluştu.';
}

export default function InjectionQuantityPage() {
  const [search, setSearch] = useState('');
  const [powerplantId, setPowerplantId] = useState<number | null>(null);
  const [startDate, setStartDate] = useState(monthStart);
  const [endDate, setEndDate] = useState(today);
  const [forceRefresh, setForceRefresh] = useState(false);
  const powerplants = useInjectionQuantityPowerplants(search);
  const records = useInjectionQuantityRecords({ powerplantId, startDate, endDate });
  const syncPowerplants = useSyncInjectionQuantityPowerplants();
  const sync = useSyncInjectionQuantity();

  const columns = useMemo<ColDef<InjectionQuantityRecord>[]>(() => [
    { field: 'date', headerName: 'Tarih', flex: 1, valueFormatter: ({ value }) => String(value).slice(0, 10) },
    { field: 'hour', headerName: 'Saat', width: 110 },
    { field: 'total', headerName: 'UEVM (MWh)', flex: 1, valueFormatter: ({ value }) => value === null ? '-' : Number(value).toLocaleString('tr-TR', { maximumFractionDigits: 3 }) },
  ], []);

  const handleSync = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (powerplantId === null || startDate > endDate) return;
    sync.mutate({ powerplant_id: powerplantId, start_date: startDate, end_date: endDate, force_refresh: forceRefresh });
  };

  return (
    <AppShell sidebar={<Sidebar />}>
      <PageHeader title="UEVM Veri Merkezi" description="Santral seçerek saatlik Uzlaştırma Esas Veriş Miktarı verilerini EPİAŞ’tan çekin ve inceleyin." />
      <ContentArea>
        <div className="grid gap-6 xl:grid-cols-[360px_1fr]">
          <WidgetContainer title="Sorgu ve senkronizasyon">
            <form className="space-y-5 p-5" onSubmit={handleSync}>
              <button type="button" onClick={() => syncPowerplants.mutate()} disabled={syncPowerplants.isPending} className="w-full rounded-md border border-border bg-secondary px-4 py-2 text-sm font-semibold hover:bg-secondary/80 disabled:opacity-50">
                {syncPowerplants.isPending ? 'Santraller alınıyor...' : 'EPİAŞ santral listesini yenile'}
              </button>
              <div>
                <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-muted-foreground">Santral ara</label>
                <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Santral adı veya kısa adı" className="w-full rounded-md border border-border bg-secondary px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-muted-foreground">Santral</label>
                <select value={powerplantId ?? ''} onChange={(event) => setPowerplantId(event.target.value ? Number(event.target.value) : null)} className="w-full rounded-md border border-border bg-secondary px-3 py-2 text-sm" required>
                  <option value="">Santral seçin</option>
                  {powerplants.data?.map((plant) => <option key={plant.epias_powerplant_id} value={plant.epias_powerplant_id}>{plant.name || plant.short_name || plant.epias_powerplant_id} ({plant.epias_powerplant_id})</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Başlangıç<input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} className="mt-2 w-full rounded-md border border-border bg-secondary px-3 py-2 text-sm" required /></label>
                <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Bitiş<input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} className="mt-2 w-full rounded-md border border-border bg-secondary px-3 py-2 text-sm" required /></label>
              </div>
              <label className="flex items-center gap-2 text-sm text-muted-foreground"><input type="checkbox" checked={forceRefresh} onChange={(event) => setForceRefresh(event.target.checked)} /> Tüm aralığı tekrar çek</label>
              <button type="submit" disabled={sync.isPending || powerplantId === null || startDate > endDate} className="w-full rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-50">{sync.isPending ? 'UEVM verisi çekiliyor...' : 'UEVM verisini çek ve kaydet'}</button>
              {startDate > endDate && <p className="text-xs text-danger">Başlangıç tarihi bitişten büyük olamaz.</p>}
              {sync.isError && <p className="text-xs text-danger">{getErrorMessage(sync.error)}</p>}
              {sync.data && <div className="rounded-md border border-success/40 bg-success/10 p-3 text-xs"><p className="font-semibold">Senkronizasyon tamamlandı</p><p>{sync.data.chunk_count} parça · {sync.data.fetched_record_count} kayıt · {sync.data.inserted_record_count} yeni · {sync.data.updated_record_count} güncel</p></div>}
            </form>
          </WidgetContainer>
          <WidgetContainer title="Saatlik UEVM kayıtları" className="min-h-[620px]">
            {records.isLoading && <LoadingState message="Kayıtlar yükleniyor..." />}
            {records.isError && <ErrorState title="UEVM kayıtları yüklenemedi" message={getErrorMessage(records.error)} onRetry={() => records.refetch()} />}
            {!records.isLoading && !records.isError && !powerplantId && <EmptyState title="Santral seçin" description="Kayıtlı UEVM verilerini görmek veya yeni veri çekmek için bir santral seçin." />}
            {!records.isLoading && !records.isError && powerplantId && records.data?.items.length === 0 && <EmptyState title="Kayıt bulunamadı" description="Bu tarih aralığı için önce UEVM verisini çekin." />}
            {!records.isLoading && !records.isError && records.data && records.data.items.length > 0 && <div className="p-4"><p className="mb-3 text-xs text-muted-foreground">{records.data.total} kayıt</p><BaseDataTable rowData={records.data.items} columnDefs={columns} /></div>}
          </WidgetContainer>
        </div>
      </ContentArea>
    </AppShell>
  );
}
