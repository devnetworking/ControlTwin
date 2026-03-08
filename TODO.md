# TODO - Dockeriser le frontend + gestion des sites

- [x] Créer `controltwin-frontend/Dockerfile` (build Vite + serve Nginx)
- [x] Créer `controltwin-frontend/.dockerignore`
- [x] Créer `controltwin-frontend/nginx.conf` (SPA fallback + proxy /api)
- [x] Ajouter un service frontend dans un fichier compose racine
- [x] Verrouiller `VITE_API_BASE_URL` en build Docker (`/api/v1`)
- [x] Diagnostiquer le 500 backend sur création site (mismatch type `sector`)
- [x] Ajouter migration backend de correction type `sites.sector`
- [x] Aligner modèle SQLAlchemy `Site.sector`

## Nouvelles tâches demandées (sites)
- [x] Backend: ajouter `SiteUpdate` schema
- [x] Backend: endpoint `PATCH /sites/{site_id}` (update infos)
- [x] Backend: endpoint `POST /sites/{site_id}/activate`
- [x] Backend: endpoint `POST /sites/{site_id}/deactivate`
- [x] Backend: endpoint `DELETE /sites/{site_id}` (soft delete)
- [x] Frontend API: ajouter `updateSite`, `activateSite`, `deactivateSite`, `deleteSite`
- [x] Frontend UI `SitesPage`: actions modifier/activer/désactiver/supprimer
- [x] Tester flux API/UI et rapporter couverture restante

## Nouvelles tâches demandées (users)
- [ ] Backend: ajouter `UserUpdate` schema
- [ ] Backend: endpoint `GET /users` (liste)
- [ ] Backend: endpoint `PATCH /users/{user_id}` (update)
- [ ] Backend: endpoint `POST /users/{user_id}/activate`
- [ ] Backend: endpoint `POST /users/{user_id}/deactivate`
- [ ] Backend: endpoint `DELETE /users/{user_id}`
- [ ] Frontend API: créer `src/api/users.js` (list/update/activate/deactivate/delete)
- [ ] Frontend UI `UsersPage`: actions update/delete/activate-disable
- [ ] Tester flux API/UI users et rapporter couverture restante
