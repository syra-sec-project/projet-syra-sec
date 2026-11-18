import torch
import torch.nn as nn

CLASSES = [
    "avion", "automobile", "oiseau", "chat", "cerf",
    "chien", "grenouille", "cheval", "bateau", "camion",
]


class SimpleCNN(nn.Module):
    """CNN de base pour CIFAR-10.

    Entrée : tensor (N, 3, 32, 32), pixels dans [0, 1].
    Sortie : logits (N, 10).
    La normalisation est faite à l'intérieur du modèle.
    """

    def __init__(self):
        super().__init__()
        self.register_buffer(
            "mean", torch.tensor([0.4914, 0.4822, 0.4465]).view(1, 3, 1, 1)
        )
        self.register_buffer(
            "std", torch.tensor([0.2470, 0.2435, 0.2616]).view(1, 3, 1, 1)
        )

        def block(cin, cout):
            return nn.Sequential(
                nn.Conv2d(cin, cout, 3, padding=1),
                nn.BatchNorm2d(cout),
                nn.ReLU(),
                nn.Conv2d(cout, cout, 3, padding=1),
                nn.BatchNorm2d(cout),
                nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Dropout(0.25),
            )

        # 32x32 -> 16x16 -> 8x8 -> 4x4
        self.features = nn.Sequential(block(3, 32), block(32, 64), block(64, 128))
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 4 * 4, 256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, 10),
        )

    def forward(self, x):
        x = (x - self.mean) / self.std
        return self.classifier(self.features(x))


def load_model(path, device="cpu"):
    """Charge les poids et renvoie le modèle en mode évaluation."""
    model = SimpleCNN().to(device)
    model.load_state_dict(torch.load(path, map_location=device))
    model.eval()
    return model


def predict(model, image):
    """image : tensor (3, 32, 32) dans [0, 1].

    Retourne (nom_de_classe, confiance).
    """
    model.eval()
    with torch.no_grad():
        probs = torch.softmax(model(image.unsqueeze(0)), dim=1)[0]
    idx = int(probs.argmax())
    return CLASSES[idx], float(probs[idx])