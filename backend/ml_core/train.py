import os

import torch
import torch.nn as nn
import torchvision
import torchvision.transforms as T
from torch.utils.data import DataLoader

try:
    from .model import SimpleCNN
except ImportError:  # lancement direct du fichier
    from model import SimpleCNN

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA_DIR = os.path.join(ROOT, "data")
WEIGHTS = os.path.join(HERE, "weights", "baseline_cifar10.pt")


def get_loaders(batch_size=128):
    """Pas de Normalize ici : la normalisation est dans le modèle."""
    train_tf = T.Compose([
        T.RandomCrop(32, padding=4),
        T.RandomHorizontalFlip(),
        T.ToTensor(),
    ])
    test_tf = T.ToTensor()
    train = torchvision.datasets.CIFAR10(
        DATA_DIR, train=True, download=True, transform=train_tf
    )
    test = torchvision.datasets.CIFAR10(
        DATA_DIR, train=False, download=True, transform=test_tf
    )
    return (
        DataLoader(train, batch_size, shuffle=True, num_workers=0),
        DataLoader(test, batch_size, shuffle=False, num_workers=0),
    )


def evaluate(model, loader, device="cpu"):
    """Accuracy (%) sur des données propres."""
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            correct += (model(x).argmax(1) == y).sum().item()
            total += y.size(0)
    return 100 * correct / total


def train(epochs=12, lr=1e-3):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("Device :", device)
    train_loader, test_loader = get_loaders()
    model = SimpleCNN().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        model.train()
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            loss_fn(model(x), y).backward()
            opt.step()
        acc = evaluate(model, test_loader, device)
        print(f"Epoch {epoch + 1}/{epochs} - accuracy test : {acc:.2f}%")

    os.makedirs(os.path.dirname(WEIGHTS), exist_ok=True)
    torch.save(model.state_dict(), WEIGHTS)
    print("Poids sauvegardés dans", WEIGHTS)


if __name__ == "__main__":
    train()