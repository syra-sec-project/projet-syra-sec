import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models import db
from routes import auth_bp
from routes_api import api_bp

# Charge le fichier .env situé à la racine du projet
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def create_app():
    app = Flask(__name__)

    # Configuration depuis .env
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///syra_dev.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'cle_dev_a_remplacer_dans_env')
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Limite d'upload : 5 Mo

    # Durée d'expiration du token JWT (2 heures par défaut)
    expires_hours = int(os.environ.get('JWT_EXPIRES_HOURS', 2))
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=expires_hours)

    # Initialisation des extensions
    CORS(app)
    db.init_app(app)
    jwt = JWTManager(app)

    # Gestion propre des erreurs JWT et upload
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"msg": "Votre session a expiré, veuillez vous reconnecter."}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"msg": "Jeton d'authentification invalide."}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"msg": "Authentification requise (token manquant)."}), 401

    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({"msg": "Fichier trop volumineux (limite : 5 Mo)."}), 413

    # Enregistrement des Blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Création des tables SQLite si inexistantes
    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    print("🚀 Serveur Flask SYRA démarré sur http://127.0.0.1:5000")
    app.run(debug=True, port=5000)