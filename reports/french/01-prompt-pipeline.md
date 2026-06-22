# Prompt : Documentation Technique — Pipeline DevSecOps

> **Instructions pour l'IA (GLM 5.2) :** Générez une documentation technique détaillée en français décrivant l'architecture, la configuration et le fonctionnement de la pipeline DevSecOps. Destiné à un public technique (développeurs, ops, sécurité).

---

## Objectif du Document

Produire une documentation technique complète qui permettrait à un ingénieur n'ayant jamais vu le projet de comprendre, exécuter et étendre la pipeline.

---

## Architecture Globale

### Dépôt GitHub
- **URL :** https://github.com/bailimohammed799-dot/devsecops-pipeline
- **Application cible :** https://github.com/gothinkster/flask-realworld-example-app (commit `4b95fb2`)
- **Langage :** Python 3.11 / Flask
- **Licences :** MIT (les deux)

### Structure du Dépôt

```
devsecops-pipeline/
├── .github/workflows/
│   ├── ci.yml                  # Étapes 1-5 : checkout → build → SonarQube → tests → SAST
│   ├── cd.yml                  # Étapes 6-8 : image → déploiement → DAST
│   └── nightly.yml             # Scan DAST complet + dependency check (planifié)
├── Jenkinsfile                 # Pipeline équivalente pour Jenkins
├── docker/
│   ├── Dockerfile              # Build multi-stage (non-root, slim)
│   ├── Dockerfile.test         # Image pour les tests
│   └── docker-compose.yml      # Services : app + db + sonarqube + registry
├── sonar-project.properties    # Configuration SonarQube
├── .secrets.baseline           # Liste blanche Gitleaks
├── .env.example                # Template des variables d'environnement
├── .gitleaks.toml              # Configuration Gitleaks
├── Makefile                    # Cibles : setup / pipeline / clean / reports
├── scripts/
│   ├── verify_integrity.sh     # Étape 1 — clone + vérification SHA + Gitleaks
│   ├── run_sonar.sh            # Étape 3 — lancement SonarQube + scanner
│   ├── run_sast.sh             # Étape 5 — Semgrep + Bandit + Gitleaks + pip-audit
│   ├── build_image.sh          # Étape 6 — build Docker + Trivy + push
│   ├── smoke_test.sh           # Étape 7 — health check + smoke test
│   ├── run_dast.sh             # Étape 8a — OWASP ZAP
│   ├── run_scenarios.sh        # Étape 8b — 12 scénarios personnalisés
│   ├── check_headers.sh        # Vérification des en-têtes de sécurité
│   └── aggregate_reports.py    # Étape 9 — génération de SUMMARY.md
├── tests/security/             # 12 scripts de scénarios DAST
│   ├── scenario_01_sql_injection.py
│   ├── scenario_02_mitm.py
│   ├── ...                     # (12 fichiers au total)
│   └── scenario_12_sender_spoofing.py
├── docs/                       # Documentation (9 fichiers)
├── reports/                    # Artefacts générés (par run)
├── target-app/                 # Clone local de l'application cible (gitignoré)
└── README.md
```

---

## Détail des 9 Étapes de la Pipeline

### Étape 1 — Récupération du code source et intégrité

**Script :** `scripts/verify_integrity.sh`

```
1. Clone le dépôt cible depuis GitHub
2. Checkout du commit pinné (TARGET_COMMIT)
3. Vérification : SHA correspond exactement
4. Vérification GPG (non-bloquante)
5. Gitleaks pre-scan sur l'arbre cloné
6. Génération du manifeste JSON (clone-manifest.json)
```

**Artefact :** `reports/<run>/01-source/clone-manifest.json`
**Durée :** ~30 secondes

### Étape 2 — Build

```
1. pip install -r requirements.txt
2. Vérification : import du module principal réussi
```

**Artefacts :** `reports/<run>/02-build/build.log`, `build-status.json`
**Durée :** ~2 minutes

### Étape 3 — Analyse de qualité (SonarQube)

**Script :** `scripts/run_sonar.sh`

```
1. Démarrage de SonarQube Community dans Docker (compose)
2. Attente de l'API /api/system/status → UP (timeout 5 min, retry toutes les 10s)
3. Exécution de sonar-scanner avec sonar-project.properties
4. Récupération du statut Quality Gate via /api/qualitygates/project_status
5. Génération du rapport Markdown
```

