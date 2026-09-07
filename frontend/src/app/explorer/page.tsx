'use client';

import { ColDef } from 'ag-grid-community';
import { AxiosError } from 'axios';
import React, { FormEvent, useMemo, useState } from 'react';
import { Search, Star } from 'lucide-react';
import { AppShell } from '@/components/layout/AppShell';
import { Sidebar } from '@/components/layout/Sidebar';
import { PageHeader } from '@/components/layout/PageHeader';
import { ContentArea } from '@/components/layout/ContentArea';
import { BaseDataTable } from '@/components/tables/BaseDataTable';
import { WidgetContainer } from '@/components/widgets/WidgetContainer';
import { EmptyState } from '@/components/states/EmptyState';
import { ErrorState } from '@/components/states/ErrorState';
import { LoadingState } from '@/components/states/LoadingState';
import { downloadCsv } from '@/lib/utils';
import {
  useCatalogCategories,
  useCatalogDatasets,
  useDatasetDetail,
  useDatasetQuery,
  useLookup,
} from '@/modules/explorer';
import { DatasetSummary, ParamDef } from '@/modules/explorer/types';

const isoDay = (offsetDays: number) =>
  new Date(Date.now() - offsetDays * 86_400_000).toISOString().slice(0, 10);

function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const detail = (error.response?.data as { detail?: string } | undefined)?.detail;
    return detail || 'EPİAŞ isteği tamamlanamadı.';
  }
  return 'Beklenmeyen bir hata oluştu.';
}

function defaultValueFor(param: ParamDef): string {
  if (param.name === 'startDate') return isoDay(7);
  if (param.name === 'endDate') return isoDay(1);
  return '';
}

