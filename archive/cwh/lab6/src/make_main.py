from makeIndex import *

from MySimilarity import Similarity1, Similarity2

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S")

    print(os.getcwd())

    html_index_file = "./Crawler_lab3/cache/index.txt"
    html_cache_dir = "./Crawler_lab3/cache/html/"
    store_dirs = ["./lucene_index_ver1", "./lucene_index_ver2"]
    similarity_classes = [Similarity1, Similarity2]

    # Set manually 0 or 1
    version = 1


    if not os.path.exists(store_dirs[version]):
        os.mkdir(store_dirs[version])

    lucene.initVM()

    sim1 = similarity_classes[version]()
    print(sim1)
    indexer = HtmlIndexer(store_dir=store_dirs[version],
                          source_dir=html_cache_dir,
                          source_index=html_index_file,
                          similarity_class=sim1)

    indexer.run()
    indexer.writer.commit()
    indexer.writer.close()