**Artefact :** `reports/<run>/03-sonar/sonar-report.md`
**Dashboard :** http://localhost:9000/dashboard?id=conduit
**Durée :** ~3 minutes

### Étape 4 — Tests unitaires et couverture

```
1. pytest tests/ -v --junitxml=junit.xml --cov=conduit --cov-report=xml:coverage.xml
2. Vérification : couverture ≥ MIN_COVERAGE (60% par défaut)
3. Échec si des tests échouent
```

**Artefacts :** `reports/<run>/04-tests/junit.xml`, `coverage.xml`
**Durée :** ~1 minute

### Étape 5 — Analyse de sécurité statique (SAST)

**Script :** `scripts/run_sast.sh`

| Outil | Règles/Config | Format |
|-------|--------------|--------|
| **Semgrep** | p/owasp-top-ten, p/security-audit, p/python | SARIF + JSON |
| **Bandit** | Toutes les règles | JSON |
| **Gitleaks** | .gitleaks.toml | JSON |
| **pip-audit** | Base PyPA Advisory DB | JSON |

**Artefacts :** SARIF + JSON + `sast-summary.md`
**Durée :** ~2 minutes

### Étape 6 — Construction de l'image Docker et scan

**Script :** `scripts/build_image.sh`

```
1. Build multi-stage :
   - Stage 1 (builder) : pip install des dépendances
   - Stage 2 (runtime) : python:3.11-slim, utilisateur non-root, HEALTHCHECK
2. Labels OCI : revision, created, version
3. Trivy filesystem scan sur le contexte de build
4. Trivy image scan sur l'image résultante
5. Push vers le registre local (localhost:5000)
```

**Artefacts :** `image-metadata.json`, `trivy-fs.json`, `trivy-image.json`, `image-scan-summary.md`
**Durée :** ~3 minutes

### Étape 7 — Déploiement dans l'environnement de test

**Script :** `scripts/smoke_test.sh`

```
1. docker compose up -d (app + db + sonarqube + registry)
2. Attente du health endpoint (/api/healthz) → 200 (timeout 90s)
3. Smoke test : GET /api/, POST /api/users/login, POST /api/users
```

**Services Docker Compose :**

| Service | Image | Port | Health Check |
|---------|-------|------|-------------|
| db | postgres:16-alpine | 5432 | pg_isready |
| app | construit localement | 8080→5000 | /api/healthz |
| sonarqube | sonarqube:community | 9000 | /api/system/status |
| registry | registry:2 | 5000 | — |

**Artefacts :** `deploy.log`, `smoke-test.md`
**Durée :** ~1 minute

### Étape 8 — Tests de sécurité dynamiques (DAST)

#### 8a — OWASP ZAP

**Script :** `scripts/run_dast.sh`

- **Baseline scan** (chaque PR) : passif, rapide
  ```bash
  docker run owasp/zap2docker-stable zap-baseline.py -t http://app:8080
  ```
- **Active scan** (nightly + merge main) : complet, spider + ajax spider
  ```bash
  docker run owasp/zap2docker-stable zap-full-scan.py -t http://app:8080
  ```

**Artefacts :** `zap-baseline.html`, `zap-baseline.xml`, `zap-baseline.json`

#### 8b — 12 Scénarios Personnalisés

**Script :** `scripts/run_scenarios.sh`

Chaque scénario est un script Python indépendant (`tests/security/scenario_NN_*.py`) qui :
1. Émet des requêtes HTTP réelles contre l'application
2. Vérifie si l'application est vulnérable
3. Produit un rapport Markdown avec :
   - Description de la vulnérabilité
   - Preuve (requête/réponse)
   - Score CVSS v3.1 (si applicable)
   - Impact métier
   - Code de correction recommandé
   - Difficulté de correction (S/M/L)

**Les 12 scénarios :**

1. **SQL Injection** — Payloads `' OR '1'='1`, time-based, sur tous les champs de saisie
2. **Man-in-the-Middle (MITM)** — Vérification TLS, HSTS, en-têtes de sécurité
3. **Broken Authentication** — Mots de passe faibles, credentials par défaut, rate limiting
4. **Session Hijacking** — Cookies HttpOnly/Secure/SameSite, expiration JWT, fixation
5. **Replay Attack** — Rejeu de requêtes valides, nonce/timestamp, jti
6. **Privilege Escalation** — Accès aux endpoints admin, parameter tampering
7. **API Abuse** — Accès sans auth, payloads malformés, mass assignment
8. **Denial of Service (DoS)** — Payloads volumineux, slowloris, concurrence
9. **Credential Stuffing** — Liste de credentials compromis, vérification rate limiting
10. **Security Misconfiguration** — Pages d'erreur par défaut, stack traces, consoles exposées
11. **Sensitive Data Exposure** — Patterns PII, hachage de mots de passe
12. **Sender Spoofing** — Injection d'en-têtes email (N/A pour cette application)

