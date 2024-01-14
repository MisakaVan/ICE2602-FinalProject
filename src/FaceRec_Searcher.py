import face_recognition
import numpy as np
import time


def LstMinEle(Lst):
    TmpMin = 100
    for i in Lst:
        if i < TmpMin:
            TmpMin = i
    return TmpMin

def find_similar_images(target_image_path = r'FaceRec_RealWork\FaceRec_ToSearch\download.jpg',
                        index_path= r'FaceRec_RealWork\FaceRec_VectorStorage\IndexFile.npy',
                        k=5):
    IdxStart = time.time()
    index = np.load(index_path, allow_pickle=True).item()
    IdxEnd = time.time()
    print( f"读取索引用时为：{IdxEnd-IdxStart}s" )

    target_image = face_recognition.load_image_file(target_image_path)
    target_encoding = face_recognition.face_encodings(target_image)[0]
    EncodingEnd = time.time()
    print( f"提取待查图片特征向量用时为：{EncodingEnd-IdxEnd}s" )

    DictDistance = {}
    for img_Path, TupleInfo in index.items():
        Lstimg_Vec = TupleInfo[0]
        ThisDistance = face_recognition.face_distance( Lstimg_Vec, target_encoding )
        DictDistance[img_Path] = (LstMinEle(ThisDistance), TupleInfo[1],TupleInfo[2])
    Lst_SortedDistance = sorted(DictDistance.items(), key=lambda x: x[1][0], reverse=False)
    most_similar_images = Lst_SortedDistance[:k]#{ img_Path: ( Distance, 原文url, 原文标题 ) }
    print( f"计算相似度用时为：{time.time()-EncodingEnd}s" )

    return [img_info for img_info in most_similar_images]

if __name__ == "__main__":

    similar_images = find_similar_images()
    for ele in similar_images:
        print(ele)