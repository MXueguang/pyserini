import argparse
import os

import faiss
import shutil


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bf-index', type=str, help='path to brute force index', required=True)
    parser.add_argument('--pq-index', type=str, help='path to hnsw index', required=True)
    parser.add_argument('--dimension', type=int, help='dimension of passage embeddings', required=True)
    parser.add_argument('--M', type=int, help='number of subquantizers', required=True)
    args = parser.parse_args()

    if not os.path.exists(args.pq_index):
        os.mkdir(args.pq_index)
    shutil.copy(os.path.join(args.bf_index, 'docid'), os.path.join(args.pq_index, 'docid'))

    bf_index = faiss.read_index(os.path.join(args.bf_index, 'index'))
    pq_index = faiss.IndexPQ(args.dimension, args.M, 8, faiss.METRIC_INNER_PRODUCT)

    vectors = bf_index.reconstruct_n(0, bf_index.ntotal)
    print(vectors)
    print('Training')
    pq_index.train(vectors)
    print('Indexing')
    pq_index.add(vectors)
    faiss.write_index(pq_index, os.path.join(args.pq_index, 'index'))
