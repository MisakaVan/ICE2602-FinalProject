import face_recognition
import os
 
path_know = 'playground\TEST_DataBase\Folder'
path_unknow = 'playground\TEST_ToSearch'
 
know = {}
for path in os.listdir(path_know):
    img_path = os.path.join(path_know, path)
    img = face_recognition.load_image_file(img_path)
    encoding = face_recognition.face_encodings(img)[0]
    name = path.split('.')[0]
    know[name] = encoding
 
match = {}
for path in os.listdir(path_unknow):
    img = face_recognition.load_image_file(path_unknow+'/'+path)
    encoding = face_recognition.face_encodings(img)[0]
    name = path.split('.')[0]
    match[name] = 'unknow'
    for key, value in know.items():
        if face_recognition.compare_faces([value],encoding)[0]:
            match[name] = key
            break
 
print(match)
 
for key, value in match.items():
    print(key+' is '+ value)