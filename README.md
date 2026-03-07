# ControlTwin ICS Platform

<p align="center">
  <strong>Plateforme moderne de supervision, sécurité et jumeau numérique pour environnements ICS/OT.</strong><br/>
  Frontend React • Backend FastAPI • Services IA avancés
</p>

<p align="center">
  <img alt="Frontend" src="https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB?logo=react&logoColor=white">
  <img alt="Backend" src="https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white">
  <img alt="Database" src="https://img.shields.io/badge/Database-PostgreSQL-336791?logo=postgresql&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/License-Internal-blue">
</p>

---

## Sommaire

- [1. Présentation](#1-présentation)
- [2. Architecture](#2-architecture)
- [3. Stack technique](#3-stack-technique)
- [4. Démarrage rapide](#4-démarrage-rapide)
- [5. Comptes par défaut (développement)](#5-comptes-par-défaut-développement)
- [6. Paramètres (Settings)](#6-paramètres-settings)
- [7. Endpoints clés](#7-endpoints-clés)
- [8. Tests et validation](#8-tests-et-validation)
- [9. Dépannage](#9-dépannage)
- [10. Sécurité & bonnes pratiques](#10-sécurité--bonnes-pratiques)
- [11. Structure du dépôt](#11-structure-du-dépôt)

---

## 1. Présentation

**ControlTwin** est une solution orientée ICS/OT permettant :

- la supervision centralisée des actifs et collecteurs industriels,
- la gestion d’alertes cybersécurité et opérationnelles,
- l’exposition d’APIs robustes (auth, assets, sites, collectors, alerts, settings),
- l’intégration de capacités IA (anomalies, simulation, remédiation, état du jumeau).

Le projet est organisé en architecture multi-services pour faciliter l’évolutivité et la maintenance.

---

## 2. Architecture

```text
ICSTwin/
├─ controltwin-frontend/   # Interface web React (Vite)
├─ controltwin-backend/    # API FastAPI + PostgreSQL + Alembic
├─ controltwin-ai/         # Services IA (anomaly, predictive, remediation, simulation)
├─ start.bat / start.sh    # Scripts de démarrage global
└─ README.md               # Ce document
```

### Vue logique

1. **Frontend** (React/Vite)
   - Authentification JWT
   - Dashboard, Assets, Alerts, Users, Settings
2. **Backend** (FastAPI)
   - API REST versionnée
   - RBAC / auth / gestion métiers
   - Persistance SQL + migrations Alembic
3. **AI Services**
   - Détection d’anomalies
   - Capacités prédictives/simulation/remédiation

---

## 3. Stack technique

### Frontend
- React
- Vite
- Axios
- Store côté client (auth/alerts)
- UI composants custom

### Backend
- FastAPI
- SQLAlchemy (async)
- PostgreSQL
- Alembic
- JWT + RBAC

### IA
- Services Python dédiés
- Routage API spécialisé (anomaly, predictive, remediation, twin state)

---

## 4. Démarrage rapide

> Prérequis recommandés :
> - Node.js LTS + npm
> - Python 3.11+
> - Docker + Docker Compose (pour backend/db)
> - Git

### Option A — démarrage global (recommandé)

#### Windows
```bash
start.bat
```

#### Linux / macOS
```bash
chmod +x start.sh
./start.sh
```

### Option B — démarrage manuel

#### 1) Backend
```bash
cd controltwin-backend
docker compose up -d
```

#### 2) Frontend
```bash
cd controltwin-frontend
npm install
npm run dev
```

Le frontend sera accessible sur l’URL affichée par Vite (souvent `http://localhost:5173` ou `http://localhost:5174`).

---

## 5. Comptes par défaut (développement)

Utiliser ces identifiants uniquement en local/dev :

- **Username**: `admin`
- **Password**: `ControlTwin2025!`

---

## 6. Paramètres (Settings)

La page **Settings** est disponible côté frontend et persistée côté backend.

### Capacités actuelles
- Sections UI/affichage
- Notifications
- Dashboard
- Security
- Data collection
- Sauvegarde en bulk via API (`/settings/bulk`)
- Persistance SQL via table `settings`

### Notes techniques
- Scope utilisateur supporté (`scope = user`)
- Résolution `user_id` côté backend possible via l’utilisateur courant
- Endpoint backend principal : `POST /api/v1/settings/bulk`

---

## 7. Endpoints clés

Base API (exemple local) : `http://localhost:8000/api/v1`

| Domaine | Endpoint | Méthode |
|---|---|---|
| Auth | `/auth/login` | POST |
| Auth | `/auth/refresh` | POST |
| Users | `/users/me` | GET |
| Sites | `/sites` | GET |
| Assets | `/assets` | GET |
| Alerts | `/alerts` | GET |
| Settings | `/settings` | GET |
| Settings | `/settings/{key}` | PUT |
| Settings | `/settings/bulk` | POST |

---

## 8. Tests et validation

### API (exemple login)
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"ControlTwin2025!\"}"
```

### Recommandations
- Valider les scénarios nominaux + erreurs
- Vérifier les permissions RBAC
- Vérifier la persistance des settings après redémarrage backend

---

## 9. Dépannage

### 1) Port frontend déjà utilisé
Vite bascule automatiquement sur un autre port (`5174`, etc.). Utiliser l’URL affichée dans le terminal.

### 2) “Invalid credentials or account locked”
- Vérifier les identifiants par défaut
- Vérifier l’état de la base et des seeds
- Vérifier que backend + DB sont bien démarrés

### 3) Échec de sauvegarde Settings
- Vérifier la disponibilité backend (`/api/v1/settings/bulk`)
- Vérifier le token d’authentification
- Vérifier logs API (erreurs 4xx/5xx)

### 4) Migrations Alembic
- En cas d’environnement local partiellement migré, réaligner l’état de migration avant retest.

---

## 10. Sécurité & bonnes pratiques

- Ne jamais utiliser les credentials par défaut en production.
- Externaliser les secrets via variables d’environnement.
- Restreindre CORS et durcir RBAC en environnement réel.
- Mettre en place rotation des tokens/secrets.
- Activer monitoring, audit logs et alerting.

---

## 11. Structure du dépôt

```text
controltwin-frontend/
  src/
    api/
    components/
    hooks/
    pages/
    store/

controltwin-backend/
  app/
    api/v1/endpoints/
    auth/
    core/
    db/
    models/
    schemas/
    services/
  alembic/
    versions/

controltwin-ai/
  app/
    api/
    anomaly/
    predictive/
    remediation/
    simulation/
    twin_state/
```

---

## Mainteneurs

Projet maintenu par l’équipe ControlTwin.  
Pour toute évolution fonctionnelle, documenter :
1) le besoin,
2) les impacts API/UI,
3) le plan de test associé.
