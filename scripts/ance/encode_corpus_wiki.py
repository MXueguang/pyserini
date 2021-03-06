#
# Pyserini: Reproducible IR research with sparse and dense representations
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import argparse
import json
import os

import faiss
import numpy as np
from tqdm import tqdm
from transformers import DPRContextEncoderTokenizer, DPRContextEncoder


def encode_passage(titles, texts, tokenizer, model, device='cuda:0'):
    max_length = 256  # hardcode for now
    inputs = tokenizer(
        titles,
        text_pair=texts,
        max_length=max_length,
        padding='longest',
        truncation=True,
        add_special_tokens=True,
        return_tensors='pt'
    )
    inputs.to(device)
    embeddings = model(inputs["input_ids"]).pooler_output.detach().cpu().numpy()
    return embeddings


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--encoder', type=str, help='encoder name or path', required=True)
    parser.add_argument('--dimension', type=int, help='dimension of passage embeddings', required=False, default=768)
    parser.add_argument('--corpus', type=str,
                        help='directory that contains corpus files to be encoded, in jsonl format.', required=True)
    parser.add_argument('--index', type=str, help='directory to store brute force index of corpus', required=True)
    parser.add_argument('--batch', type=int, help='batch size', default=8)
    parser.add_argument('--device', type=str, help='device cpu or cuda [cuda:0, cuda:1...]', default='cuda:0')
    args = parser.parse_args()

    tokenizer = DPRContextEncoderTokenizer.from_pretrained(args.encoder)
    model = DPRContextEncoder.from_pretrained(args.encoder)
    model.to(args.device)

    index = faiss.IndexFlatIP(args.dimension)

    if not os.path.exists(args.index):
        os.mkdir(args.index)

    titles = []
    texts = []
    with open(os.path.join(args.index, 'docid'), 'w') as id_file:
        for file in sorted(os.listdir(args.corpus)):
            file = os.path.join(args.corpus, file)
            if file.endswith('json') or file.endswith('jsonl'):
                print(f'Encoding {file}')
                with open(file, 'r') as corpus:
                    for idx, line in enumerate(tqdm(corpus.readlines())):
                        info = json.loads(line)
                        docid = info['id']
                        title, text = info['contents'].split('\n')
                        title = title.replace('"', '')
                        text = text.replace('""', '"')
                        id_file.write(f'{docid}\n')
                        titles.append(title)
                        texts.append(text)
    for idx in tqdm(range(0, len(titles), args.batch)):
        title_batch = titles[idx: idx+args.batch]
        text_batch = texts[idx: idx+args.batch]
        embeddings = encode_passage(title_batch, text_batch, tokenizer, model, args.device)
        index.add(np.array(embeddings))
    faiss.write_index(index, os.path.join(args.index, 'index'))