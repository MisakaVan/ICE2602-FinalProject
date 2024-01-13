import face_recognition
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import time

def find_similar_images(target_image_path, index_path, k=5):
    IdxStart = time.time()
    index = np.load(index_path, allow_pickle=True).item()
    IdxEnd = time.time()
    print( f"读取索引用时为：{IdxEnd-IdxStart}s" )
    target_image = face_recognition.load_image_file(target_image_path)
    target_encoding = face_recognition.face_encodings(target_image)[0]
    EncodingEnd = time.time()
    print( f"提取待查图片特征向量用时为：{EncodingEnd-IdxEnd}s" )
    DictDistance = {}
    for img_Name, img_Vec in index.items():
        ThisDistance = face_recognition.face_distance( [img_Vec], target_encoding )
        DictDistance[img_Name] = ThisDistance[0]
    Lst_SortedDistance = sorted(DictDistance.items(), key=lambda x: x[1], reverse=False)
    most_similar_images = Lst_SortedDistance[:k]
    print( f"计算相似度用时为：{time.time()-EncodingEnd}s" )
    return [img_name for img_name, _ in most_similar_images]

target_image_path = r'playground\TEST_ToSearch\download.jpg'
index_path = r'playground\TEST_Vectors_FaceRecognition\IndexFile.npy'
similar_images = find_similar_images(target_image_path, index_path, k=5)
print(similar_images)