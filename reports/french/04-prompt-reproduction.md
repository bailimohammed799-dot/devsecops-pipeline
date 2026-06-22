# Prompt : Guide de Reproduction — Pipeline DevSecOps

> **Instructions pour l'IA (GLM 5.2) :** Générez un guide de reproduction pas à pas en français, destiné à un évaluateur qui doit pouvoir cloner le dépôt et exécuter la pipeline complète sur une machine propre Ubuntu 22.04.

---

## Objectif

Ce guide permet à un évaluateur de reproduire l'intégralité de la pipeline DevSecOps à partir d'une machine Ubuntu 22.04 vierge, sans aucune connaissance préalable du projet.

---

## Prérequis Matériels

| Ressource | Minimum | Recommandé |
|-----------|---------|------------|
| RAM | 8 GB | 16 GB |
| CPU | 2 cœurs | 4 cœurs |
| Disque | 20 GB libres | 50 GB |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| Réseau | Connexion Internet | Haut débit |

> **Note :** SonarQube Community nécessite au minimum 2 GB de RAM pour fonctionner correctement.

---

## Étape 0 : Préparer l'Environnement

**Durée :** ~15 minutes

```bash
# 1. Mettre à jour le système
sudo apt-get update && sudo apt-get upgrade -y

# 2. Installer Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# IMPORTANT : se déconnecter et se reconnecter pour appliquer le groupe docker
newgrp docker

# 3. Installer les dépendances système
sudo apt-get install -y \
    git make curl jq \
    python3 python3-pip python3-venv \
    openjdk-11-jre-headless \
    ca-certificates

# 4. Vérifier les installations
docker --version         # ≥ 24.0
python3 --version        # ≥ 3.10
git --version            # ≥ 2.34
```

---

## Étape 1 : Cloner le Dépôt

**Durée :** ~30 secondes

```bash
git clone https://github.com/bailimohammed799-dot/devsecops-pipeline.git
cd devsecops-pipeline
```

**Structure attendue après clonage :**
```
devsecops-pipeline/
├── .github/workflows/    # 3 fichiers YAML (CI, CD, nightly)
├── docker/               # Dockerfile + compose
├── scripts/              # 9 scripts shell/python
├── tests/security/       # 12 scénarios DAST
├── docs/                 # 9 documents
├── reports/french/       # Prompts pour rapports en français
├── Makefile
├── Jenkinsfile
└── README.md
```

---

## Étape 2 : Configurer l'Environnement

**Durée :** ~2 minutes

```bash
# Copier le template d'environnement
cp .env.example .env

# Éditer le fichier .env avec vos valeurs
nano .env
```

**Variables à configurer obligatoirement :**

```ini
# Application cible
TARGET_REPO=gothinkster/flask-realworld-example-app
TARGET_COMMIT=4b95fb2227dfeb5dd1a45d89b2bf48630b93fd28

# SonarQube (générer un token via l'interface web après démarrage)
SONAR_HOST_URL=http://localhost:9000
SONAR_TOKEN=votre-token-sonarqube

# Application Flask
SECRET_KEY=votre-clé-secrète-aléatoire

# Seuil de couverture (optionnel)
MIN_COVERAGE=60
```

**Générer une clé secrète aléatoire :**
```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
# Copier la sortie comme valeur de SECRET_KEY
```

---

## Étape 3 : Installer les Outils (make setup)

**Durée :** ~10-15 minutes

```bash
make setup
```

**Ce que fait `make setup` :**

1. ✅ Installe les paquets système (python3, nodejs, openjdk)
2. ✅ Installe les outils Python (semgrep, bandit, pip-audit, pytest)
3. ✅ Installe Sonar Scanner CLI (depuis les binaires officiels)
4. ✅ Installe Trivy (scanner de vulnérabilités conteneur)
5. ✅ Télécharge les images Docker (SonarQube, OWASP ZAP, PostgreSQL, Registry)

**Vérification rapide :**
```bash
semgrep --version     # ≥ 1.0
bandit --version      # ≥ 1.7
trivy --version       # ≥ 0.45
sonar-scanner --version  # ≥ 5.0
```

---

## Étape 4 : Exécuter la Pipeline (make pipeline)

**Durée :** ~15-20 minutes

```bash
make pipeline
```

### Déroulement Détaillé

#### Stage 1 — Récupération du code source (~30s)
```
=== Stage 1: Source retrieval & integrity ===
Cloning gothinkster/flask-realworld-example-app...
Commit verified: 4b95fb2227dfeb5dd1a45d89b2bf48630b93fd28
Gitleaks pre-scan...
Stage 1: DONE
```

#### Stage 2 — Build (~2 min)
```
=== Stage 2: Build ===
pip install -r requirements.txt...
Build OK
Stage 2: DONE
```

#### Stage 3 — SonarQube (~3 min)
```
=== Stage 3: SonarQube quality scan ===
Waiting for SonarQube...
SonarQube is UP
Running sonar-scanner...
Quality Gate: OK
Stage 3: DONE
```

#### Stage 4 — Tests unitaires (~1 min)
```
=== Stage 4: Unit tests & coverage ===
pytest tests/ -v --cov=conduit...
30 passed, 0 failed
Coverage: 85%
Stage 4: DONE
```

#### Stage 5 — SAST (~2 min)
```
=== Stage 5: SAST ===
Semgrep: 0 findings (156 rules)
Bandit: 2 findings (LOW)
pip-audit: 3 findings (HIGH — SQLAlchemy CVEs)
Stage 5: DONE
```

