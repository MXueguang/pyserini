import argparse
import json
import os
import sys
from tqdm import tqdm

# We're going to explicitly use a local installation of Pyserini (as opposed to a pip-installed one).
# Comment these lines out to use a pip-installed one instead.
sys.path.insert(0, './')
sys.path.insert(0, '../pyserini/')

from pyserini.search import SimpleSearcher, get_topics

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert an TREC run to DPR retrieval result json.')
    parser.add_argument('--topics', required=True, help='topic name')
    parser.add_argument('--index', required=True, help='Anserini Index that contains raw')
    parser.add_argument('--input', required=True, help='Input TREC run file.')
    parser.add_argument('--output', required=True, help='Output DPR Retrieval json file.')
    args = parser.parse_args()

    qas = get_topics(args.topics)

    if os.path.exists(args.index):
        searcher = SimpleSearcher(args.index)
    else:
        searcher = SimpleSearcher.from_prebuilt_index(args.index)
    if not searcher:
        exit()

    retrieval = {}
    with open(args.input) as f_in:
        for line in tqdm(f_in.readlines()):
            question_id, _, doc_id, _, score, bm25, dpr, _ = line.strip().split()
            question_id = int(question_id)
            question = qas[question_id]['title']
            answers = qas[question_id]['answers']
            if answers[0] == '"':
                answers = answers[1:-1].replace('""', '"')
            answers = eval(answers)
            ctx = json.loads(searcher.doc(doc_id).raw())['contents']
            if question_id not in retrieval:
                retrieval[question_id] = {'question': question, 'answers': answers, 'contexts': []}
            retrieval[question_id]['contexts'].append(
                {'docid': doc_id, 'hybrid_score': float(score), 'bm25_score': float(bm25), 'dpr_score': float(dpr), 'text': ctx}
            )

    json.dump(retrieval, open(args.output, 'w'), indent=4)
