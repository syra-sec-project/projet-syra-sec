import base64
import binascii
import io
import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image, UnidentifiedImageError
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from models import db, Experiment
from ml_core.model import CLASSES, load_model, predict as ml_predict
from ml_core.attack import fgsm_attack, get_perturbation

api_bp = Blueprint('api', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
WEIGHTS_DIR = Path(__file__).resolve().parent / 'ml_core' / 'weights'
BASELINE_WEIGHTS = WEIGHTS_DIR / 'baseline_cifar10.pt'
ROBUST_WEIGHTS = WEIGHTS_DIR / 'robust_cifar10.pt'

# Cache en mémoire pour ne charger les modèles PyTorch qu'une seule fois
_baseline_model = None
_robust_model = None


def _get_baseline_model():
    global _baseline_model
    if _baseline_model is None:
        if not BASELINE_WEIGHTS.exists():
            raise FileNotFoundError(f"Poids introuvables : {BASELINE_WEIGHTS}")
        _baseline_model = load_model(str(BASELINE_WEIGHTS), device="cpu")
    return _baseline_model


def _get_robust_model():
    global _robust_model
    if _robust_model is None:
        if not ROBUST_WEIGHTS.exists():
            return None
        _robust_model = load_model(str(ROBUST_WEIGHTS), device="cpu")
    return _robust_model


def _is_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _bytes_to_tensor(image_bytes):
    """Convertit des octets image (PNG/JPG) en tenseur (3, 32, 32) dans [0, 1]."""
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    img = img.resize((32, 32), Image.Resampling.BILINEAR)
    arr = np.array(img, dtype=np.float32) / 255.0
    return torch.from_numpy(arr).permute(2, 0, 1)


def _tensor_to_base64(tensor):
    """Convertit un tenseur (1, 3, 32, 32) ou (3, 32, 32) dans [0, 1] en PNG Base64."""
    if tensor.dim() == 4:
        tensor = tensor.squeeze(0)
    arr = (tensor.detach().cpu().clamp(0, 1).permute(1, 2, 0).numpy() * 255).astype(np.uint8)
    img = Image.fromarray(arr)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def _extract_image_tensor_and_params():
    """
    Accepte soit un upload multipart/form-data (champ 'image'),
    soit un JSON contenant 'image_base64' (avec ou sans préfixe data:image/...).
    Retourne (image_name, tensor_3d, params_dict, error_response).
    """
    if request.content_type and 'multipart/form-data' in request.content_type:
        if 'image' not in request.files:
            return None, None, None, (jsonify({"msg": "Champ fichier 'image' manquant."}), 400)

        file = request.files['image']
        if not file.filename:
            return None, None, None, (jsonify({"msg": "Aucun fichier sélectionné."}), 400)

        if not _is_allowed_file(file.filename):
            return None, None, None, (jsonify({"msg": "Format non autorisé. Utilisez PNG ou JPG."}), 400)

        filename = secure_filename(file.filename)
        image_bytes = file.read()
        params = request.form.to_dict()
    else:
        data = request.get_json(silent=True)
        if not data:
            return None, None, None, (jsonify({"msg": "Requête JSON ou multipart/form-data requise."}), 400)

        b64_str = data.get('image_base64')
        if not b64_str:
            return None, None, None, (jsonify({"msg": "Champ 'image_base64' requis pour l'inférence."}), 400)

        filename = secure_filename(data.get('image_name', 'uploaded_image.png'))
        if not _is_allowed_file(filename):
            return None, None, None, (jsonify({"msg": "Extension d'image non autorisée (PNG/JPG uniquement)."}), 400)

        # Supprime un éventuel préfixe Data URL envoyé par React ("data:image/png;base64,...")
        if ',' in b64_str:
            b64_str = b64_str.split(',', 1)[1]

        try:
            image_bytes = base64.b64decode(b64_str, validate=True)
        except (binascii.Error, ValueError):
            return None, None, None, (jsonify({"msg": "Champ 'image_base64' invalide."}), 400)

        params = data

    try:
        tensor_3d = _bytes_to_tensor(image_bytes)
    except (UnidentifiedImageError, OSError, ValueError):
        return None, None, None, (jsonify({"msg": "Fichier image corrompu ou illisible."}), 400)

    return filename, tensor_3d, params, None


def _resolve_label_index(raw_label, model, tensor_3d):
    """
    Si true_label est fourni (index 0-9 ou nom de classe français), le convertit en index.
    Sinon, utilise la prédiction initiale du modèle comme cible à tromper.
    """
    if raw_label is not None and str(raw_label).strip() != '':
        raw_str = str(raw_label).strip().lower()
        if raw_str.isdigit():
            idx = int(raw_str)
            if 0 <= idx < len(CLASSES):
                return idx
        elif raw_str in CLASSES:
            return CLASSES.index(raw_str)
        return None

    predicted_class, _ = ml_predict(model, tensor_3d)
    return CLASSES.index(predicted_class)


@api_bp.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    user_id = int(get_jwt_identity())
    image_name, tensor_3d, params, error = _extract_image_tensor_and_params()
    if error:
        return error

    try:
        model = _get_baseline_model()
        predicted_class, confidence = ml_predict(model, tensor_3d)
        confidence = round(confidence, 4)
    except Exception as e:
        return jsonify({"msg": f"Erreur lors de la prédiction IA : {str(e)}"}), 500

    experiment = Experiment(
        user_id=user_id,
        action_type='predict',
        image_name=image_name,
        parameters=json.dumps({"model": "baseline_cifar10"}),
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
        "classes": CLASSES
    }), 200


