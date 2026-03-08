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