/** A <select> whose options come from an EPİAŞ lookup endpoint. */
function LookupField({
  param,
  value,
  onChange,
}: {
  param: ParamDef;
  value: string;
  onChange: (value: string) => void;
}) {
  const { data, isLoading, isError } = useLookup(param.lookup_id);
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      required={param.required}
      className="w-full rounded-md border border-border bg-secondary px-3 py-2 text-sm"
    >
      <option value="">
        {isLoading ? 'Yükleniyor…' : isError ? 'Liste alınamadı' : `${param.label} seçin`}
      </option>
      {data?.map((option) => (
        <option key={String(option.value)} value={String(option.value)}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

function ParamField({
  param,
  value,
  onChange,
}: {
  param: ParamDef;
  value: string;
  onChange: (value: string) => void;
}) {
  const base = 'w-full rounded-md border border-border bg-secondary px-3 py-2 text-sm';

  if (param.lookup_id) {
    return <LookupField param={param} value={value} onChange={onChange} />;
  }
  if (param.enum?.length) {
    return (
      <select value={value} onChange={(e) => onChange(e.target.value)} required={param.required} className={base}>
        <option value="">Seçin</option>
        {param.enum.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    );
  }
  if (param.format === 'date-time' || param.format === 'date') {
    return <input type="date" value={value} onChange={(e) => onChange(e.target.value)} required={param.required} className={base} />;
  }
  if (param.type === 'integer' || param.type === 'number') {
    return <input type="number" value={value} onChange={(e) => onChange(e.target.value)} required={param.required} className={base} />;
  }
  return <input type="text" value={value} onChange={(e) => onChange(e.target.value)} required={param.required} className={base} placeholder={param.description} />;
}

function DatasetButton({
  dataset,
  active,
  onSelect,
}: {
  dataset: Pick<DatasetSummary, 'id' | 'name'> & { featured?: boolean };
  active: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`flex w-full items-start gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors ${
        active ? 'bg-primary text-primary-foreground' : 'hover:bg-secondary'
      }`}
    >
      {dataset.featured && <Star size={14} className="mt-0.5 shrink-0" />}
      <span>{dataset.name}</span>
    </button>
  );
}

export default function ExplorerPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [openCategory, setOpenCategory] = useState<string | null>(null);
  const [form, setForm] = useState<{ id: string | null; values: Record<string, string> }>({
    id: null,
    values: {},
  });

  const categories = useCatalogCategories();
  const trimmedSearch = search.trim();
  const datasets = useCatalogDatasets(
    trimmedSearch
      ? { q: trimmedSearch }
      : openCategory
        ? { category: openCategory }
        : { featured: true },
  );
  const detail = useDatasetDetail(selectedId);
  const runQuery = useDatasetQuery(selectedId);

  // Seed the filter form with defaults when a different dataset loads. Adjusting
  // state during render (not in an effect) is the sanctioned pattern here.
  if (detail.data && form.id !== detail.data.id) {
    const values: Record<string, string> = {};
    for (const param of detail.data.params) values[param.name] = defaultValueFor(param);
    setForm({ id: detail.data.id, values });
  }
  const formValues = form.values;
  const setFormValues = (updater: (prev: Record<string, string>) => Record<string, string>) =>
    setForm((prev) => ({ ...prev, values: updater(prev.values) }));

  const selectDataset = (id: string) => {
    setSelectedId(id);
    runQuery.reset();
  };

  // Only show results that belong to the dataset currently in the form.
  const result = runQuery.data && form.id === selectedId ? runQuery.data : undefined;

  const columnDefs = useMemo<ColDef<Record<string, unknown>>[]>(
    () => (result?.columns ?? []).map((column) => ({ field: column.field, headerName: column.headerName })),
    [result?.columns],
  );

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!detail.data) return;
    const params: Record<string, string> = {};
    for (const [key, value] of Object.entries(formValues)) {
      if (value !== '') params[key] = value;
    }
    runQuery.mutate({ params });
  };

  const handleExport = () => {
    if (!result?.data.length) return;
    downloadCsv(`${detail.data?.id ?? 'epias'}_${new Date().toISOString().slice(0, 10)}.csv`, result.columns, result.data);
  };

  const featuredIds = new Set(categories.data?.featured.map((item) => item.id));

  return (
    <AppShell sidebar={<Sidebar />}>
      <PageHeader
        title="Veri Gezgini"
        description="EPİAŞ Şeffaflık Platformu'ndaki her veri setini seçip filtreleyerek çekin ve dışa aktarın."
      />
      <ContentArea>
        <div className="grid items-start gap-6 xl:grid-cols-[340px_1fr]">
          {/* ---------------------------------------------------------- dataset picker */}
          <WidgetContainer title="Veri setleri" className="max-h-[80vh] overflow-hidden">
            <div className="flex h-full flex-col">
              <div className="border-b border-border p-3">
                <div className="flex items-center gap-2 rounded-md border border-border bg-secondary px-3">
                  <Search size={15} className="text-muted-foreground" />
                  <input
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Veri seti ara…"
                    className="w-full bg-transparent py-2 text-sm focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-2">
                {trimmedSearch ? (
                  <>
                    {datasets.isLoading && <LoadingState message="Aranıyor…" />}
                    {datasets.data?.length === 0 && (
                      <p className="px-3 py-4 text-sm text-muted-foreground">Sonuç yok.</p>
                    )}
                    {datasets.data?.map((dataset) => (
                      <DatasetButton
                        key={dataset.id}
                        dataset={{ ...dataset, featured: featuredIds.has(dataset.id) }}
                        active={dataset.id === selectedId}
                        onSelect={() => selectDataset(dataset.id)}
                      />
                    ))}
                  </>
                ) : (
                  <>
                    <p className="px-3 pb-1 pt-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Öne çıkanlar
                    </p>
                    {categories.data?.featured.map((item) => (
                      <DatasetButton
                        key={item.id}
                        dataset={{ ...item, featured: true }}
                        active={item.id === selectedId}
                        onSelect={() => selectDataset(item.id)}
                      />
                    ))}

                    <p className="px-3 pb-1 pt-4 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Kategoriler
                    </p>
                    {categories.data?.categories.map((category) => (
                      <div key={category.id}>
                        <button
                          type="button"
                          onClick={() => setOpenCategory(openCategory === category.id ? null : category.id)}
                          className="flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm hover:bg-secondary"
                        >
                          <span>{category.label}</span>
                          <span className="text-xs text-muted-foreground">{category.dataset_count}</span>
                        </button>
                        {openCategory === category.id && (
                          <div className="ml-2 border-l border-border pl-2">
                            {datasets.isLoading && <LoadingState message="Yükleniyor…" />}
                            {datasets.data?.map((dataset) => (
                              <DatasetButton
                                key={dataset.id}
                                dataset={{ ...dataset, featured: featuredIds.has(dataset.id) }}
                                active={dataset.id === selectedId}
                                onSelect={() => selectDataset(dataset.id)}
                              />
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </>
                )}
              </div>
            </div>
          </WidgetContainer>

          {/* ---------------------------------------------------------- query + results */}
          <div className="space-y-6">
            {!selectedId && (
              <WidgetContainer title="Sorgu">
                <EmptyState title="Veri seti seçin" description="Soldan bir veri seti seçerek filtreleri belirleyin ve veriyi çekin." />
              </WidgetContainer>
            )}

            {selectedId && detail.isLoading && (
              <WidgetContainer title="Sorgu">
                <LoadingState message="Veri seti bilgisi yükleniyor…" />
              </WidgetContainer>
            )}

            {selectedId && detail.data && (
              <WidgetContainer title={detail.data.name}>
                <form className="space-y-4 p-5" onSubmit={handleSubmit}>
                  {detail.data.description && (
                    <p className="text-xs text-muted-foreground">{detail.data.description}</p>
                  )}
                  {detail.data.params.length === 0 && (
                    <p className="text-sm text-muted-foreground">Bu veri seti parametre almıyor.</p>
                  )}
                  <div className="grid gap-4 sm:grid-cols-2">
                    {detail.data.params.map((param) => (
                      <label key={param.name} className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        {param.label}
                        {param.required && <span className="text-danger"> *</span>}
                        <div className="mt-2">
                          <ParamField
                            param={param}
                            value={formValues[param.name] ?? ''}
                            onChange={(value) => setFormValues((prev) => ({ ...prev, [param.name]: value }))}
                          />
                        </div>
                      </label>
                    ))}
                  </div>
                  <button
                    type="submit"
                    disabled={runQuery.isPending}
                    className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                  >
                    {runQuery.isPending ? 'Çekiliyor…' : 'Sorgula'}
                  </button>
                  {runQuery.isError && (
                    <p className="text-xs text-danger">{getErrorMessage(runQuery.error)}</p>
                  )}
                </form>
              </WidgetContainer>
            )}

            {selectedId && detail.isError && (
              <ErrorState title="Veri seti yüklenemedi" message={getErrorMessage(detail.error)} onRetry={() => detail.refetch()} />
            )}

            {result && (
              <WidgetContainer
                title={`Sonuçlar · ${result.meta.total.toLocaleString('tr-TR')} kayıt`}
                className="min-h-[560px]"
              >
                <div className="flex items-center justify-between border-b border-border p-3">
                  <p className="text-xs text-muted-foreground">
                    {result.meta.intervals > 1 && `${result.meta.intervals} dönem birleştirildi · `}
                    {result.meta.truncated && (
                      <span className="text-warning">50.000 satır sınırına ulaşıldı, sonuç kırpıldı. </span>
                    )}
                  </p>
                  <button
                    type="button"
                    onClick={handleExport}
                    disabled={!result.data.length}
                    className="rounded-md bg-secondary px-3 py-1.5 text-xs font-semibold hover:bg-secondary/80 disabled:opacity-50"
                  >
                    CSV indir
                  </button>
                </div>
                {result.data.length === 0 ? (
                  <EmptyState title="Kayıt bulunamadı" description="Bu filtrelerle EPİAŞ boş sonuç döndürdü." />
                ) : (
                  <div className="p-4">
                    <BaseDataTable rowData={result.data} columnDefs={columnDefs} />
                  </div>
                )}
              </WidgetContainer>
            )}
          </div>
        </div>
      </ContentArea>
    </AppShell>
  );
}
