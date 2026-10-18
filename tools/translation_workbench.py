"""Prepare a private translation worksheet; never enable unreviewed game text.

Each row keeps its exact source digest and control tokens. Identical source
strings share a row. Cross-game candidates remain unreviewed, even when the
source bytes decode to identical text: story context still needs checking.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def controls(value):
    if isinstance(value, str):
        import re
        return re.findall(r'\{[^{}]+\}|<[^<>]+>|%[-+ #0]*\d*(?:\.\d+)?[sdif]', value)
    return [segment for segment in value if segment.get('t') not in ('text', 'nl', 'para', 'scroll', 'eos')]


def prepare(source, references=()):
    memory = collections.defaultdict(dict)
    for original, translated in references:
        for key, value in original.items():
            target = translated.get(key)
            if target is None or value == target or controls(value) != controls(target):
                continue
            memory[canonical(value)][canonical(target)] = target
    groups = {}
    for key, value in sorted(source.items()):
        fingerprint = hashlib.sha256(canonical(value).encode()).hexdigest()
        if fingerprint not in groups:
            choices = list(memory.get(canonical(value), {}).values())
            groups[fingerprint] = dict(source_sha256=fingerprint, keys=[], source=value,
                                       candidate=choices[0] if len(choices)==1 else None,
                                       status='needs_review' if len(choices)==1 else 'needs_translation',
                                       target=None)
        groups[fingerprint]['keys'].append(key)
    return list(groups.values())


def validate(row):
    if hashlib.sha256(canonical(row['source']).encode()).hexdigest() != row['source_sha256']:
        raise ValueError('Source changed; translation must be reviewed again')
    if row['status'] != 'approved' or row['target'] is None:
        raise ValueError('Translation is not approved')
    if type(row['target']) is not type(row['source']):
        raise ValueError('Translation changed the text representation')
    if isinstance(row['target'], list):
        if not all(isinstance(s, dict) and isinstance(s.get('t'), str) and
                   (s['t'] != 'text' or isinstance(s.get('s'), str)) for s in row['target']):
            raise ValueError('Malformed translated text segment')
        for value in (row['source'], row['target']):
            if not value or value[-1].get('t') != 'eos':
                raise ValueError('Text must end with EOS')
    if controls(row['source']) != controls(row['target']):
        raise ValueError('Translation changed control tokens/placeholders')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--reference-source', type=Path)
    parser.add_argument('--reference-target', type=Path)
    args = parser.parse_args()
    if bool(args.reference_source) != bool(args.reference_target):
        parser.error('Both reference files are required together')
    references = []
    if args.reference_source:
        references.append((json.loads(args.reference_source.read_text()), json.loads(args.reference_target.read_text())))
    rows = prepare(json.loads(args.source.read_text()), references)
    report = dict(format='ula-translation-workbench-v1', target_language='pt-BR',
                  runtime_enabled=False, entries=rows,
                  summary=dict(keys=sum(len(row['keys']) for row in rows), unique=len(rows),
                               candidates=sum(row['candidate'] is not None for row in rows), approved=0))
    with args.output.open('x') as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
        output.write('\n')
    print(json.dumps(report['summary']))
