import json
import random
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from models import db, Experiment

api_bp = Blueprint('api', __name__)

CIFAR10_CLASSES = [
    "airplane", "automobile", "bird", "cat", "deer",
    "dog", "frog", "horse", "ship", "truck"
]
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def _is_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _extract_image_and_params():
    """
    Accepte soit un upload multipart/form-data (champ 'image'),
    soit un JSON contenant 'image_base64' ou 'image_name'.
    Retourne (image_name, params_dict, error_response).
    """
    if request.content_type and 'multipart/form-data' in request.content_type:
        if 'image' not in request.files:
            return None, None, (jsonify({"msg": "Champ fichier 'image' manquant."}), 400)

        file = request.files['image']
        if not file.filename:
            return None, None, (jsonify({"msg": "Aucun fichier sélectionné."}), 400)

        if not _is_allowed_file(file.filename):
            return None, None, (jsonify({"msg": "Format non autorisé. Utilisez PNG ou JPG."}), 400)

        filename = secure_filename(file.filename)
        params = request.form.to_dict()
        return filename, params, None

    data = request.get_json(silent=True)
    if not data:
        return None, None, (jsonify({"msg": "Corps de requête JSON ou multipart/form-data requis."}), 400)

    if not data.get('image_base64') and not data.get('image_name'):
        return None, None, (jsonify({"msg": "Fournissez 'image_base64' ou 'image_name'."}), 400)

    filename = secure_filename(data.get('image_name', 'uploaded_image.png'))
    if not _is_allowed_file(filename):
        return None, None, (jsonify({"msg": "Extension d'image non autorisée (PNG/JPG uniquement)."}), 400)

    return filename, data, None


@api_bp.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    user_id = int(get_jwt_identity())
    image_name, params, error = _extract_image_and_params()
    if error:
        return error

    # TODO (Équipe IA) : Remplacer ce mock par l'appel au vrai modèle CNN CIFAR-10
    predicted_class = random.choice(CIFAR10_CLASSES)
    confidence = round(random.uniform(0.82, 0.99), 4)

    experiment = Experiment(
        user_id=user_id,
        action_type='predict',
        image_name=image_name,
        parameters=json.dumps({"mode": "mock"}),
        original_prediction=predicted_class,
        final_prediction=predicted_class,
        confidence=confidence,
        status='success'
    )
    db.session.add(experiment)
    db.session.commit()

    return jsonify({
        "experiment_id": experiment.id,
        "image_name": image_name,
        "predicted_class": predicted_class,
        "confidence": confidence,
        "is_mock": True
    }), 200


@api_bp.route('/attack', methods=['POST'])
@jwt_required()
def attack():
    user_id = int(get_jwt_identity())
    image_name, params, error = _extract_image_and_params()
    if error:
        return error

    attack_type = params.get('attack_type', 'square_attack')
    try:
        epsilon = float(params.get('epsilon', 0.05))
        n_queries = int(params.get('n_queries', 1000))
    except (ValueError, TypeError):
        return jsonify({"msg": "Les paramètres 'epsilon' (float) et 'n_queries' (int) sont invalides."}), 400

    if not (0.0 < epsilon <= 1.0) or n_queries <= 0:
        return jsonify({"msg": "'epsilon' doit être dans ]0, 1] et 'n_queries' > 0."}), 400

    # TODO (Équipe IA) : Remplacer ce mock par le script Square Attack
    original_class = "cat"
    adversarial_class = "dog"
    adversarial_confidence = round(random.uniform(0.70, 0.95), 4)
    queries_used = random.randint(50, min(n_queries, 600))

    attack_params = {
        "attack_type": attack_type,
        "epsilon": epsilon,
        "n_queries": n_queries,
        "queries_used": queries_used
    }

    experiment = Experiment(
        user_id=user_id,
        action_type='attack',
        image_name=image_name,
        parameters=json.dumps(attack_params),
        original_prediction=original_class,
        final_prediction=adversarial_class,
        confidence=adversarial_confidence,
        status='success'
    )
    db.session.add(experiment)
    db.session.commit()

    return jsonify({
        "experiment_id": experiment.id,
        "image_name": image_name,
        "attack_type": attack_type,
        "epsilon": epsilon,
        "queries_used": queries_used,
        "original_prediction": original_class,
        "adversarial_prediction": adversarial_class,
        "confidence": adversarial_confidence,
        "attack_success": original_class != adversarial_class,
        "adversarial_image_base64": None,  # Sera rempli par le module IA
        "is_mock": True
    }), 200


@api_bp.route('/defend', methods=['POST'])
@jwt_required()
def defend():
    user_id = int(get_jwt_identity())
    image_name, params, error = _extract_image_and_params()
    if error:
        return error

    defense_type = params.get('defense_type', 'randomized_smoothing')
    try:
        sigma = float(params.get('sigma', 0.25))
        n_samples = int(params.get('n_samples', 100))
    except (ValueError, TypeError):
        return jsonify({"msg": "Les paramètres 'sigma' (float) et 'n_samples' (int) sont invalides."}), 400

    if sigma <= 0 or n_samples <= 0:
        return jsonify({"msg": "'sigma' et 'n_samples' doivent être strictement positifs."}), 400

    # TODO (Équipe IA) : Remplacer ce mock par le script Randomized Smoothing
    original_adversarial_class = "dog"
    defended_class = "cat"
    confidence = round(random.uniform(0.85, 0.98), 4)
    certified_radius = round(sigma * random.uniform(0.8, 1.5), 4)

    defense_params = {
        "defense_type": defense_type,
        "sigma": sigma,
        "n_samples": n_samples,
        "certified_radius": certified_radius
    }

    experiment = Experiment(
        user_id=user_id,
        action_type='defend',
        image_name=image_name,
        parameters=json.dumps(defense_params),
        original_prediction=original_adversarial_class,
        final_prediction=defended_class,
        confidence=confidence,
        status='success'
    )
    db.session.add(experiment)
    db.session.commit()

    return jsonify({
        "experiment_id": experiment.id,
        "image_name": image_name,
        "defense_type": defense_type,
        "sigma": sigma,
        "n_samples": n_samples,
        "defended_prediction": defended_class,
        "confidence": confidence,
        "certified_radius": certified_radius,
        "is_mock": True
    }), 200


@api_bp.route('/history', methods=['GET'])
@jwt_required()
def history():
    user_id = int(get_jwt_identity())
    limit = request.args.get('limit', default=20, type=int)
    limit = max(1, min(limit, 100))

    experiments = (
        Experiment.query
        .filter_by(user_id=user_id)
        .order_by(Experiment.created_at.desc())
        .limit(limit)
        .all()
    )

    return jsonify({
        "count": len(experiments),
        "history": [exp.to_dict() for exp in experiments]
    }), 200