#### Stage 6 — Image Docker (~3 min)
```
=== Stage 6: Image/artifact build ===
Building Docker image...
Trivy filesystem scan...
Trivy image scan...
Pushing to localhost:5000...
Stage 6: DONE
```

#### Stage 7 — Déploiement (~1 min)
```
=== Stage 7: Deploy to test environment ===
docker compose up -d...
Waiting for app health check...
App is responding (HTTP 200)
Smoke test: PASS
Stage 7: DONE
```

#### Stage 8 — DAST (~5 min)
```
=== Stage 8: DAST ===
ZAP Baseline scan...
Running custom scenarios...
  Scenario 01: SQL Injection — 2 findings
  Scenario 02: MITM — 2 findings
  ...
  Scenario 12: Sender Spoofing — N/A
Stage 8: DONE
```

#### Stage 9 — Rapports (~5s)
```
=== Stage 9: Report generation ===
Generating SUMMARY.md...
Stage 9: DONE
```

---

## Étape 5 : Consulter les Résultats

```bash
# Trouver le dernier rapport
DERMIER_RUN=$(ls -1t reports/ | head -1)
echo "Rapports disponibles : reports/$DERMIER_RUN/"

# Lire le résumé exécutif
cat reports/$DERMIER_RUN/SUMMARY.md

# Lister tous les artefacts
ls -R reports/$DERMIER_RUN/

# Ouvrir le dashboard SonarQube
echo "Dashboard : http://localhost:9000/dashboard?id=conduit"
```

**Structure des rapports :**
```
reports/20260622-220000/
├── SUMMARY.md                    # Résumé exécutif
├── 01-source/clone-manifest.json  # Métadonnées du clone
├── 02-build/build.log            # Log de compilation
├── 03-sonar/sonar-report.md      # Rapport SonarQube
├── 04-tests/junit.xml            # Résultats tests (JUnit)
├── 05-sast/
│   ├── semgrep.sarif             # Résultats Semgrep (SARIF)
│   ├── bandit.json               # Résultats Bandit
│   └── sast-summary.md           # Résumé SAST
├── 06-image/trivy-image.json     # Scan Trivy
├── 07-deploy/smoke-test.md       # Test de fumée
└── 08-dast/scenarios/            # 12 rapports de scénarios
    ├── 01-SQL_Injection.md
    ├── 02-MITM.md
    └── ...
```

---

## Commandes Utiles

```bash
# Nettoyer les conteneurs (garde les rapports)
make clean

# Nettoyer TOUT (conteneurs + images + cache Docker)
make clean && docker system prune -a

# Relancer uniquement une étape spécifique
make stage5    # SAST uniquement
make stage8    # DAST uniquement

# Réexécuter la pipeline avec un nouveau dossier de rapports
make pipeline

# Aide
make help
```

---

## Résolution des Problèmes

### Problème : SonarQube ne démarre pas
```bash
# Vérifier les logs
docker logs sonarqube

# Cause fréquente : mémoire insuffisante
docker stats --no-stream
# Solution : augmenter la mémoire Docker Desktop à ≥ 4 GB

# Vérifier l'état
curl -s http://localhost:9000/api/system/status
```

### Problème : Tests échouent (connexion base de données)
```bash
# Vérifier que PostgreSQL est lancé
docker ps | grep postgres

# Vérifier la variable d'environnement
echo $DATABASE_URL

# Dans le docker-compose, PostgreSQL est accessible à l'adresse :
# postgresql://conduit:conduit_dev_password@db:5432/conduit
```

### Problème : Permission denied sur Docker
```bash
# Vérifier l'appartenance au groupe docker
groups | grep docker

# Si absent :
sudo usermod -aG docker $USER
# Se déconnecter et se reconnecter
```

### Problème : Port déjà utilisé
```bash
# Vérifier les ports 8080, 9000, 5000, 5432
sudo lsof -i :8080
sudo lsof -i :9000

# Libérer un port :
sudo kill -9 <PID>
# ou changer les ports dans docker-compose.yml
```

### Problème : Espace disque insuffisant
```bash
# Nettoyer Docker
docker system prune -a --volumes

# Supprimer les anciens rapports
ls -t reports/ | tail -n +5 | xargs rm -rf
```

---

## Exécution via GitHub Actions (Alternative)

Si vous ne voulez pas exécuter localement, la pipeline s'exécute automatiquement sur GitHub Actions :

1. **Push sur la branche main** → déclenche `ci.yml` + `cd.yml`
2. **Pull request** → déclenche `ci.yml` (étapes 1-5)
3. **Tous les jours à 3h UTC** → déclenche `nightly.yml` (scan complet)

**Configurer les secrets GitHub requis :**
- Aller dans Settings → Secrets and variables → Actions
- Ajouter `SONAR_TOKEN`

**Consulter les résultats :**
- Onglet « Actions » du dépôt GitHub
- Artefacts téléchargeables (ZIP)
- Dashboard SonarQube (si exposé publiquement)

---

## Instructions de Formatage pour l'IA

**Format de sortie attendu :**
- Guide PDF en français, format « tutoriel pas à pas »
- Chaque étape avec : durée estimée, commandes exactes, sortie attendue
- Captures d'écran (placeholders — indiquer où les insérer)
- Blocs de code avec sortie console simulée (réaliste)
- Section « Résolution des problèmes » avec tableau problème/solution
- Police : Times New Roman 11pt, code en Courier New 9pt
- Longueur cible : 10-12 pages
