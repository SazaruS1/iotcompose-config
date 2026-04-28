# Guide Complet : Push du Dossier iotcompose sur GitHub

## Préalable
- Repo privé créé sur GitHub : `iotcompose-config`
- SSH configuré avec GitHub
- Dossier iotcompose en local : `c:\Users\inimu\Desktop\Travaux\Fac\Stage\Archives_Pihole\Pihole_Archive\iotcompose`

---

## ÉTAPES

### 📍 **ÉTAPE 1 : Naviguer vers le dossier**

```powershell
cd "c:\Users\inimu\Desktop\Travaux\Fac\Stage\Archives_Pihole\Pihole_Archive\iotcompose"
```

**Vérifier que vous êtes au bon endroit :**
```powershell
pwd
```

Output attendu :
```
Path
----
C:\Users\inimu\Desktop\Travaux\Fac\Stage\Archives_Pihole\Pihole_Archive\iotcompose
```

---

### 📍 **ÉTAPE 2 : Initialiser le repo Git (si pas déjà fait)**

```powershell
git init
```

Output attendu :
```
Initialized empty Git repository in C:.../iotcompose/.git/
```

> **Note :** Si le dossier `.git` existe déjà, vous pouvez ignorer cette étape.

---

### 📍 **ÉTAPE 3 : Créer/Vérifier le fichier .gitignore**

**Créer le fichier .gitignore pour exclure les fichiers sensibles :**

```powershell
# Créer le fichier
New-Item -Path ".gitignore" -Force
```

**Ajouter le contenu (ouvrir le fichier dans un éditeur) :**
```
# Fichiers de configuration sensibles
etc-pihole/cli_pw
etc-pihole/dhcp.leases
etc-pihole/*.pem
etc-pihole/tls.*
etc-dnsmasq.d/

# Fichiers de données et backups
etc-pihole/config_backups/
etc-pihole/gravity_backups/
homeassistant/
ENV/

# Cache Python
__pycache__/
*.pyc
*.log
```

---

### 📍 **ÉTAPE 4 : Vérifier l'état du repo**

```powershell
git status
```

Output attendu : Affiche les fichiers non stagés et non trackés.

---

### 📍 **ÉTAPE 5 : Ajouter tous les fichiers**

```powershell
git add .
```

**Vérifier :**
```powershell
git status
```

Output attendu : Les fichiers doivent être verts (staged).

---

### 📍 **ÉTAPE 6 : Configurer Git (première fois seulement)**

```powershell
git config user.email "votre.email@example.com"
git config user.name "Votre Nom"
```

> Remplacez par vos informations réelles.

---

### 📍 **ÉTAPE 7 : Faire un commit**

```powershell
git commit -m "Initial commit: Complete iotcompose setup with Docker, PiHole, ChirpStack, GYSMO"
```

Output attendu :
```
[main ...] Initial commit: Complete iotcompose setup...
 XXX files changed, XXXXX insertions(+)
```

---

### 📍 **ÉTAPE 8 : Ajouter la remote GitHub**

```powershell
git remote add origin git@github.com:SazaruS1/iotcompose-config.git
```

**Vérifier la remote :**
```powershell
git remote -v
```

Output attendu :
```
origin  git@github.com:SazaruS1/iotcompose-config.git (fetch)
origin  git@github.com:SazaruS1/iotcompose-config.git (push)
```

> **Si la remote existe déjà et pointe vers le mauvais URL :**
> ```powershell
> git remote set-url origin git@github.com:SazaruS1/iotcompose-config.git
> ```

---

### 📍 **ÉTAPE 9 : Renommer la branche en "main" (optionnel mais recommandé)**

```powershell
git branch -M main
```

---

### 📍 **ÉTAPE 10 : Pousser le code sur GitHub**

```powershell
git push -u origin main
```

> **À la première connexion SSH :**
> - Vous verrez une demande de confirmation de la clé SSH de GitHub
> - Tapez `yes` et appuyez sur Entrée

Output attendu :
```
Enumerating objects: 500+, done.
Counting objects: 100% (500+), done.
...
* [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

---

### 📍 **ÉTAPE 11 : Vérifier le succès**

```powershell
git status
```

Output attendu :
```
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

---

## ✅ VÉRIFICATION FINALE

**Sur le terminal :**
```powershell
git log --oneline
```

**Sur GitHub :**
- Aller sur https://github.com/SazaruS1/iotcompose-config
- Vérifier que le repo est marqué **Private** ✅
- Vérifier que tous les fichiers sont présents ✅

---

## 🚨 COMMANDES D'UNE LIGNE (Pour les push suivants)

Une fois le premier push fait, pour les futurs changements :

```powershell
cd "c:\Users\inimu\Desktop\Travaux\Fac\Stage\Archives_Pihole\Pihole_Archive\iotcompose" ; git add . ; git commit -m "Votre message de commit" ; git push
```

---

## 📝 RÉSUMÉ DES COMMANDES CLÉS

| Étape | Commande |
|-------|----------|
| Naviguer | `cd "path/to/iotcompose"` |
| Initialiser | `git init` |
| Ajouter fichiers | `git add .` |
| Vérifier état | `git status` |
| Commiter | `git commit -m "message"` |
| Ajouter remote | `git remote add origin URL` |
| Pousser | `git push -u origin main` |

