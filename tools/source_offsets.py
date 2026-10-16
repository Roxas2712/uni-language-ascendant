"""Recover absent symbol addresses by exact encoded source/ROM matching.

Only offsets leave this developer step. Unencodable or absent strings are
skipped; no approximate text matching or ROM-relative address guesses.
"""
import re

def recover(source, rom, keys):
    chars, tokens = {}, {}
    for line in (source/'charmap.txt').read_text().splitlines():
        m=re.match(r"\s*(?:'([^']*)'|([A-Z_0-9]+))\s*=\s*((?:[0-9A-F]{2}(?:\s+|$))+)",line)
        if m:
            (chars if m[1] is not None else tokens)[m[1] if m[1] is not None else m[2]]=bytes.fromhex(m[3])
    chars.update({'\\n':b'\xfe','\\l':b'\xfa','\\p':b'\xfb','$':b'\xff','\\"':chars.get('"',b'\xb1')})
    def encode(text):
        result=b''
        for token in re.findall(r'\{[^}]+\}|\\.|.',text):
            if token.startswith('{'):
                for part in token[1:-1].split():
                    result+=tokens[part] if part in tokens else bytes([int(part,0)])
            else: result+=chars[token]
        return result if result.endswith(b'\xff') else result+b'\xff'
    candidates={}
    for path in list(source.rglob('*.inc'))+list((source/'src').rglob('*.c')):
        if '/build/' in str(path): continue
        text=path.read_text(errors='replace')
        if path.suffix=='.inc':
            # A source label can appear more than once before the same string.
            matches=list(re.finditer(r'^([A-Za-z_][\w]*):[^\n]*\n((?:(?:[^\n]*\.string[^\n]*|\s*)\n)+)',text,re.M))
            for m in matches:
                if m[1] in keys:
                    value=''.join(re.findall(r'\.string\s+"((?:\\.|[^"\\])*)"',m[2]))
                    if value: candidates.setdefault(m[1],[]).append(value)
        else:
            for m in re.finditer(r'\b(\w+)\[\]\s*=\s*_\(\s*((?:"(?:\\.|[^"\\])*"\s*)+)\)',text):
                if m[1] in keys:
                    candidates.setdefault(m[1],[]).append(''.join(re.findall(r'"((?:\\.|[^"\\])*)"',m[2])))
    result={}
    for key,values in candidates.items():
        # German alternatives follow the English definitions in these sources.
        for value in reversed(values):
            try: data=encode(value)
            except (KeyError,ValueError): continue
            off=rom.find(data)
            if off>=0:
                result[key]=(off,len(data));break
    return result
