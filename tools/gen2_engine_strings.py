"""Collect actual Gen-2 engine UI keys and bind exact ROM-text equivalents."""
import re

def literal(token):
    body=token[1:-1];out=bytearray();i=0
    escapes={'a':7,'b':8,'f':12,'n':10,'r':13,'t':9,'v':11}
    while i<len(body):
        c=body[i];i+=1
        if c!='\\':out.extend(c.encode('utf-8'));continue
        c=body[i];i+=1
        if c in escapes:out.append(escapes[c])
        elif c in ('\\','"',"'"):out.extend(c.encode())
        elif c.isdigit():
            digits=c
            while i<len(body) and len(digits)<3 and body[i].isdigit():digits+=body[i];i+=1
            out.append(int(digits))
        elif c=='x':out.append(int(body[i:i+2],16));i+=2
        elif c=='z':
            while i<len(body) and body[i].isspace():i+=1
        else:raise ValueError('Unsupported Lua string escape: '+c)
    return out.decode('utf-8')

QUOTED=re.compile(r"\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'",re.S)

def code_without_comments(code):
    chars=list(code);i=0
    while i<len(code):
        if code[i] in ('"',"'"):
            match=QUOTED.match(code,i)
            if not match:raise ValueError('Unterminated Lua literal')
            i=match.end();continue
        if code.startswith('--',i):
            long=re.match(r'--\[(=*)\[',code[i:])
            if long:
                end=code.find(']'+long[1]+']',i+len(long[0]))
                if end<0:raise ValueError('Unterminated Lua comment')
                end+=len(long[1])+2
            else:
                end=code.find('\n',i)
                if end<0:end=len(code)
            for j in range(i,end):
                if chars[j]!='\n':chars[j]=' '
            i=end
        else:i+=1
    return ''.join(chars)

def keys_in_source(code):
    code=code_without_comments(code)
    for match in re.finditer(r'Strings(?:\.source)?\(\s*',code):
        at=match.end();chunks=[]
        while True:
            part=QUOTED.match(code,at)
            if not part:break
            chunks.append(literal(part[0]));at=part.end()
            while at<len(code) and code[at].isspace():at+=1
            if not code.startswith('..',at):
                if at<len(code) and code[at] in (')',','):yield ''.join(chunks)
                break
            at+=2
            while at<len(code) and code[at].isspace():at+=1

def harvest(engine):
    result={}
    for path in sorted((engine/'src').rglob('*.lua')):
        if 'gen2' not in path.parts and path.name!='Game2.lua':continue
        for value in keys_in_source(path.read_text()):
            result.setdefault(value,[]).append(str(path.relative_to(engine)))
    return result

def normalize(value):
    return value.replace('#MON','POKéMON').replace('#DEX','POKéDEX').replace('#GEAR','POKéGEAR').replace('<PK><MN>','POKéMON').removesuffix('{DONE}').removesuffix('{PROMPT}')

def bind_rom_strings(keys,review,recipes,authored):
    by_original={}
    for row in review:by_original.setdefault(normalize(row['original']),[]).append(row)
    out={k:{'value':v} for k,v in authored.items()};missing=[]
    for source in keys:
        if source in out:continue
        candidates=by_original.get(normalize(source),[])
        if candidates and len({normalize(row['translated']) for row in candidates})==1:
            recipe=recipes[candidates[0]['key']]
            if 'value' in recipe:recipe={'value':normalize(recipe['value'])}
            else:
                parts=list(recipe['parts'])
                if parts and parts[-1].get('token') in ('{DONE}','{PROMPT}'):parts.pop()
                recipe={'parts':parts}
            out[source]=recipe
        else:missing.append(source)
    return out,missing
