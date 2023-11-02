from MySimilarity import *
from searchIndex import *

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S")

    print(os.getcwd())

    lucene.initVM()

    store_dirs = ["./lucene_index_ver1", "./lucene_index_ver2"]
    similarity_classes = [Similarity1, Similarity2]

    # Set manually
    # version = 1
    version = int(input("Select version [0 or 1]:"))
    assert version in [0, 1]


    searcher = HtmlIndexSearcher(store_dir=store_dirs[version],
                                 similarity_class=similarity_classes[version]())

    command = ""
    while True:
        command = input("Search command: ")
        # command = "sjtu"
        if command == "":
            continue

        if command == "q":
            break

        searcher.query(command)

    del searcher
