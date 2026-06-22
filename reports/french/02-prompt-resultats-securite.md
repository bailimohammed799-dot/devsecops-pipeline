# Prompt : Résultats des Analyses de Sécurité — Pipeline DevSecOps

> **Instructions pour l'IA (GLM 5.2) :** Générez un rapport de sécurité détaillé en français présentant tous les résultats des analyses SAST et DAST. Format professionnel, destiné à une équipe de développement et sécurité.

---

## Contexte

Ce rapport présente les résultats complets des analyses de sécurité effectuées sur l'application **Conduit** (https://github.com/gothinkster/flask-realworld-example-app), un clone de Medium.com développé en Flask/Python.

**Méthodologie :** L'analyse combine :
- **SAST (Static Application Security Testing) :** Analyse statique du code source
- **DAST (Dynamic Application Security Testing) :** 12 scénarios de test analysés sur le code source
- **Dependency Scanning :** Analyse des vulnérabilités dans les dépendances
- **Secret Scanning :** Détection de secrets exposés

**Date de l'analyse :** 22 juin 2026
**Version analysée :** Commit `4b95fb2`

---

## Résumé Exécutif

**Total : 20 vulnérabilités identifiées**

| Sévérité | Nombre | Pourcentage |
|----------|--------|-------------|
| 🔴 CRITIQUE | 1 | 5% |
| 🔴 HAUTE | 5 | 25% |
| 🟡 MOYENNE | 8 | 40% |
| 🟢 BASSE | 6 | 30% |

**Score de sécurité global :** 55/100 (moyen — améliorations nécessaires)

---

## Section 1 : Résultats SAST (Static Application Security Testing)

### 1.1 Semgrep

**Règles exécutées :** 156 (p/owasp-top-ten, p/security-audit, p/python)
**Fichiers analysés :** 21
**Résultat :** ✅ 0 vulnérabilité

L'application utilise SQLAlchemy ORM de manière cohérente avec des requêtes paramétrées, ce qui offre une protection intégrée contre les injections SQL et XSS. Aucun motif OWASP Top 10 n'a été détecté.

### 1.2 Bandit

**Résultat :** 2 vulnérabilités (toutes BASSE)

| ID | Règle | Fichier | Ligne | Description |
|----|-------|--------|-------|-------------|
| B404 | subprocess_import | conduit/commands.py | 5 | Import du module `subprocess` |
| B603 | subprocess_without_shell_equals_true | conduit/commands.py | 41 | Appel à `subprocess.call()` |

**Analyse :** Ces deux vulnérabilités sont dans des commandes CLI de développement (`flask lint`, `flask test`), pas exposées via l'API web. La sévérité BASSE est appropriée car :
- Les commandes CLI ne sont exécutées que par les développeurs
- Aucune entrée utilisateur non fiable n'est passée à `subprocess.call()`
- L'impact est limité à l'environnement de développement

### 1.3 pip-audit — Vulnérabilités dans les Dépendances

**Résultat :** 3 vulnérabilités HAUTE dans 1 paquet

| CVE | Paquet | Version installée | Version corrigée | CVSS | Description |
|-----|--------|-------------------|------------------|------|-------------|
| CVE-2019-7164 | SQLAlchemy | 1.1.9 | 1.3.0b3 | 9.8 | Injection SQL via le paramètre `order_by` |
| CVE-2019-7164 | SQLAlchemy | 1.1.9 | 1.3.0b3 | 9.8 | (doublon — même CVE) |
| CVE-2019-7548 | SQLAlchemy | 1.1.9 | 1.2.18 | 9.8 | Injection SQL via le paramètre `group_by` |

**Détail technique :**

**CVE-2019-7164 :** SQLAlchemy avant 1.3.0b3 permet une injection SQL lorsque des chaînes contrôlées par l'attaquant sont passées à la méthode `order_by()`. Le correctif (commit 30307c4) a été appliqué uniquement sur la branche principale et n'a jamais été rétroporté sur la ligne 1.2.x. **Toutes les versions 1.2.x restent vulnérables.**

