# Prompt : Plan de Remédiation Priorisé — Pipeline DevSecOps

> **Instructions pour l'IA (GLM 5.2) :** Générez un plan de remédiation détaillé en français, classé par priorité (P0-P3), avec pour chaque vulnérabilité : la correction exacte (code), le temps estimé, et la vérification.

---

## Contexte

Ce document présente le plan de remédiation pour les 20 vulnérabilités découvertes dans l'application **Conduit** (https://github.com/gothinkster/flask-realworld-example-app).

**Principe :** Chaque correction est priorisée selon la formule :
**Priorité = Sévérité × Exploitabilité × Impact métier**

---

## Définitions des Priorités

| Priorité | Délai | Critère |
|----------|-------|---------|
| **P0 — Immédiat** | Maintenant | Bloque le déploiement en production |
| **P1 — Ce sprint** | 1-2 semaines | Risque élevé d'exploitation |
| **P2 — Prochain sprint** | 2-4 semaines | Réduit significativement la surface d'attaque |
| **P3 — Backlog** | Quand possible | Amélioration continue, défense en profondeur |

---

## P0 — Immédiat (1 vulnérabilité)

### P0-1 : Supprimer la valeur par défaut de SECRET_KEY

- **Vulnérabilité liée :** F-10.1 (CRITIQUE — CVSS 9.8)
- **Fichier :** `conduit/settings.py:10`
- **Temps estimé :** 5 minutes
- **Difficulté :** S (3 lignes)

**Code actuel (vulnérable) :**
```python
SECRET_KEY=os.env...ET', 'secret-key')  # TODO: Change me
```

**Code corrigé :**
```python
SECRET_KEY=os.env...')
if not SECRET_KEY:
    raise RuntimeError(
        "CONDUIT_SECRET environment variable must be set. "
        "Generate a strong key: python -c 'import secrets; print(secrets.token_hex(32))'"
    )
```

**Vérification :**
```bash
# Sans la variable d'environnement, l'application doit refuser de démarrer
unset CONDUIT_SECRET
python -c "from conduit.app import create_app; create_app()"  # Doit lever RuntimeError

# Avec une clé valide, l'application démarre normalement
export CONDUIT_SECRET=$(python -c 'import secrets; print(secrets.token_hex(32))')
python -c "from conduit.app import create_app; app = create_app(); print('OK')"
```

---

## P1 — Ce Sprint (3 vulnérabilités)

### P1-1 : Mettre à jour SQLAlchemy de 1.1.9 vers ≥ 2.0

- **Vulnérabilités liées :** F-1.1 (HAUTE — CVE-2019-7164), F-1.2 (HAUTE — CVE-2019-7548)
- **Fichier :** `requirements/prod.txt`
- **Temps estimé :** 2 heures (mise à jour + tests de régression)
- **Difficulté :** M (changements d'API entre 1.x et 2.x)

**Code actuel :**
```
SQLAlchemy==1.1.9
```

**Code corrigé :**
```
SQLAlchemy>=2.0.0,<3.0.0
```

**Adaptations nécessaires :**
```python
# Avant (SQLAlchemy 1.x)
Article.query.filter_by(slug=slug).first()

# Après (SQLAlchemy 2.x — utilise db.session)
from conduit.database import db
db.session.execute(db.select(Article).filter_by(slug=slug)).scalar_one_or_none()
```

**Points de vigilance :**
- La méthode `.query` est dépréciée en 2.0 — utiliser `db.session.execute(db.select(...))`
- `autocommit` a changé de comportement
- Certains types de colonnes peuvent nécessiter des ajustements

**Vérification :**
```bash
pip install SQLAlchemy>=2.0
pip-audit -r requirements/prod.txt  # Doit retourner 0 vulnérabilité pour SQLAlchemy
pytest tests/ -v  # Tous les tests doivent passer
```

### P1-2 : Ajouter un rate limiting sur l'authentification

- **Vulnérabilités liées :** F-3.1 (HAUTE), F-9.1 (HAUTE)
- **Fichiers :** `requirements/prod.txt`, `conduit/app.py`, `conduit/user/views.py`
- **Temps estimé :** 1 heure
- **Difficulté :** M

**Étape 1 — Ajouter la dépendance :**
```
# requirements/prod.txt — ajouter :
Flask-Limiter>=3.0
```

**Étape 2 — Configurer Flask-Limiter dans app.py :**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def create_app():
    app = Flask(__name__)
    
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",
    )
    # ...
    return app
```

**Étape 3 — Appliquer le rate limit sur le login :**
```python
# conduit/user/views.py
from flask_limiter import Limiter

@blueprint.route('/api/users/login', methods=('POST',))
@limiter.limit("5 per minute")  # ← Ajouter cette ligne
@jwt_optional
@use_kwargs(user_schema)
@marshal_with(user_schema)
def login_user(email, password, **kwargs):
    # ... code existant
```

**Vérification :**
```bash
# Envoyer 6 requêtes de connexion en moins d'une minute
for i in $(seq 1 6); do
    curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8080/api/users/login \
        -H "Content-Type: application/json" \
        -d '{"user":{"email":"test@test.com","password":"wrong"}}'
