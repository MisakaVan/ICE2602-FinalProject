import torch
import torchvision.models as models
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
import os
import numpy as np

image_folder = 'playground/TEST_DataBase'  # 图片文件夹路径
storage_path = 'playground/TEST_Vectors'  # 特征向量存储路径

resnet = models.resnet50(pretrained=True)
resnet = torch.nn.Sequential(*(list(resnet.children())[:-1]))
resnet.eval()

transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def load_images(image_folder):
    dataset = ImageFolder(root=image_folder, transform=transform)
    dataloader = DataLoader(dataset, batch_size=1, shuffle=False)
    return dataloader

def extract_features(save_path, image_folder):
    dataloader = load_images(image_folder)
    for i, (inputs, _) in enumerate(dataloader):
        with torch.no_grad():
            features = resnet(inputs).numpy().flatten()
            features /= np.linalg.norm(features)
            file_name = f'features_{i}.npy'
            file_path = os.path.join(save_path, file_name)
            np.save(file_path, features)
if __name__ == '__main__':
    extract_features(storage_path, image_folder)