import face_recognition
import numpy as np
import os

def build_index(image_database_path, index_path):
    index = {}

    os.makedirs(os.path.dirname(index_path), exist_ok=True)

    for img_name in os.listdir(image_database_path):
        img_path = os.path.join(image_database_path, img_name)
        image = face_recognition.load_image_file(img_path)
        if len( face_recognition.face_locations( image ) ) == 0:
            continue
        encodings = face_recognition.face_encodings(image)

        if len(encodings) > 0:
            index[img_name] = encodings[0]

    np.save(index_path, index)

image_database_path = 'playground\TEST_DataBase\Folder'
index_path = 'playground\TEST_Vectors_FaceRecognition\IndexFile.npy'

build_index(image_database_path, index_path)