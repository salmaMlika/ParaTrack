

import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import torch.nn.functional as F


class SkinAnalyzer:
    def __init__(self, model_path="skin_issues_best.pth"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Charger le modèle sauvegardé
        checkpoint = torch.load(model_path, map_location=self.device)
        self.classes = checkpoint['classes']
        
        # Reconstruire le modèle
        self.model = models.mobilenet_v3_small(weights=None)
        in_features = self.model.classifier[0].in_features
        self.model.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(in_features, 256),
            nn.Hardswish(),
            nn.Dropout(0.2),
            nn.Linear(256, len(self.classes))
        )
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model = self.model.to(self.device)
        self.model.eval()
        
        # Transformations
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
    
    def predict(self, image_path):
        """Prédit le problème de peau sur une image"""
        img = Image.open(image_path).convert('RGB')
        img_tensor = self.transform(img).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(img_tensor)
            probs = F.softmax(outputs, dim=1)[0]
        
        scores = {cls: float(probs[i]) for i, cls in enumerate(self.classes)}
        predicted = max(scores, key=scores.get)
        
        return {
            'skin_issue': predicted,
            'confidence': round(scores[predicted], 4),
            'scores': scores
        }