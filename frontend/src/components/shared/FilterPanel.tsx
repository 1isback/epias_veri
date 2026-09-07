'use client';
import React from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useFilterStore } from '@/store/useFilterStore';

const filterSchema = z.object({
  startDate: z.string().min(1, "Start date is required"),
  endDate: z.string().min(1, "End date is required"),
  datasets: z.array(z.string()).optional(),
});

type FilterValues = z.infer<typeof filterSchema>;

export function FilterPanel() {
  const setDateRange = useFilterStore((state) => state.setDateRange);
  
  const { register, handleSubmit, formState: { errors } } = useForm<FilterValues>({
    resolver: zodResolver(filterSchema),
    defaultValues: {
      startDate: '',
      endDate: '',
      datasets: []
    }
  });

  const onSubmit = (data: FilterValues) => {
    setDateRange(data.startDate, data.endDate);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex gap-4 p-4 border rounded bg-white">
      <div>
        <label className="block text-sm">Start Date</label>
        <input type="date" {...register('startDate')} className="border rounded px-2 py-1" />
        {errors.startDate && <p className="text-red-500 text-xs">{errors.startDate.message}</p>}
      </div>
      <div>
        <label className="block text-sm">End Date</label>
        <input type="date" {...register('endDate')} className="border rounded px-2 py-1" />
        {errors.endDate && <p className="text-red-500 text-xs">{errors.endDate.message}</p>}
      </div>
      <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">
        Apply Filters
      </button>
    </form>
  );
}
