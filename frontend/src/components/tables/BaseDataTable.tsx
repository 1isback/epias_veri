'use client';
import React from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ModuleRegistry, AllCommunityModule, ColDef } from 'ag-grid-community';

ModuleRegistry.registerModules([AllCommunityModule]);

interface BaseDataTableProps<TData> {
  rowData: TData[];
  columnDefs: ColDef<TData>[];
}

export function BaseDataTable<TData>({ rowData, columnDefs }: BaseDataTableProps<TData>) {
  return (
    <div className="w-full h-[500px]">
      <AgGridReact<TData>
        modules={[AllCommunityModule]}
        rowData={rowData}
        columnDefs={columnDefs}
        pagination={true}
        paginationPageSize={20}
      />
    </div>
  );
}
