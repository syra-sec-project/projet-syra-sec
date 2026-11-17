from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from models import db, User

# Création du module de routes
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Vérification des données reçues
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"msg": "Le nom d'utilisateur et le mot de passe sont requis"}), 400

    # Vérification si l'utilisateur existe déjà
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"msg": "Cet utilisateur existe déjà"}), 409

    # Création et sauvegarde du nouvel utilisateur
    new_user = User(username=data['username'])
    new_user.set_password(data['password'])

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "Utilisateur créé avec succès"}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"msg": "Identifiants manquants"}), 400

    user = User.query.filter_by(username=data['username']).first()

    # Vérification du mot de passe
    if not user or not user.check_password(data['password']):
        return jsonify({"msg": "Nom d'utilisateur ou mot de passe incorrect"}), 401

    # Création du jeton d'accès valide pour ce login
    access_token = create_access_token(identity=str(user.id))
    return jsonify(access_token=access_token, username=user.username), 200