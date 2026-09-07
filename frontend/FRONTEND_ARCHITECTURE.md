# Enterprise Frontend Architecture

This document describes the foundational architectural principles, module layout, and strict conventions utilized across the project. 

## Architectural Philosophy

The frontend architecture strictly enforces domain-driven design, unidirectional data flows, and comprehensive encapsulation.
- **Components are presentational**: No API logic or data-fetching logic is allowed directly inside React UI components.
- **Zero Mock Data in Production**: All mock data is isolated under `src/test/mocks` and is excluded from production builds.
- **100% Type Safe**: The usage of `any`, `@ts-ignore`, or `unsafe` casts is explicitly forbidden.

## Directory Structure

```text
src/
├── app/                  # Next.js App Router Pages & Layouts
├── components/           # Shared, presentational, generic components
│   ├── badges/           # Reusable status/trend badges
│   ├── cards/            # Reusable KPI and Metric cards
│   ├── charts/           # Generic Recharts wrappers
│   ├── layout/           # AppShell, ContentArea
│   ├── states/           # Loading, Error, and Empty generic states
│   └── tables/           # BaseDataTable wrapping AG Grid
├── config/               # Global constants (routes, timeouts)
├── lib/                  # Infrastructure logic
│   └── api-client/       # Centralized Axios instance with auth interceptors
├── modules/              # Domain-Driven Modules
│   ├── auth/             # Authentication & session state
│   ├── company/          # Entity profiles, assets, production data
│   ├── dashboard/        # Multi-domain aggregations
│   └── explorer/         # AG Grid dynamic data views
└── test/
    └── mocks/            # Isolated mock datasets for unit/e2e testing
```

## Data Flow Pipeline

Every asynchronous request must follow this unidirectional flow:

1. **React Component**: Defines the UI and passes arguments (e.g., `companyId`).
2. **TanStack Query Hook**: Located in `src/modules/[domain]/hooks/`. Manages caching, retries, loading states, and duplicate-request deduplication.
3. **Service Interface & Implementation**: Located in `src/modules/[domain]/[domain].service.ts`. Abstracts HTTP logic and binds strictly typed Request/Response DTOs.
4. **API Client**: `apiClient.ts` globally injects the Bearer token and handles 401/403 redirects seamlessly.

## Key Design Decisions

- **Dynamic Data Grids**: The `BaseDataTable` component acts as a generic `<TData>` wrapper around AG Grid. Columns are dynamically parsed from the backend's metadata payload, completely decoupling the frontend from schema updates.
- **Component States**: Skeletons, Errors, and Empty conditions are standardized across the application via `<LoadingState>`, `<ErrorState>`, and `<EmptyState>`.
- **Dynamic Routing**: Entities like `Company` are resolved dynamically via Next.js routing parameters (e.g., `/company/[id]`), enabling massive scalability without frontend redeployments.

## Future Readiness
This architecture natively supports upcoming features:
- **Alert Center / Monitoring**: By replacing HTTP endpoints in the Service layer with WebSocket connections, real-time data will flow naturally into the existing TanStack hooks.
- **Custom Dashboards**: `WidgetRow` and `WidgetColumn` are designed to be replaced by JSON-driven layout engines (e.g., `react-grid-layout`) without altering the underlying data components.
