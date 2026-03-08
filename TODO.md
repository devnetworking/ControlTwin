# i18n lang module implementation plan

- [x] Create `controltwin-frontend/src/lang/fr.js` with full French translations.
- [x] Create `controltwin-frontend/src/lang/en.js` with full English translations (same keys).
- [x] Create `controltwin-frontend/src/store/langStore.js` using Zustand persist (`controltwin_lang`).
- [x] Create `controltwin-frontend/src/lang/index.js` exporting `useLang`.
- [x] Replace `controltwin-frontend/src/pages/SettingsPage.jsx` with language toggle + theme stub UI.
- [x] Update `controltwin-frontend/src/components/layout/Sidebar.jsx` to use `useLang` for nav labels.
- [x] Update `controltwin-frontend/src/pages/DashboardPage.jsx` visible text with `t(...)`.
- [x] Update `controltwin-frontend/src/pages/AlertsPage.jsx` visible text with `t(...)`.
- [x] Update `controltwin-frontend/src/pages/AssetsPage.jsx` visible text with `t(...)`.
- [x] Update `controltwin-frontend/src/pages/CollectorsPage.jsx` visible text with `t(...)`.
- [x] Update `controltwin-frontend/src/pages/UsersPage.jsx` visible text with `t(...)`.
- [x] Run frontend build validation.
- [ ] Extend lang coverage to all user-facing terms across all pages/components.
- [ ] Replace remaining hardcoded strings in shared components (TopBar, AlertTable, AlertDetailDrawer, TimeSeriesChart, AlertBarChart, others).
- [ ] Run frontend build validation after full coverage.
- [ ] Mark all tasks complete.

## Fix asset creation failure (/assets/new)

- [x] Inspect and normalize payload in `controltwin-frontend/src/pages/AssetCreatePage.jsx` (site_id UUID string, optional fields).
- [x] Improve API error rendering to display backend validation detail when available.
- [x] Run frontend validation (`npm run build`).
- [x] Mark this fix section complete.

## Fix Live Data Points empty in Asset detail

- [ ] Update `controltwin-frontend/src/pages/AssetDetailPage.jsx` to request timeseries with `data_point_ids` + `start/stop`.
- [ ] Add explicit empty state in Live Data Points section when no datapoints exist.
- [ ] Run frontend validation (`npm run build`).
- [ ] Mark this section complete.

## Add alerts bell mini dropdown in TopBar

- [ ] Update `controltwin-frontend/src/components/layout/TopBar.jsx` to open a mini dropdown on bell click.
- [ ] Show recent alerts with severity, title, and triggered_at.
- [ ] Add empty state and `Mark all read` action.
- [ ] Run frontend validation (`npm run build`).
- [ ] Mark this section complete.
