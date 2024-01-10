import torch
import torchvision.models as models
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
import os
import numpy as np

# 图片文件夹路径和特征向量存储路径
image_folder = 'playground/TEST_DataBase'
storage_path = 'playground/TEST_Vectors'

# 使用预训练的VGG16模型
vgg16 = models.vgg16(pretrained=True)
vgg16.classifier = torch.nn.Sequential(*list(vgg16.classifier.children())[:-3])  # 保留到倒数第三层
vgg16.eval()

# 定义图片转换方式
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# 加载图片
def load_images(image_folder):
    dataset = ImageFolder(root=image_folder, transform=transform)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=False)  # 使用较大的batch size以提高效率
    return dataloader

# 提取特征向量
def extract_features(save_path, image_folder):
    dataloader = load_images(image_folder)
    for i, (inputs, _) in enumerate(dataloader):
        with torch.no_grad():
            features = vgg16(inputs)
            features = features.view(features.size(0), -1)  # 将特征向量拉平
            features /= torch.norm(features, dim=1, keepdim=True)  # 归一化
            for j, feature in enumerate(features):
                file_name = f'features_{i*len(features)+j}.npy'
                file_path = os.path.join(save_path, file_name)
                np.save(file_path, feature.numpy())

if __name__ == '__main__':
    extract_features(storage_path, image_folder)