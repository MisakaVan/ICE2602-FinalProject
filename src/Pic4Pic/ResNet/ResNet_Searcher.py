import torch
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import os
import torchvision.models as models

transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

resnet = models.resnet50(pretrained=True)
resnet = torch.nn.Sequential(*(list(resnet.children())[:-1]))
resnet.eval()

def load_features(storage_path):
    features = []
    file_names = []
    for file in os.listdir(storage_path):
        if file.endswith('.npy'):
            file_names.append(file.replace('features_', '').replace('.npy', ''))
            feature_path = os.path.join(storage_path, file)
            features.append(np.load(feature_path))
    return np.array(features), file_names

def get_image_feature(image_path, transform, model):
    image = Image.open(image_path).convert('RGB')
    image = transform(image).unsqueeze(0)
    with torch.no_grad():
        feature = model(image).numpy().flatten()
        feature /= np.linalg.norm(feature)
    return feature

def compute_similarity(query_feature, database_features):
    similarities = np.dot(database_features, query_feature)
    return similarities

def search_similar_images(query_image_path, storage_path, transform, model, k=5):
    database_features, file_names = load_features(storage_path)
    query_feature = get_image_feature(query_image_path, transform, model)
    similarities = compute_similarity(query_feature, database_features)
    most_similar_indices = np.argsort(similarities)[::-1][:k]
    return [file_names[i] for i in most_similar_indices]

if __name__ == '__main__':
    query_image_path = 'playground/TEST_ToSearch/download.jpg'  
    storage_path = 'playground/TEST_Vectors'  
    similar_images = search_similar_images(query_image_path, storage_path, transform, resnet)
    print("Most similar images:", similar_images)