"""Compile authored dialogue to the original game's validated text IR.

Dynamic/control operands require explicit numbered placeholders in source order.
Cross-edition reuse requires identical complete source IR, never similar prose.
The conservative 26-glyph layout fits the 208px field box at <=8px per glyph;
the live suite additionally checks the actual active font's measured widths.
"""
import argparse
import json
import re
import textwrap
from pathlib import Path

from build_authored import build, controls
from build_profiles import lua


def plain_ir(source, prose):
    if controls(source):
        raise ValueError('Plain translation cannot replace dynamic/control operands')
    if not isinstance(prose,str) or not prose.strip():
        raise ValueError('Translation must contain text')
    if any(ch in prose for ch in ('{','}','\x00')):
        raise ValueError('Plain translation contains control syntax')
    result = []
    for paragraph in prose.split('\n\n'):
        if result:
            result.append({'t':'para'})
        lines = [line for explicit in paragraph.strip().split('\n') for line in
                 textwrap.wrap(explicit, width=26, break_long_words=False, break_on_hyphens=False)]
        for i,line in enumerate(lines):
            if len(line)>26:
                raise ValueError('Word exceeds the field box')
            if i:
                result.append({'t':'nl' if i==1 else 'scroll'})
            result.append({'t':'text','s':line})
    # A leading blank is meaningful in concatenated fragments such as
    # "<player> has no berries". Do not silently join the name and verb.
    if prose.startswith(' '):
        result[0]['s']=' '+result[0]['s']
    result.append({'t':'eos'})
    return result


def template_ir(source, prose):
    operands=controls(source)
    indices=[int(n) for n in re.findall(r'\{(\d+)\}',prose)]
    if indices!=list(range(len(operands))):
        raise ValueError('Translation must preserve every control operand in order')
    if re.search(r'[{}]',re.sub(r'\{\d+\}','',prose)):
        raise ValueError('Invalid placeholder syntax')
    def width(word):
        size=len(re.sub(r'\{\d+\}','',word))
        for n in re.findall(r'\{(\d+)\}',word):
            op=operands[int(n)]
            size+=({'ext':0,'ph':0,'player':7,'tag':8,'bph':16}.get(op['t'],12))
        return size
    out=[]
    for paragraph in prose.split('\n\n'):
        lines=[]
        for explicit in paragraph.split('\n'):
            line=''
            for word in explicit.split():
                if width(word)>26:raise ValueError('Unbreakable dynamic text is too wide')
                if line and width(line+' '+word)>26:lines.append(line);line=word
                else:line=(line+' '+word).lstrip()
            if line:lines.append(line)
        if out:out.append({'t':'para'})
        for i,line in enumerate(lines):
            if i:out.append({'t':'nl' if i==1 else 'scroll'})
            for part in re.split(r'(\{\d+\})',line):
                if re.fullmatch(r'\{\d+\}',part):out.append(dict(operands[int(part[1:-1])]))
                elif part:out.append({'t':'text','s':part})
    if not out:raise ValueError('Empty template')
    out.append({'t':'eos'})
    return out


def compile_prose(source, prose):
    targets={}
    for key,text in prose.items():
        try:
            targets[key]=(template_ir if controls(source[key]) else plain_ir)(source[key],text)
        except ValueError as error:
            raise ValueError(f'{key}: {error}') from error
    return targets


def reuse_exact(source, reference, targets, overrides=None):
    canonical=lambda ir:json.dumps(ir,sort_keys=True,ensure_ascii=False)
    translated={}
    for key,target in targets.items():
        identity=canonical(reference[key])
        if identity in translated and translated[identity]!=target:
            raise ValueError('Conflicting reference aliases: '+key)
        translated[identity]=target
    # Edition-specific corrections override every alias of that source IR.
    for key,target in (overrides or {}).items():
        translated[canonical(source[key])]=target
    return {key:translated[canonical(ir)] for key,ir in source.items() if canonical(ir) in translated}


def main(args):
    source=json.loads(args.base.read_text())
    corrections=json.loads(args.corrections.read_text()) if args.corrections else {}
    if args.edition_translations:
        local=compile_prose(source,json.loads(args.edition_translations.read_text()))
        local.update(corrections)
        corrections=local
    prose=json.loads(args.translations.read_text())
    reference=json.loads(args.reference_base.read_text()) if args.reference_base else source
    targets=reuse_exact(source,reference,compile_prose(reference,prose),corrections)
    rows=build(source,targets,args.engine,args.luajit)
    args.output.write_text('-- Authored PT-BR dialogue; exact base-IR fingerprints.\nreturn '+lua(rows)+'\n')
    print('AUTHORED_SUPPLEMENT_OK',len(prose),'reference templates;',len(rows),'applied validated aliases')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('base','translations','engine','luajit','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--corrections',type=Path)
    p.add_argument('--reference-base',type=Path,help='Reuse only complete identical IR from another edition')
    p.add_argument('--edition-translations',type=Path,help='Additional prose keyed to this edition')
    main(p.parse_args())