**Artefacts :** Un fichier Markdown par scénario dans `reports/<run>/08-dast/scenarios/`

### Étape 9 — Génération des rapports

**Script :** `scripts/aggregate_reports.py`

```
1. Parcourt tous les artefacts des étapes 1-8
2. Extrait les métriques clés
3. Génère un résumé exécutif (SUMMARY.md) contenant :
   - Statut de chaque étape
   - Résultats SonarQube (Quality Gate + métriques)
   - Résultats SAST (comptage par sévérité)
   - Résultats DAST (tableau des 12 scénarios)
   - Top 5 des risques
   - Index des artefacts
4. Publie le résumé dans GitHub Actions Job Summary ($GITHUB_STEP_SUMMARY)
```

**Artefact :** `reports/<run>/SUMMARY.md`
**Durée :** ~5 secondes

---

## Configuration CI/CD

### GitHub Actions

**Fichier :** `.github/workflows/ci.yml` (Étapes 1-5)
- Déclencheurs : push et pull_request sur main
- Runners : ubuntu-22.04
- Secrets requis : `SONAR_TOKEN`

**Fichier :** `.github/workflows/cd.yml` (Étapes 6-8)
- Déclencheur : push sur main
- Utilise les services PostgreSQL

**Fichier :** `.github/workflows/nightly.yml`
- Déclencheur : cron `0 3 * * *` (3h UTC quotidien) + workflow_dispatch
- Exécute le scan ZAP actif complet + OWASP Dependency-Check

### Jenkinsfile

Pipeline déclarative Jenkins couvrant les 9 étapes. Utilise les mêmes scripts shell. Archive les artefacts de rapports.

---

## Exécution Locale

### Prérequis
- Ubuntu 22.04
- Docker ≥ 24.0
- make, git, curl, jq
- Python 3.11, pip
- 8+ GB RAM (SonarQube nécessite ~3 GB)

### Commandes

```bash
# Installation unique
make setup

# Pipeline complète (9 étapes)
make pipeline

# Nettoyage des conteneurs
make clean

# Consultation des rapports
ls reports/$(ls -1t reports/ | head -1)/
cat reports/$(ls -1t reports/ | head -1)/SUMMARY.md
```

---

## Variables d'Environnement

**Fichier :** `.env.example` → copier vers `.env`

| Variable | Obligatoire | Description |
|----------|:----------:|-------------|
| `TARGET_REPO` | Oui | Dépôt GitHub de l'application cible |
| `TARGET_COMMIT` | Oui | SHA du commit à analyser |
| `SONAR_HOST_URL` | Oui | URL du serveur SonarQube |
| `SONAR_TOKEN` | Oui | Token d'authentification SonarQube |
| `SECRET_KEY` | Oui | Clé secrète Flask |
| `MIN_COVERAGE` | Non | Seuil de couverture (défaut : 60) |
| `REGISTRY_URL` | Non | URL du registre Docker (défaut : localhost:5000) |

---

## Sécurité de la Pipeline

- **Aucun secret dans le code :** Tous les secrets passent par des variables d'environnement ou GitHub Secrets
- **`.env` gitignoré :** Seul le template `.env.example` est versionné
- **Gitleaks :** Scan pre-commit + dans la CI (étape 1 et étape 5)
- **Scan Trivy :** Double scan (filesystem + image) à chaque build
- **OWASP ZAP :** Baseline scan sur chaque PR, actif en nightly
- **Docker non-root :** L'image utilise un utilisateur `conduit` dédié
- **Base slim :** `python:3.11-slim` pour réduire la surface d'attaque

---

## Instructions de Formatage pour l'IA

**Format de sortie attendu :**
- Document technique PDF en français
- Police : Consolas/Inconsolata pour le code, Times New Roman pour le texte
- Chaque étape sur une nouvelle page ou section clairement délimitée
- Diagrammes Mermaid rendus en images
- Extraits de code avec coloration syntaxique (thème sombre)
- Tableaux de configuration bien formatés
- Index des commandes en fin de document
- Longueur cible : 10-12 pages
