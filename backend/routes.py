from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True)

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"msg": "Le nom d'utilisateur et le mot de passe sont requis"}), 400

    username = data['username'].strip()
    password = data['password']

    if len(password) < 6:
        return jsonify({"msg": "Le mot de passe doit contenir au moins 6 caractères"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "Cet utilisateur existe déjà"}), 409

    new_user = User(username=username)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "Utilisateur créé avec succès"}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"msg": "Identifiants manquants"}), 400

    username = data['username'].strip()
    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(data['password']):
        return jsonify({"msg": "Nom d'utilisateur ou mot de passe incorrect"}), 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role}
    )

    return jsonify(
        access_token=access_token,
        user={
            "id": user.id,
            "username": user.username,
            "role": user.role
        }
    ), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    user = db.session.get(User, int(current_user_id))

    if not user:
        return jsonify({"msg": "Utilisateur introuvable"}), 404

    return jsonify(
        id=user.id,
        username=user.username,
        role=user.role
    ), 200