import os

def rename_images(folder_path):
    image_files = [f for f in os.listdir(folder_path) if f.endswith('.jpg')]
    for i, old_name in enumerate(image_files):
        new_name = str(i) + '.jpg'
        os.rename(os.path.join(folder_path, old_name), os.path.join(folder_path, new_name))

if __name__ == '__main__':
    folder_path = 'playground/TEST_DataBase/Folder'  # 替换成你的文件夹路径
    rename_images(folder_path)