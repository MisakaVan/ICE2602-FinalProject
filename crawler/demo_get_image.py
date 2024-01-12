import ImageRetriever as ir

def demo_get_image():
    retriever_directory = "./image_sina_cache"

    image_retriever = ir.ImageRetriever.load_from(directory=retriever_directory, load_fileset=False)

    img_src = 'http://n.sinaimg.cn/sports/transform/20160506/cfMn-fxrytex7140466.jpg'

    print(image_retriever.get_location(img_src))

    img_src2 = img_src + '?foo=bar'

    print(image_retriever.get_location(img_src2))


if __name__ == '__main__':
    demo_get_image()
