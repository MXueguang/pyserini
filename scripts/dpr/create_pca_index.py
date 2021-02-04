import argparse
import os

import faiss
import shutil


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bf-index', type=str, help='path to brute force index', required=True)
    parser.add_argument('--din', type=int, help='dimension of input index', required=True)
    parser.add_argument('--dout', type=int, help='dimension of output index', required=True)
    parser.add_argument('--pca-index', type=str, help='path to hnsw index', required=True)
    parser.add_argument('--model', type=str, help='path to pca model', required=True)
    args = parser.parse_args()

    if not os.path.exists(args.pca_index):
        os.mkdir(args.pca_index)
    shutil.copy(os.path.join(args.bf_index, 'docid'), os.path.join(args.pca_index, 'docid'))

    print("Reading Index")
    bf_index = faiss.read_index(os.path.join(args.bf_index, 'index'))
    vectors = bf_index.reconstruct_n(0, bf_index.ntotal)

    print("Fitting PCA")
    mat = faiss.PCAMatrix(args.din, args.dout)
    mat.train(vectors)

    pca_index = faiss.IndexFlatIP(args.dout)

    print("Transforming")
    vectors_tr = mat.apply_py(vectors)

    print("Creat PCA index")
    pca_index.add(vectors_tr)

    faiss.write_index(pca_index, os.path.join(args.pca_index, 'index'))

    faiss.write_VectorTransform(mat, args.model)
