# backend/ml_core/defense.py
import torch
import torch.nn as nn
import torchattacks

def adversarial_training(model, train_loader, epochs=3, epsilon=0.1, lr=0.001, device="cpu"):
    """Ré-entraîne le modèle avec un mélange d'images propres et FGSM."""
    model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()
    atk = torchattacks.FGSM(model, eps=epsilon)

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            adv_images = atk(images, labels)

            optimizer.zero_grad()
            loss = loss_fn(model(images), labels) + loss_fn(model(adv_images), labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"Epoch {epoch+1}/{epochs} - loss: {total_loss/len(train_loader):.4f}")

    return model

def evaluate_robustness(model, test_loader, epsilon=0.1, device="cpu"):
    """Retourne (accuracy propre, accuracy sous attaque)."""
    model.eval()
    atk = torchattacks.FGSM(model, eps=epsilon)
    clean_ok = adv_ok = total = 0
    for images, labels in test_loader:
        images, labels = images.to(device), labels.to(device)
        adv = atk(images, labels)
        with torch.no_grad():
            clean_ok += (model(images).argmax(1) == labels).sum().item()
            adv_ok += (model(adv).argmax(1) == labels).sum().item()
        total += labels.size(0)
    return clean_ok / total, adv_ok / total
