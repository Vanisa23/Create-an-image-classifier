# -*- coding: utf-8 -*-
"""predict.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1y_nmvYNGhbUd75HNTd7Qw0IgossfOoyL
"""

import argparse
import torch
from torchvision import models, transforms
from PIL import Image
import json

def parse_args():
    parser = argparse.ArgumentParser(description="Predict the most likely image class and its associated probability")
    parser.add_argument("image_path", metavar="image_path", type=str, help="Path to the image file")
    parser.add_argument("checkpoint", metavar="checkpoint", type=str, help="Path to the checkpoint file")
    parser.add_argument("--top_k", type=int, default=1, help="Number of top classes to be displayed")
    parser.add_argument("--category_names", type=str, default=None, help="Path to a JSON file mapping the class values to category names")
    parser.add_argument("--gpu", action="store_true", help="Use GPU for inference if available")
    return parser.parse_args()

def load_checkpoint(filepath):
    checkpoint = torch.load(filepath)
    if checkpoint['arch'] == "densenet121":
        model = models.densenet121(pretrained=False)
    elif checkpoint['arch'] == "resnet18":
        model = models.resnet18(pretrained=False)
    else:
        print("Invalid model architecture in the checkpoint.")
        return None
    model.classifier = checkpoint['classifier']
    model.load_state_dict(checkpoint['state_dict'])
    model.class_to_idx = checkpoint['class_to_idx']
    return model

def process_image(image_path):
    image = Image.open(image_path)
    preprocess = transforms.Compose([transforms.Resize(256),
                                     transforms.CenterCrop(224),
                                     transforms.ToTensor(),
                                     transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                                          std=[0.229, 0.224, 0.225])])
    image = preprocess(image)
    return image

def predict(image_path, model, topk=1, device='cpu'):
    model.eval()
    model.to(device)
    image = process_image(image_path).unsqueeze(0).to(device)
    with torch.no_grad():
        output = model(image)
        probabilities, indices = torch.topk(output, topk)
        probabilities = torch.exp(probabilities).squeeze().tolist()
        indices = indices.squeeze().tolist()
    return probabilities, indices

def load_category_names(filename):
    with open(filename, 'r') as f:
        category_names = json.load(f)
    return category_names

def main():
    args = parse_args()
    model = load_checkpoint(args.checkpoint)
    if model is None:
        return
    device = torch.device("cuda" if args.gpu and torch.cuda.is_available() else "cpu")
    image_path = args.image_path
    topk = args.top_k

    if args.gpu and not torch.cuda.is_available():
        print("GPU is not available. Using CPU for inference.")

    probabilities, indices = predict(image_path, model, topk, device)

    if args.category_names:
        category_names = load_category_names(args.category_names)
        classes = [category_names[str(index)] for index in indices]
    else:
        classes = indices

    for i in range(len(classes)):
        print(f"Top {i+1} class: {classes[i]}, Probability: {probabilities[i]:.5f}")

if __name__ == "__main__":
    main()