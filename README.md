SYRA - SYstem for Intelligent Robustness Analysis
Bienvenue sur le dépôt officiel du projet SYRA.
Ce projet est une application web sécurisée développée dans le cadre de notre TP final d'Intelligence Artificielle. Il permet de simuler une attaque adversariale par évasion (FGSM) sur un modèle de classification d'images, puis d'y appliquer une méthode de défense (Entraînement Adversarial).
Périmètre du Projet (Plan Optimisé)
Pour garantir une livraison dans les temps (6 jours) tout en respectant le cahier des charges, le projet se concentre sur :
￼ IA : Un modèle CNN simple (PyTorch), attaqué via FGSM, défendu par Adversarial Training.
￼ Backend & Sécurité : Une API Flask sécurisée avec base de données locale (SQLite) et authentification par JWT.
￼ Frontend : Une interface React pour téléverser une image, l'attaquer et observer la défense en direct.
Répartition des Rôles (Équipe de 4)
Chaque membre est responsable d'un lot précis pour éviter de se bloquer mutuellement.
1. Membre 1 (Base IA & Data) : Création du modèle CNN de base, chargement des données (CIFAR-10 ou MNIST), entraînement initial et évaluation (Accuracy).
2. Membre 2 (Sécurité IA) : Création du script d'attaque (FGSM) pour tromper le modèle, et du script de défense (ré-entraînement robuste).
3. Membre 3 (Backend Flask & Auth) : Création de l'API web, gestion de la base de données, sécurisation des routes (Login/JWT) et exécution du code IA.
4. Membre 4 (Frontend React) : Développement de l'interface utilisateur, des pages de connexion, et du tableau de bord d'attaque interactif.
Technologies Utilisées
￼ Machine Learning : Python 3.11+, PyTorch, Torchattacks
￼ API & Backend : Flask, Flask-JWT-Extended, SQLAlchemy (SQLite)
￼ Frontend : React.js (Vite), Axios
   Guide d'Installation Local
Pour travailler sur le projet, chaque membre doit cloner ce dépôt et installer les environnements.
1. Cloner le projet
2. Lancer le Backend (Flask & IA)
Ouvrez un terminal et placez-vous à la racine du projet :
3. Lancer le Frontend (React)
Ouvrez un second terminal, placez-vous à la racine du projet :
Règles de Collaboration Git (TRÈS IMPORTANT)
Pour éviter de détruire le projet ou de passer des nuits à régler des conflits Git, tout le monde doit respecter ce flux de travail :
 Fichiers Interdits
Grâce au fichier ⁠.gitignore⁠, certains fichiers ne seront pas envoyés. Ne forcez jamais l'envoi des éléments suivants :
￼ Le fichier ⁠.env⁠ (qui contient vos mots de passe locaux).
￼ Le dossier ⁠node_modules/⁠ (il pèse très lourd).
￼ Le dossier ⁠.venv/⁠ (environnement Python propre à votre PC).
￼ Les modèles IA (⁠*.pt⁠, ⁠*.pth⁠) : mettez-les sur un Google Drive partagé et téléchargez-les localement.
