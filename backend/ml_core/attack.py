# backend/ml_core/attack.py
import torch
import torchattacks

def fgsm_attack(model, image, label, epsilon=0.1):
    """
    image : tenseur (1, C, H, W), valeurs dans [0, 1]
    label : tenseur (1,) avec la vraie classe
    Retourne : image adversariale, prédiction avant, prédiction après
    """
    model.eval()
    atk = torchattacks.FGSM(model, eps=epsilon)
    adv_image = atk(image, label)

    with torch.no_grad():
        pred_before = model(image).argmax(dim=1).item()
        pred_after = model(adv_image).argmax(dim=1).item()

    return adv_image, pred_before, pred_after

def get_perturbation(image, adv_image):
    """Bruit ajouté, amplifié pour être visible à l'affichage."""
    noise = (adv_image - image)
    return (noise * 10 + 0.5).clamp(0, 1)
