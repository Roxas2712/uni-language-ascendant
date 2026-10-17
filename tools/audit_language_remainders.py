"""Find unchanged text without dropping short strings or non-ASCII dialogue.

This is a review queue, not a language-completeness certificate. Names, cries,
labels and actual untranslated dialogue can all be unchanged. Output contains
keys and fingerprints only; --private-texts may retain prose under build/.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from build_plain_supplement import compile_prose, reuse_exact


def canonical(ir):
    return json.dumps(ir,sort_keys=True,ensure_ascii=False)


def prose(ir):
    return re.sub(r'\s+',' ',''.join(s.get('s','') if s['t']=='text' else ' ' for s in ir)).strip()


def audit(source, decoded, authored):
    grouped={};missing=[]
    for key,original in source.items():
        effective=authored.get(key,decoded.get(key))
        if effective is None:
            missing.append(key);continue
        text=prose(original)
        if not any(c.isalpha() for c in text) or text!=prose(effective):continue
        identity=canonical(original)
        row=grouped.setdefault(identity,{'source_sha256':hashlib.sha256(identity.encode()).hexdigest(),
              'keys':[], 'characters':len(text),'review':'unreviewed-unchanged-candidate'})
        row['keys'].append(key)
    rows=list(grouped.values())
    return dict(status='review-required',completeness_proven=False,unchanged_unique_candidates=len(rows),
                unchanged_keys=sum(len(r['keys']) for r in rows),missing_decoded_keys=missing,
                candidates=rows)



def apply_neutral_review(report, source, review):
    verified={}
    for row in review['entries']:
        digest=row['source_sha256']
        assert row['keys'] and row['reason'], 'Incomplete neutral review'
        for key in row['keys']:
            actual=hashlib.sha256(canonical(source[key]).encode()).hexdigest()
            if actual!=digest:raise ValueError('Stale neutral review: '+key)
        if digest in verified and verified[digest]!=row['reason']:
            raise ValueError('Conflicting neutral review: '+digest)
        verified[digest]=row['reason']
    for row in report['candidates']:
        reason=verified.get(row['source_sha256'])
        if reason:row.update(review='reviewed-neutral',reason=reason)
    report['reviewed_neutral_unique']=sum(r['review']=='reviewed-neutral' for r in report['candidates'])
    report['unreviewed_unique_candidates']=sum(r['review']!='reviewed-neutral' for r in report['candidates'])
    # This audit cannot judge changed native prose, graphics or gameplay.
    report['completeness_proven']=False


def main(a):
    source=json.loads(a.base.read_text());decoded=json.loads(a.decoded.read_text())
    reference=json.loads(a.reference_base.read_text()) if a.reference_base else source
    targets=compile_prose(reference,json.loads(a.translations.read_text()))
    corrections=json.loads(a.corrections.read_text()) if a.corrections else {}
    if a.edition_translations:
        edition_reference=json.loads(a.edition_reference_base.read_text()) if a.edition_reference_base else source
        local=reuse_exact(source,edition_reference,compile_prose(edition_reference,json.loads(a.edition_translations.read_text())))
        local.update(corrections);corrections=local
    authored=reuse_exact(source,reference,targets,corrections)
    report=audit(source,decoded,authored)
    if a.neutral:apply_neutral_review(report,source,json.loads(a.neutral.read_text()))
    report['inputs_sha256']={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in
       [('base',a.base),('decoded',a.decoded),('translations',a.translations),
        ('reference_base',a.reference_base),('corrections',a.corrections),
        ('edition_translations',a.edition_translations),('edition_reference_base',a.edition_reference_base),('neutral',a.neutral)] if path}
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    if a.private_texts:
        assert 'build' in a.private_texts.parts,'Source prose must remain in the private build directory'
        a.private_texts.write_text(json.dumps([{**r,'text':prose(source[r['keys'][0]])} for r in report['candidates']],ensure_ascii=False,indent=2)+'\n')
    print('REMAINDER_AUDIT',report.get('unreviewed_unique_candidates',report['unchanged_unique_candidates']),'unreviewed candidates;',len(report['missing_decoded_keys']),'missing keys; NOT a completion claim')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('base','decoded','translations','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('reference-base','corrections','private-texts','edition-translations','edition-reference-base','neutral'):p.add_argument('--'+name,type=Path)
    main(p.parse_args())