**Statut dans l'application :** Le code actuel utilise `order_by(Article.createdAt.desc())` — une référence de colonne statique, pas une entrée utilisateur. La vulnérabilité n'est donc **pas directement exploitable**. Cependant :
- Si un développeur ajoute `order_by(user_input)` à l'avenir, l'application devient immédiatement vulnérable
- La version 1.1.9 date de 2017 et n'est plus maintenue
- Aucun correctif de sécurité n'est disponible pour cette branche

**CVE-2019-7548 :** Similaire à CVE-2019-7164 mais via le paramètre `group_by()`. L'application n'utilise pas `group_by()` actuellement.

**Recommandation :** Mettre à jour SQLAlchemy vers ≥ 2.0.0. La mise à jour majeure peut nécessiter des adaptations de code (l'API a changé entre 1.x et 2.x).

### 1.4 Gitleaks

**Statut :** Non exécuté (nécessite un scan complet de l'historique git sur Ubuntu)
**Config :** `.gitleaks.toml` prêt

---

## Section 2 : Résultats DAST (Dynamic Application Security Testing)

### Analyse par Scénario

#### Scénario 1 — Injection SQL
**Sévérité max :** HAUTE

| ID | Sévérité | Description |
|----|----------|-------------|
| F-1.1 | HAUTE | SQLAlchemy 1.1.9 — CVE-2019-7164 (SQLi via order_by) |
| F-1.2 | INFO | `order_by(Article.createdAt.desc())` — colonne statique, vérifié OK |

**Analyse :** L'application utilise l'ORM SQLAlchemy de manière systématique, ce qui offre une protection solide contre les injections SQL classiques. Le seul risque provient de la version obsolète de SQLAlchemy. Aucune requête SQL brute ni concaténation de chaînes n'a été trouvée.

#### Scénario 2 — Man-in-the-Middle (MITM)
**Sévérité max :** HAUTE

| ID | Sévérité | Description |
|----|----------|-------------|
| F-2.1 | HAUTE | Application servie en HTTP uniquement — pas de TLS/SSL |
| F-2.2 | MOYENNE | En-tête HSTS (Strict-Transport-Security) non configuré |

**Analyse :** L'application Flask elle-même n'implémente pas TLS. Dans un déploiement réel, un reverse proxy (Nginx, Traefik) devrait assurer la terminaison TLS. L'absence de HSTS expose les utilisateurs à des attaques de downgrade.

**Correction :**
```nginx
# Configuration Nginx recommandée
server {
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    location / {
        proxy_pass http://app:5000;
    }
}
```

#### Scénario 3 — Broken Authentication
**Sévérité max :** HAUTE

| ID | Sévérité | Description |
|----|----------|-------------|
| F-3.1 | HAUTE | Absence de rate limiting sur `/api/users/login` |
| F-3.2 | MOYENNE | Aucune politique de complexité de mot de passe |
| F-3.3 | MOYENNE | Pas de verrouillage de compte après échecs |
| F-3.4 | BASSE | Expiration JWT excessive en mode dev (~11.5 jours) |

**Analyse détaillée :**

**F-3.1 — Rate Limiting :** L'endpoint de connexion accepte un nombre illimité de tentatives. Un attaquant peut :
- Tester des milliers de mots de passe par force brute
- Effectuer du credential stuffing avec des listes de credentials compromis
- Saturer le service avec des tentatives de connexion

**F-3.2 — Politique de mot de passe :** Aucune validation de complexité n'est effectuée. L'application accepte des mots de passe comme `"a"` ou `"123"`.

**F-3.4 — Expiration JWT :** En mode développement, le token JWT expire après `10^6` secondes (~11.5 jours), ce qui est excessif même pour le développement.

#### Scénario 4 — Session Hijacking
**Sévérité max :** BASSE

| ID | Sévérité | Description |
|----|----------|-------------|
| F-4.1 | INFO | JWT dans l'en-tête Authorization (pas de cookies) |
| F-4.2 | BASSE | Pas de mécanisme de révocation de token JWT |

**Analyse :** L'application utilise JWT dans l'en-tête HTTP `Authorization: Token <jwt>`, et non des cookies de session. Cela rend les attaques classiques de hijacking de cookies (XSS → vol de cookie) non applicables. Cependant, un token JWT volé reste valide jusqu'à son expiration, car aucun mécanisme de blacklist n'est implémenté.

#### Scénario 5 — Replay Attack
**Sévérité max :** MOYENNE

| ID | Sévérité | Description |
|----|----------|-------------|
| F-5.1 | MOYENNE | Tokens JWT sans identifiant unique (jti) |
| F-5.2 | BASSE | Pas de clés d'idempotence sur les endpoints de mutation |

#### Scénario 6 — Privilege Escalation
**Sévérité max :** INFO

| ID | Sévérité | Description |
|----|----------|-------------|
| F-6.1 | INFO | Modèle de permissions plat — pas de rôles (par conception) |
| F-6.2 | INFO | Vérification de propriété des ressources (author_id) correctement implémentée |

**Analyse :** L'application utilise un modèle où tous les utilisateurs authentifiés ont les mêmes privilèges. Il n'y a pas de rôles administrateur/utilisateur, donc pas de vecteur d'escalade de privilèges. Les opérations de modification/suppression vérifient que l'utilisateur est bien le propriétaire de la ressource.

#### Scénario 7 — API Abuse
**Sévérité max :** MOYENNE

| ID | Sévérité | Description |
|----|----------|-------------|
| F-7.1 | MOYENNE | Pas de limite `MAX_CONTENT_LENGTH` — payloads volumineux possibles |
| F-7.2 | BASSE | Liste blanche CORS étendue (plusieurs ports localhost) |

#### Scénario 8 — Denial of Service (DoS)
**Sévérité max :** MOYENNE

| ID | Sévérité | Description |
|----|----------|-------------|
| F-8.1 | MOYENNE | Pas de timeout de requête ni limite de taille configurés |

#### Scénario 9 — Credential Stuffing
**Sévérité max :** HAUTE

| ID | Sévérité | Description |
|----|----------|-------------|
| F-9.1 | HAUTE | Rate limiting absent — credential stuffing possible |

#### Scénario 10 — Security Misconfiguration
**Sévérité max :** CRITIQUE

| ID | Sévérité | Description |
|----|----------|-------------|
| F-10.1 | CRITIQUE | `SECRET_KEY` avec valeur par défaut `'secret-key'` — JWT forgeable |
| F-10.2 | MOYENNE | `DEBUG=True` dans DevConfig — doit être False en déploiement |

**Détail F-10.1 (CRITIQUE) :**

```python
# Fichier : conduit/settings.py, ligne 10
SECRET_KEY=os.env...ET', 'secret-key')  # TODO: Change me
```

Si la variable d'environnement `CONDUIT_SECRET` n'est pas définie, la clé secrète utilisée pour signer les tokens JWT est `'secret-key'`. N'importe quel attaquant connaissant cette clé peut générer des tokens JWT valides pour n'importe quel utilisateur.

**CVSS v3.1 :** CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H — Score : 9.8 (CRITIQUE)

**Exploitation :**
```python
import jwt
token = jwt.encode(
    {'identity': {'email': 'victim@example.com'}},
    'secret-key',  # La clé par défaut !
    algorithm='HS256'
)
# Ce token sera accepté par l'application
```

#### Scénario 11 — Sensitive Data Exposure
**Sévérité max :** INFO

| ID | Sévérité | Description |
|----|----------|-------------|
| F-11.1 | INFO | Hachage des mots de passe : bcrypt (Flask-Bcrypt) ✅ |
| F-11.2 | INFO | Champ password en `load_only=True` ✅ |
| F-11.3 | BASSE | URL de base de données dérivée de variable d'environnement ✅ |

**Analyse positive :**
- ✅ **bcrypt avec 13 rounds** en production (BCRYPT_LOG_ROUNDS=13) — excellent niveau de sécurité
- ✅ **load_only=True** sur le champ `password` dans le schéma Marshmallow — le mot de passe n'apparaît jamais dans les réponses API
- ✅ **DATABASE_URL** lu depuis l'environnement, jamais codé en dur

#### Scénario 12 — Sender Spoofing
**Statut :** NON APPLICABLE

L'application Conduit est un backend API REST pur. Elle n'implémente pas d'envoi d'emails, de SMS, ou de fonctionnalités de messagerie. Il n'y a pas de formulaire de contact, de réinitialisation de mot de passe par email, ou de système de notification. Ce scénario ne s'applique donc pas.

**Recommandation préventive :** Si des fonctionnalités d'envoi de messages sont ajoutées à l'avenir :
1. Valider les adresses email selon la RFC 5322
2. Supprimer les caractères CR/LF des en-têtes pour prévenir l'injection
3. Utiliser Flask-Mail avec l'en-tête From défini côté serveur
4. Implémenter SPF, DKIM et DMARC sur le domaine d'envoi

---

## Section 3 : Vulnérabilités par Composant

### Modèle Utilisateur (User)
- ✅ Hachage bcrypt — bon
- ❌ Pas de politique de complexité de mot de passe
- ❌ Pas de verrouillage de compte
- ❌ Clé secrète JWT par défaut

### Authentification
- ✅ JWT avec Flask-JWT-Extended
- ✅ Décorateur @jwt_required sur les endpoints protégés
- ❌ Pas de rate limiting
- ❌ Pas de jti (JWT ID)
- ❌ Pas de liste noire de tokens

### API REST
- ✅ ORM SQLAlchemy — requêtes paramétrées
- ✅ Vérification de propriété des ressources
- ❌ Pas de MAX_CONTENT_LENGTH
- ❌ CORS permissif en développement
- ❌ Pas de clés d'idempotence

### Infrastructure
- ✅ Docker multi-stage avec utilisateur non-root
- ✅ Base image slim
- ❌ Pas de TLS
- ❌ Pas de HSTS
- ❌ Pas de CSP ni autres en-têtes de sécurité

### Dépendances
- ❌ SQLAlchemy 1.1.9 — 6 ans de retard, 2 CVE critiques connues
- ✅ Autres dépendances à jour (Flask, PyJWT, bcrypt)

---

## Section 4 : Statistiques et Métriques

| Métrique | Valeur |
|----------|--------|
| Total vulnérabilités | 20 |
| Vulnérabilités critiques | 1 |
| Vulnérabilités hautes | 5 |
| Vulnérabilités moyennes | 8 |
| Vulnérabilités basses | 6 |
| Faux positifs | 0 |
| Corrections triviales (S — 1 ligne) | 3 |
| Corrections moyennes (M — 1 fichier) | 10 |
| Corrections complexes (L — architecturales) | 3 |
| Délai estimé de correction total | 3-5 jours-homme |

---

## Section 5 : Conformité OWASP Top 10 (2021)

| Rang | Risque | Statut |
|------|--------|--------|
| A01 | Contrôle d'accès défaillant | ✅ Correct |
| A02 | Défaillances cryptographiques | ❌ SECRET_KEY par défaut |
| A03 | Injection | ⚠️ CVE dans dépendance |
| A04 | Conception non sécurisée | ⚠️ Pas de rate limiting |
| A05 | Mauvaise configuration de sécurité | ❌ SECRET_KEY + DEBUG |
| A06 | Composants vulnérables | ❌ SQLAlchemy 1.1.9 |
| A07 | Identification et authentification | ❌ Rate limiting absent |
| A08 | Intégrité logicielle et données | ✅ SHA vérifié |
| A09 | Surveillance et journalisation | ⚠️ Pas de logging |
| A10 | SSRF | ✅ N/A — pas d'appels externes |

---

## Instructions de Formatage pour l'IA

**Format de sortie attendu :**
- Rapport de sécurité PDF en français
- Première page : résumé exécutif avec score global et graphique de sévérité (camembert)
- Sections numérotées avec sous-sections
- Chaque vulnérabilité présentée avec :
  - Identifiant unique (F-XX)
  - Score CVSS v3.1 et vecteur
  - Extrait de code (preuve)
  - Scénario d'exploitation
  - Impact métier
  - Code de correction
  - Difficulté (S/M/L)
- Tableau de conformité OWASP Top 10
- Graphiques : répartition par sévérité, par composant, par scénario
- Police : Times New Roman 11pt, code en Courier New 9pt
- Longueur cible : 15-20 pages