@api_bp.route('/attack', methods=['POST'])
@jwt_required()
def attack():
    user_id = int(get_jwt_identity())
    image_name, tensor_3d, params, error = _extract_image_tensor_and_params()
    if error:
        return error

    try:
        epsilon = float(params.get('epsilon', 0.1))
    except (ValueError, TypeError):
        return jsonify({"msg": "Le paramètre 'epsilon' doit être un nombre décimal."}), 400

    if not (0.0 < epsilon <= 1.0):
        return jsonify({"msg": "'epsilon' doit être compris dans ]0, 1]."}), 400

    try:
        model = _get_baseline_model()
        label_idx = _resolve_label_index(params.get('true_label'), model, tensor_3d)
        if label_idx is None:
            return jsonify({"msg": f"'true_label' invalide. Valeurs acceptées : 0-9 ou {CLASSES}."}), 400

        img_batch = tensor_3d.unsqueeze(0)  # (1, 3, 32, 32)
        label_tensor = torch.tensor([label_idx], dtype=torch.long)

        adv_image, pred_before_idx, pred_after_idx = fgsm_attack(
            model, img_batch, label_tensor, epsilon=epsilon
        )
        perturbation = get_perturbation(img_batch, adv_image)

        original_class = CLASSES[pred_before_idx]
        adversarial_class = CLASSES[pred_after_idx]
        _, adv_confidence = ml_predict(model, adv_image.squeeze(0))
        adv_confidence = round(adv_confidence, 4)

        adv_b64 = _tensor_to_base64(adv_image)
        perturbation_b64 = _tensor_to_base64(perturbation)
    except Exception as e:
        return jsonify({"msg": f"Erreur lors de l'attaque FGSM : {str(e)}"}), 500

    attack_params = {
        "attack_type": "fgsm",
        "epsilon": epsilon,
        "target_label": CLASSES[label_idx]
    }

    experiment = Experiment(
        user_id=user_id,
        action_type='attack',
        image_name=image_name,
        parameters=json.dumps(attack_params),
        original_prediction=original_class,
        final_prediction=adversarial_class,
        confidence=adv_confidence,
        status='success'
    )
    db.session.add(experiment)
    db.session.commit()

    return jsonify({
        "experiment_id": experiment.id,
        "image_name": image_name,
        "attack_type": "fgsm",
        "epsilon": epsilon,
        "original_prediction": original_class,
        "adversarial_prediction": adversarial_class,
        "confidence": adv_confidence,
        "attack_success": original_class != adversarial_class,
        "adversarial_image_base64": adv_b64,
        "perturbation_image_base64": perturbation_b64
    }), 200


@api_bp.route('/defend', methods=['POST'])
@jwt_required()
def defend():
    user_id = int(get_jwt_identity())
    image_name, tensor_3d, params, error = _extract_image_tensor_and_params()
    if error:
        return error

    robust_model = _get_robust_model()
    if robust_model is None:
        return jsonify({
            "msg": (
                "Le modèle défendu (robust_cifar10.pt) n'est pas encore disponible. "
                "L'équipe IA doit exécuter adversarial_training() et sauvegarder les poids "
                "dans backend/ml_core/weights/robust_cifar10.pt."
            ),
            "defense_model_ready": False
        }), 503

    try:
        baseline_model = _get_baseline_model()
        baseline_class, baseline_conf = ml_predict(baseline_model, tensor_3d)
        defended_class, defended_conf = ml_predict(robust_model, tensor_3d)

        baseline_conf = round(baseline_conf, 4)
        defended_conf = round(defended_conf, 4)
    except Exception as e:
        return jsonify({"msg": f"Erreur lors de l'inférence défendue : {str(e)}"}), 500

    defense_params = {
        "defense_type": "adversarial_training",
        "baseline_prediction": baseline_class,
        "baseline_confidence": baseline_conf
    }

    experiment = Experiment(
        user_id=user_id,
        action_type='defend',
        image_name=image_name,
        parameters=json.dumps(defense_params),
        original_prediction=baseline_class,
        final_prediction=defended_class,
        confidence=defended_conf,
        status='success'
    )
    db.session.add(experiment)
    db.session.commit()

    return jsonify({
        "experiment_id": experiment.id,
        "image_name": image_name,
        "defense_type": "adversarial_training",
        "baseline_prediction": baseline_class,
        "baseline_confidence": baseline_conf,
        "defended_prediction": defended_class,
        "confidence": defended_conf,
        "defense_model_ready": True
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