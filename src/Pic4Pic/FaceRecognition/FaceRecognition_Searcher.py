import face_recognition
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def find_similar_images(target_image_path, index_path, k=5):
    index = np.load(index_path, allow_pickle=True).item()

    target_image = face_recognition.load_image_file(target_image_path)
    target_encoding = face_recognition.face_encodings(target_image)[0]

    similarities = {}
    for img_name, img_encoding in index.items():
        similarity = cosine_similarity([target_encoding], [img_encoding])[0][0]
        similarities[img_name] = similarity

    sorted_similarities = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
    most_similar_images = sorted_similarities[:k]

    return [img_name for img_name, _ in most_similar_images]

target_image_path = r'playground\TEST_ToSearch\OIP-C (1).jpg'
index_path = r'playground\TEST_Vectors_FaceRecognition\IndexFile.npy'
similar_images = find_similar_images(target_image_path, index_path, k=5)
print(similar_images)