done
# La 6ème requête doit retourner HTTP 429 (Too Many Requests)
```

### P1-3 : Déployer un reverse proxy avec TLS

- **Vulnérabilités liées :** F-2.1 (HAUTE), F-2.2 (MOYENNE)
- **Fichier :** `docker/nginx.conf` (nouveau), `docker/docker-compose.yml`
- **Temps estimé :** 3 heures
- **Difficulté :** M

**Étape 1 — Créer la configuration Nginx (`docker/nginx.conf`) :**
```nginx
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;

    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location / {
        proxy_pass http://app:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Étape 2 — Ajouter Nginx au docker-compose.yml :**
```yaml
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - app
    networks:
      - conduit-net
```

**Pour la production :** Remplacer les certificats auto-signés par Let's Encrypt (gratuit).

---

## P2 — Prochain Sprint (5 vulnérabilités)

### P2-1 : Politique de complexité de mot de passe

- **Vulnérabilité :** F-3.2 (MOYENNE)
- **Temps :** 30 minutes
- **Difficulté :** S

```python
# conduit/user/views.py — dans register_user()
import re

def validate_password(password):
    if len(password) < 8:
        raise InvalidUsage.custom_error(
            'Le mot de passe doit contenir au moins 8 caractères.'
        )
    if not re.search(r'[A-Z]', password):
        raise InvalidUsage.custom_error(
            'Le mot de passe doit contenir au moins une majuscule.'
        )
    if not re.search(r'[a-z]', password):
        raise InvalidUsage.custom_error(
            'Le mot de passe doit contenir au moins une minuscule.'
        )
    if not re.search(r'[0-9]', password):
        raise InvalidUsage.custom_error(
            'Le mot de passe doit contenir au moins un chiffre.'
        )
    if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
        raise InvalidUsage.custom_error(
            'Le mot de passe doit contenir au moins un caractère spécial.'
        )

# Dans register_user() :
def register_user(username, password, email, **kwargs):
    validate_password(password)  # ← Ajouter
    # ... reste du code
```

### P2-2 : Verrouillage de compte après échecs

- **Vulnérabilité :** F-3.3 (MOYENNE)
- **Temps :** 1 heure
- **Difficulté :** M

```python
# Ajouter au modèle User
class User(db.Model):
    # ... champs existants
    login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

# Dans login_user() :
def login_user(email, password, **kwargs):
    user = User.query.filter_by(email=email).first()
    
    if user and user.locked_until and user.locked_until > dt.datetime.utcnow():
        raise InvalidUsage.custom_error(
            'Compte verrouillé. Réessayez dans 15 minutes.'
        )
    
    if user is not None and user.check_password(password):
        user.login_attempts = 0
        user.locked_until = None
        user.save()
        user.token = create_access_token(identity=user, fresh=True)
        return user
    else:
        if user:
            user.login_attempts += 1
            if user.login_attempts >= 5:
                user.locked_until = dt.datetime.utcnow() + dt.timedelta(minutes=15)
            user.save()
        raise InvalidUsage.user_not_found()
```

### P2-3 : Ajouter l'en-tête HSTS

- **Vulnérabilité :** F-2.2 (MOYENNE)
- **Fichier :** `conduit/app.py`
- **Temps :** 10 minutes
- **Difficulté :** S

```python
# conduit/app.py — dans create_app()
@app.after_request
def add_security_headers(response):
    response.headers['Strict-Transport-Security'] = \
        'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response
```

### P2-4 : Ajouter jti aux tokens JWT

- **Vulnérabilité :** F-5.1 (MOYENNE)
- **Temps :** 30 minutes
- **Difficulté :** S

```python
# conduit/user/views.py
import uuid

def register_user(username, password, email, **kwargs):
    # ...
    userprofile.user.token = create_access_token(
        identity=userprofile.user,
        additional_claims={'jti': str(uuid.uuid4())}  # ← Ajouter
    )
```

### P2-5 : Configurer MAX_CONTENT_LENGTH

- **Vulnérabilités :** F-7.1 (MOYENNE), F-8.1 (MOYENNE)
- **Temps :** 5 minutes
- **Difficulté :** S

```python
# conduit/settings.py — dans Config
class Config(object):
    # ... existant
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1 MB
```

---

## P3 — Backlog (5 vulnérabilités)

### P3-1 : Réduire l'expiration JWT en dev
```python
# conduit/settings.py
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)  # Au lieu de 10**6 secondes
```

### P3-2 : Implémenter une liste noire de tokens
Utiliser Redis pour stocker les jti révoqués. Vérifier à chaque requête authentifiée.

### P3-3 : Ajouter des clés d'idempotence
Exiger `X-Idempotency-Key` sur POST/PUT/DELETE. Stocker la clé + réponse pendant 24h.

### P3-4 : Restreindre CORS en production
```python
CORS_ORIGIN_WHITELIST = [
    'https://votre-frontend-prod.com',
]
```

### P3-5 : Ajouter Content-Security-Policy
```python
response.headers['Content-Security-Policy'] = \
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
```

---

## Résumé du Plan de Remédiation

| Priorité | Nombre | Temps total estimé | Impact |
|----------|--------|--------------------|--------|
| P0 | 1 | 5 min | Supprime la vulnérabilité critique |
| P1 | 3 | 6 heures | Corrige 5 vulnérabilités HAUTES |
| P2 | 5 | 3 heures | Corrige 5 vulnérabilités MOYENNES |
| P3 | 5 | 4 heures | Améliore la posture de sécurité |
| **Total** | **14** | **~13 heures** | **Score de sécurité : 55 → 90/100** |

---

## Instructions de Formatage pour l'IA

**Format de sortie attendu :**
- Document PDF en français, format « plan d'action »
- Une page par priorité (P0, P1, P2, P3)
- Chaque correction avec : code AVANT/APRÈS, temps estimé, difficulté, vérification
- Code colorisé (rouge = code vulnérable, vert = code corrigé)
- Tableau récapitulatif en fin de document
- Police : Times New Roman 11pt, code en Courier New 9pt
- Longueur cible : 8-10 pages
