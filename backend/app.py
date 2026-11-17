import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models import db
from routes import auth_bp

def create_app():
    app = Flask(__name__)

    # Configuration (utilise le fichier .env si présent, sinon des valeurs par défaut)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///syra_dev.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'cle_secrete_super_robuste_pour_le_projet')

    # Initialisation des outils de sécurité et de base de données
    CORS(app) # Autorise les requêtes provenant de React
    db.init_app(app)
    JWTManager(app)

    # Ajout des routes d'authentification avec le préfixe /auth
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Création du fichier de base de données (syra_dev.db) s'il n'existe pas
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    print("🚀 Serveur Flask SYRA démarré sur http://127.0.0.1:5000")
    app.run(debug=True, port=5000)