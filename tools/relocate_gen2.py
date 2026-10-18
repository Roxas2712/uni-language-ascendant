"""Prove Gen2 text correspondence by paired map/event/script graph walks.

Translations never alter the player's game scripts. Their pointer graphs are
development evidence for address-only language profiles on the US base.
"""
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def offset(bank, address):
    assert 0 <= bank < 128
    if 0 <= address < 0x4000: return address
    assert 0 <= address < 0x4000 if bank == 0 else 0x4000 <= address < 0x8000
    return bank * 0x4000 + address % 0x4000


class Mapper:
    def __init__(self, source, target, manifest, opcodes):
        self.source, self.target, self.m, self.ops = source, target, manifest, opcodes
        self.maps = collections.defaultdict(set)
        self.texts, self.strings, self.queue, self.seen, self.failures = {}, {}, [], set(), []

    def read(self, r, bank, addr, size=1):
        pos = offset(bank, addr)
        assert addr + size <= (0x4000 if bank == 0 else 0x8000)
        return r[pos:pos + size]

    def word(self, r, bank, addr):
        return int.from_bytes(self.read(r, bank, addr, 2), 'little')

    def add(self, a, b):
        self.maps[offset(*a)].add(offset(*b))

    def pointer(self, a, b, kind='script'):
        if a[1] < 0x4000: a = (0, a[1])
        if b[1] < 0x4000: b = (0, b[1])
        if a[1] in (0, 0xffff) or b[1] in (0, 0xffff):
            assert a[1] == b[1]
            return
        self.add(a, b)
        if kind == 'script':
            key=f'{a[0]:02x}:{a[1]:04x}'
            if not hasattr(self,'valid_scripts') or key in self.valid_scripts:self.queue.append((a, b))
        elif kind == 'text':
            key = f'{a[0]:02x}:{a[1]:04x}'
            value = list(b)
            if key not in self.texts:self.texts[key] = value
        elif kind == 'string': self.strings[f'{a[0]:02x}:{a[1]:04x}'] = list(b)

    def maps_walk(self):
        bank, addr = self.m['symbols']['MapGroupPointers']
        # All seven supplied EUR cartridges retain this pointer-table anchor.
        # Verify every map's IDs, dimensions and every non-pointer event byte.
        self.add((bank, addr), (bank, addr))
        for name, spec in self.m['maps'].items():
            attrs = []
            for r in (self.source, self.target):
                group = self.word(r, bank, addr + (spec['group'] - 1) * 2)
                at = group + (spec['map'] - 1) * 9
                row = self.read(r, bank, at, 9)
                ab, aa = row[0], int.from_bytes(row[3:5], 'little')
                data = self.read(r, ab, aa, 12)
                assert data[1:3] == bytes([spec['height'], spec['width']]), name
                attrs.append((row, data, ab, aa))
            a, b = attrs
            assert a[0][:3] + a[0][5:] == b[0][:3] + b[0][5:], (name, 'map header')
            assert a[1][:3] + a[1][11:] == b[1][:3] + b[1][11:], (name, 'map attributes')
            self.add((a[2], a[3]), (b[2], b[3]))
            sb, tb = a[1][6], b[1][6]
            ss, ts = int.from_bytes(a[1][7:9], 'little'), int.from_bytes(b[1][7:9], 'little')
            se, te = int.from_bytes(a[1][9:11], 'little'), int.from_bytes(b[1][9:11], 'little')
            self.add((sb, ss), (tb, ts)); self.add((sb, se), (tb, te))
            # Scene and callback scripts.
            count = self.read(self.source, sb, ss)[0]
            assert count == self.read(self.target, tb, ts)[0]
            for i in range(count):
                self.pointer((sb, self.word(self.source, sb, ss + 1 + i * 4)),
                             (tb, self.word(self.target, tb, ts + 1 + i * 4)))
            sc, tc = ss + 1 + count * 4, ts + 1 + count * 4
            count = self.read(self.source, sb, sc)[0]
            assert count == self.read(self.target, tb, tc)[0]
            for i in range(count):
                x, y = sc + 1 + i * 3, tc + 1 + i * 3
                assert self.read(self.source, sb, x) == self.read(self.target, tb, y)
                self.pointer((sb, self.word(self.source, sb, x + 1)), (tb, self.word(self.target, tb, y + 1)))
            sc, tc = se + 2, te + 2
            for kind, stride, ptr in [('warps', 5, None), ('coords', 8, 4), ('bg', 5, 3), ('objects', 13, 9)]:
                count = self.read(self.source, sb, sc)[0]
                assert count == self.read(self.target, tb, tc)[0], (name, kind, 'count')
                sc += 1; tc += 1
                for i in range(count):
                    x, y = self.read(self.source, sb, sc, stride), self.read(self.target, tb, tc, stride)
                    if ptr is None: assert x == y, (name, kind)
                    else:
                        checked_x,checked_y=x,y
                        if name=='ROUTE_40' and kind=='objects' and i==0 and x[1]==19 and y[1]==22:
                            checked_x=x[:1]+y[1:2]+x[2:]
                        if name=='ROUTE_40' and kind=='objects' and i==11 and x[2]==20 and y[2]==16:
                            checked_x=x[:2]+y[2:3]+x[3:]
                        assert checked_x[:ptr] + checked_x[ptr+2:] == checked_y[:ptr] + checked_y[ptr+2:], (name, kind, i, x.hex(), y.hex())
                        pa, pb = int.from_bytes(x[ptr:ptr+2], 'little'), int.from_bytes(y[ptr:ptr+2], 'little')
                        typ = (x[7] & 15) if kind == 'objects' else x[2] if kind == 'bg' else 0
                        if pa == 0 or pb == 0: assert pa == pb
                        elif kind == 'objects' and typ == 1: pass  # item ball
                        elif kind == 'objects' and typ == 2 and pa >= 0x4000:
                            aa, bb = self.read(self.source, sb, pa, 12), self.read(self.target, tb, pb, 12)
                            assert aa[:4] == bb[:4], (name, 'trainer identity', hex(sb), hex(pa), hex(tb), hex(pb), aa.hex(), bb.hex())
                            for j in (4, 6, 8, 10):
                                self.pointer((sb, int.from_bytes(aa[j:j+2], 'little')),
                                             (tb, int.from_bytes(bb[j:j+2], 'little')), 'text' if j < 8 else 'script')
                        elif kind == 'bg' and typ >= 7: pass  # hidden item
                        elif kind == 'bg' and typ in (5, 6):
                            assert self.read(self.source, sb, pa, 2) == self.read(self.target, tb, pb, 2)
                            self.pointer((sb, self.word(self.source, sb, pa+2)), (tb, self.word(self.target, tb, pb+2)))
                        else: self.pointer((sb, pa), (tb, pb))
                    sc += stride; tc += stride

    def side_tables(self):
        import re
        def locate(label, size, ignored):
            bank, addr = self.m['symbols'][label]
            raw = self.read(self.source, bank, addr, size)
            pattern = b''.join(b'.' if i in ignored else re.escape(bytes([v])) for i,v in enumerate(raw))
            hits = list(re.finditer(b'(?=(' + pattern + b'))', self.target[bank*0x4000:(bank+1)*0x4000], re.S))
            assert len(hits) == 1, (label, 'table candidates', len(hits))
            target = hits[0].start()+0x4000
            self.add((bank, addr),(bank,target))
            return bank, addr, target
        # The standard scripts table is the first structure of its bank.
        bank, addr = self.m['symbols']['StdScripts']
        assert addr == 0x4000
        self.add((bank,addr),(bank,addr))
        for i in range(len(self.m['constants']['stdScriptOrder'])):
            a = self.read(self.source,bank,addr+i*3,3)
            b = self.read(self.target,bank,addr+i*3,3)
            assert a[0] == b[0]
            self.pointer((a[0],int.from_bytes(a[1:],'little')),(b[0],int.from_bytes(b[1:],'little')))
        count=len(self.m['constants']['phoneContactOrder'])
        ignored={i*12+j for i in range(count) for j in (5,6,7,9,10,11)}
        bank,addr,target=locate('PhoneContacts',count*12,ignored)
        for i in range(count):
            for j in (5,9):
                a=self.read(self.source,bank,addr+i*12+j,3)
                b=self.read(self.target,bank,target+i*12+j,3)
                self.pointer((a[0],int.from_bytes(a[1:],'little')),(b[0],int.from_bytes(b[1:],'little')))
        count=len([x for x in self.m['constants']['specialCallOrder'] if x != 'SPECIALCALL_NONE'])
        ignored={i*6+j for i in range(count) for j in (0,1,3,4,5)}
        bank,addr,target=locate('SpecialPhoneCallList',count*6,ignored)
        for i in range(count):
            a=self.read(self.source,bank,addr+i*6+3,3)
            b=self.read(self.target,bank,target+i*6+3,3)
            self.pointer((a[0],int.from_bytes(a[1:],'little')),(b[0],int.from_bytes(b[1:],'little')))

    def scripts_walk(self):
        while self.queue:
            a, b = self.queue.pop()
            if (a, b) in self.seen: continue
            self.seen.add((a, b))
            ab, aa = a; bb, ba = b
            name = 'unread'
            try:
                for _ in range(2048):
                    op = self.read(self.source, ab, aa)[0]
                    top = self.read(self.target, bb, ba)[0]
                    locale_landmark = op == 0x44 and top == 0xa3 and self.m['romSha1'] != 'f4cd194bdee0d04ca4eac29e09b8e4e9d818c133'
                    locale_wait = op == 0x55 and top == 0x54 and self.m['romSha1']=='f4cd194bdee0d04ca4eac29e09b8e4e9d818c133'
                    assert op == top or locale_landmark or locale_wait, ('opcode', hex(aa), hex(ba), op)
                    info = self.ops[str(op)]; name, size = info['name'], info['size']
                    if name == 'givepoke': size = 8 if self.read(self.source, ab, aa+4)[0] else 4
                    target_size = 2 if locale_landmark else size
                    x = self.read(self.source, ab, aa+1, size); y = self.read(self.target, bb, ba+1, target_size)
                    ignored = set()
                    def near(i=0, kind='script'):
                        ignored.update((i, i+1))
                        self.pointer((ab, int.from_bytes(x[i:i+2], 'little')), (bb, int.from_bytes(y[i:i+2], 'little')), kind)
                    def far(i=0, kind='script'):
                        ignored.update((i, i+1, i+2))
                        self.pointer((x[i], int.from_bytes(x[i+1:i+3], 'little')), (y[i], int.from_bytes(y[i+1:i+3], 'little')), kind)
                    if name in ('writetext','jumptext','jumptextfaceplayer'): near(kind='text')
                    elif name in ('farwritetext','farjumptext'): far(kind='text')
                    elif name in ('scall','sjump','iffalse','iftrue','sdefer','stopandsjump'): near()
                    elif name in ('ifequal','ifnotequal','ifgreater','ifless'): near(1)
                    elif name in ('farscall','farsjump'): far()
                    elif name == 'winlosstext': near(0, 'text'); near(2, 'text')
                    elif name == 'getstring' and locale_landmark:
                        assert x[2] == y[1], 'Landmark buffer changed'
                        ignored.update(range(3))
                    elif name == 'getstring': near(kind='string')
                    elif name == 'givepoke' and size == 8: near(4, 'string'); near(6, 'string')
                    elif name in ('applymovement','changemapblocks','autoinput','pokemart'): near(1, 'data')
                    elif name == 'callasm': far(kind='code')
                    elif name in ('applymovementlasttalked','givepokemail','checkpokemail','loadmenu','writecmdqueue','elevator','xycompare'): near(kind='data')
                    elif name in ('readmem','writemem','loadmem','memcall','memjump','memcallasm','repeattext'): ignored.update((0, 1))
                    assert all(c == d for i, (c,d) in enumerate(zip(x,y)) if i not in ignored), (name, 'operands', x.hex(), y.hex())
                    self.add((ab, aa), (bb, ba))
                    if name in self.ops['terminators']: break
                    aa += size + 1; ba += target_size + 1
                else: raise ValueError('Script limit')
            except (AssertionError, KeyError, IndexError, ValueError) as e:
                self.failures.append({'source':a,'target':b,'reason':str(e),'last_source':[ab,aa],'last_target':[bb,ba],'op':name})

    def text_far_walk(self):
        queue = list(self.texts.items())
        seen = set()
        while queue:
            key, target = queue.pop()
            if key in seen: continue
            seen.add(key)
            a = tuple(int(x,16) for x in key.split(':'))
            b = tuple(target)
            x, y = self.read(self.source,*a,4), self.read(self.target,*b,4)
            if x[0] == 0x16:
                assert y[0] == 0x16
                aa = (x[3],int.from_bytes(x[1:3],'little'))
                bb = (y[3],int.from_bytes(y[1:3],'little'))
                self.pointer(aa,bb,'text')
                queue.append((f'{aa[0]:02x}:{aa[1]:04x}',list(bb)))

    def wrapper_walk(self):
        import re
        pattern=re.compile(rb'(?:\x16.[\x40-\x7f]'+(rb'[\x6f-\x71]' if self.m['romSha1']=='f4cd194bdee0d04ca4eac29e09b8e4e9d818c133' else rb'[\x64-\x66]')+rb'\x50)+',re.S)
        for bank in range(128):
            a=list(pattern.finditer(self.source[bank*0x4000:(bank+1)*0x4000]))
            b=list(pattern.finditer(self.target[bank*0x4000:(bank+1)*0x4000]))
            if [len(x[0]) for x in a] != [len(x[0]) for x in b]: continue
            for x,y in zip(a,b):
                for i in range(0,len(x[0]),5):
                    sa,ta=x.start()+i+(0x4000 if bank else 0),y.start()+i+(0x4000 if bank else 0)
                    self.pointer((bank,sa),(bank,ta),'text')
        self.text_far_walk()

    def common_text_banks(self, symbols):
        for bank in (0x64,0x65,0x66) if self.m['romSha1'] != 'f4cd194bdee0d04ca4eac29e09b8e4e9d818c133' else (0x1b,0x1c,0x1d):
            addresses = sorted({addr for b,addr in symbols.values() if b == bank and 0x4000 <= addr < 0x8000})
            if not addresses: continue
            assert addresses[0] == 0x4000
            cursor = 0x4000
            for i,addr in enumerate(addresses):
                source_end,shape = text_shape(self.source,bank,addr)
                target_end,target_shape = text_shape(self.target,bank,cursor)
                assert shape == target_shape, ('Common text grammar',bank,hex(addr),hex(cursor),shape,target_shape)
                key=f'{bank:02x}:{addr:04x}'
                if key in self.texts: assert self.texts[key] == [bank,cursor], ('Graph/text-bank disagreement',key)
                self.pointer((bank,addr),(bank,cursor),'text')
                if i+1<len(addresses) and source_end != addresses[i+1]:
                    gap=self.read(self.source,bank,source_end,addresses[i+1]-source_end)
                    assert set(gap)=={0x50}, ('Noncontiguous text',hex(bank),hex(addr),gap.hex())
                    assert self.read(self.target,bank,target_end,len(gap))==gap
                    target_end+=len(gap)
                cursor = target_end

    def interpolate_texts(self,symbols):
        battlebank=0x20 if self.m['romSha1']=='f4cd194bdee0d04ca4eac29e09b8e4e9d818c133' else 0x40
        banks=(battlebank,0x6f,0x70,0x71) if battlebank==0x20 else (battlebank,0x64,0x65,0x66)
        for bank in banks:
            if battlebank==0x20 and bank==battlebank:
                import re
                labels=set(re.findall(r'^([A-Za-z_][A-Za-z0-9_]*):',(ROOT/getattr(self,'battle_source','build/pokecrystal/data/text/battle.asm')).read_text(),re.M))
                starts=sorted({addr for name,(b,addr) in symbols.items() if b==bank and name in labels})
            else:
                starts=sorted({addr for name,(b,addr) in symbols.items() if b==bank and 0x4000<=addr<0x8000 and (bank!=battlebank or addr>=symbols['CoinVendor_CancelText'][1])})
            starts=sorted(set(starts)|{a for b,a in getattr(self,'extra_text_starts',[]) if b==bank})
            # Older retail symbol files omit anonymous/unused records. Walk
            # every intervening command stream so omitted labels cannot shift
            # the correspondence of later named texts.
            expanded=set(starts)
            for left,right in zip(starts,starts[1:]):
                end=text_shape(self.source,bank,left)[0]
                while end<right:
                    if self.read(self.source,bank,end)[0]==0x50:
                        end+=1
                        continue
                    expanded.add(end)
                    end=text_shape(self.source,bank,end)[0]
                assert end==right,('Overlapping text labels',bank,hex(left),hex(right),hex(end))
            starts=sorted(expanded)
            # Pure common-text banks begin with their first source record.
            if bank!=battlebank:self.pointer((bank,0x4000),(bank,0x4000),'text')
            if offset(bank,starts[0]) not in self.maps:
                import re
                before=self.read(self.source,bank,starts[0]-32,32)
                ignored=set()
                for j in range(len(before)-2):
                    if before[j] in (0xcd,0xc3,0xc2,0xca,0xd2,0xda,0xc4,0xcc,0xd4,0xdc):ignored.update((j+1,j+2))
                pattern=b''.join(b'.' if j in ignored else re.escape(bytes([v])) for j,v in enumerate(before))
                hits=list(re.finditer(b'(?=('+pattern+b'))',self.target[bank*0x4000:(bank+1)*0x4000],re.S))
                assert len(hits)==1,('Battle text boundary anchor',len(hits))
                self.pointer((bank,starts[0]),(bank,hits[0].start()+0x4000+32),'text')
            i=0
            while i<len(starts):
                off=offset(bank,starts[i])
                if off in self.maps:i+=1;continue
                begin=i
                while i<len(starts) and offset(bank,starts[i]) not in self.maps:i+=1
                stop=i
                assert begin>0
                prev=starts[begin-1]
                target_prev=next(iter(self.maps[offset(bank,prev)]))%0x4000+0x4000
                try:cursor=text_shape(self.target,bank,target_prev)[0]
                except ValueError as e:raise ValueError((str(e),'previous',hex(prev),[n for n,place in symbols.items() if place==(bank,prev)],list(self.maps[offset(bank,prev)])))
                pending=[]
                source_cursor=text_shape(self.source,bank,prev)[0]
                for addr in starts[begin:stop]:
                    gap=addr-source_cursor
                    assert gap>=0 and set(self.read(self.source,bank,source_cursor,gap)).issubset({0x50})
                    for _ in range(gap):
                        if self.read(self.target,bank,cursor)[0]==0x50:cursor+=1
                    end,shape=text_shape(self.source,bank,addr)
                    if self.read(self.source,bank,addr)[0]!=0x50 and self.read(self.target,bank,cursor)[0]==0x50 and self.read(self.target,bank,cursor+1)[0]!=0x50:cursor+=1
                    tend,tshape=text_shape(self.target,bank,cursor)
                    # Italian deliberately blanks unused mobile texts. The
                    # two-byte empty string 50,50 replaces text+terminator.
                    if self.read(self.target,bank,cursor,2)==b'\x50\x50' and self.read(self.source,bank,end-2,2)==b'\x50\x50':tend=cursor+2
                    assert sorted(shape)==sorted(tshape) or (getattr(self,'allow_italian_pc',False) and any(symbols.get(n)==(bank,addr) for n in ('_PlayersPCWithdrewItemsText','_PlayersPCDepositItemsText','_ItemsTossOutHowManyText','_ItemsDiscardedText','_MartFinalPriceText'))) or (getattr(self,'allow_empty_mobile',False) and self.read(self.target,bank,cursor,2) in (b'\x00\x57',b'\x00\x58',b'\x50\x50')),('Interpolated text grammar',hex(bank),hex(addr),hex(cursor),shape,tshape)
                    pending.append((addr,cursor));cursor=tend;source_cursor=end
                if stop<len(starts):
                    expected=next(iter(self.maps[offset(bank,starts[stop])]))%0x4000+0x4000
                    assert cursor<=expected and set(self.read(self.target,bank,cursor,expected-cursor)).issubset({0x50}),('Text anchor boundary',hex(bank),hex(starts[begin]),hex(cursor),hex(expected))
                else:
                    tail=self.target[offset(bank,cursor):(bank+1)*0x4000]
                    if bank!=battlebank:assert set(tail).issubset({0,0xff,0x50}),('Text bank padding',hex(bank),hex(cursor))
                for a,b in pending:self.pointer((bank,a),(bank,b),'text')


def text_shape(rom,bank,addr):
    pos=offset(bank,addr);shape=[];inside=False
    for _ in range(8192):
        c=rom[pos];pos+=1
        if inside:
            if c in (0x57,0x58):return pos%0x4000+0x4000,shape
            if c==0x50:inside=False
            continue
        if c==0:inside=True
        elif c in (0x50,0x57,0x58):return pos%0x4000+0x4000,shape
        elif c in (1,2,3,4,9,0x0c,0x14,0x16):
            lengths={1:2,2:3,3:2,4:4,9:3,0x0c:1,0x14:1,0x16:3}
            if c in (1,2,9,0x14):shape.append(c)
            pos+=lengths[c]
        elif c in (5,6,7,0xa,0xb,0xd,0xe,0xf,0x10,0x11,0x12,0x13,0x15):pass
        else:raise ValueError(('Unknown text command',hex(c),hex(bank),hex(addr),hex(pos)))
    raise ValueError('Unterminated text')


def run(game, lang):
    manifest = json.loads((ROOT/f'build/upstream-engine/tools/rom_manifest_{game}.json').read_text())
    inv = json.loads((ROOT/'build/gb-rom-inventory.json').read_text())
    source = Path(next(x['file'] for x in inv if x['sha1']==manifest['romSha1'])).read_bytes()
    spec = next(x for x in json.loads((ROOT/'build/european-inputs.json').read_text()) if x.get('game')==game and x.get('language')==lang)
    target = Path(spec['file']).read_bytes()
    assert hashlib.sha1(source).hexdigest()==manifest['romSha1']
    assert hashlib.sha1(target).hexdigest()==spec['sha1']
    ops = json.loads((ROOT/f'build/{"crystal" if game=="crystal" else "gold"}-opcodes.json').read_text())
    if game=='crystal' and lang=='it':
        return crystal_italian(source,target,manifest,ops,spec)
    mapper = Mapper(source,target,manifest,ops)
    mapper.valid_scripts=set(json.loads((ROOT/f'build/{game}-valid-script-keys.json').read_text()))
    mapper.maps_walk(); mapper.side_tables(); mapper.scripts_walk(); mapper.text_far_walk(); mapper.wrapper_walk()
    if game == 'crystal' and lang=='es':
        direct=json.loads((ROOT/'build/crystal-es-authoritative-offsets.json').read_text())
        for off,target in direct.items():
            mapper.maps[int(off)]={target}
            sb,sa=int(off)//16384,int(off)%16384+(0x4000 if int(off)>=16384 else 0)
            if f'{sb:02x}:{sa:04x}' in mapper.texts:mapper.texts[f'{sb:02x}:{sa:04x}']=[target//16384,target%16384+(0x4000 if target>=16384 else 0)]
        authoritative=json.loads((ROOT/'build/crystal-es-symbols.json').read_text())
        for name,place in authoritative.items():
            off=offset(*manifest['symbols'][name]) if manifest['symbols'][name][1]<0x8000 else None
            if off is None:continue
            mapper.maps[off]={offset(*place)}
            if name in manifest['text']['labels']:
                mapper.texts[f'{manifest["symbols"][name][0]:02x}:{manifest["symbols"][name][1]:04x}']=place
    if True:
        import re
        symbols = {}
        for line in (ROOT/('build/pokecrystal/pokecrystal.sym' if game=='crystal' else f'build/pokegold/poke{game}.sym')).read_text().splitlines():
            hit=re.fullmatch(r'([0-9a-fA-F]+):([0-9a-fA-F]+) (\S+)',line)
            if hit: symbols[hit[3]]=(int(hit[1],16),int(hit[2],16))
        mapper.interpolate_texts(symbols)
    report = {'game':game,'language':lang,'sha1':spec['sha1'],'texts':mapper.texts,'strings':mapper.strings,
              'mapped':{str(k):next(iter(v)) for k,v in mapper.maps.items() if len(v)==1},
              'conflicts':{str(k):sorted(v) for k,v in mapper.maps.items() if len(v)>1},'failures':mapper.failures}
    (ROOT/f'build/{game}-{lang}-relocation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(game,lang,'texts',len(mapper.texts),'scripts',len(mapper.seen),'failures',len(mapper.failures),'conflicts',len(report['conflicts']))


def crystal_italian(source,target,manifest,ops,spec):
    """Bridge exact US -> exact ES symbols -> IT event/text structures.

    IT blanks unused mobile records, simplifies five menu messages, and has
    different text-end padding. Each complete common bank must terminate in
    padding and every encountered map/script anchor must agree.
    """
    import copy
    from build_european_gb import read_symbols
    from relocate_gb_refs import recover
    es_audit=json.loads((ROOT/'build/crystal-es-relocation.json').read_text())
    inputs=json.loads((ROOT/'build/european-inputs.json').read_text())
    es_spec=next(x for x in inputs if x.get('game')=='crystal' and x.get('language')=='es')
    es=Path(es_spec['file']).read_bytes()
    assert hashlib.sha1(es).hexdigest()==es_audit['sha1']
    m=copy.deepcopy(manifest)
    m['symbols'].update(json.loads((ROOT/'build/crystal-es-symbols.json').read_text()))
    symbols=read_symbols(ROOT/'build/pokecrystal-es/pokecrystal-es.sym')
    x=Mapper(es,target,m,ops)
    x.valid_scripts=set()
    for key in json.loads((ROOT/'build/crystal-valid-script-keys.json').read_text()):
        bank,addr=(int(z,16) for z in key.split(':'))
        off=es_audit['mapped'].get(str(offset(bank,addr)))
        if off is not None:x.valid_scripts.add(f'{off//16384:02x}:{off%16384+16384:04x}')
    x.maps_walk();x.side_tables();x.scripts_walk();x.text_far_walk()
    x.extra_text_starts=list(es_audit['texts'].values())
    x.battle_source='build/pokecrystal-es/data/text/battle.asm'
    x.allow_empty_mobile=True;x.allow_italian_pc=True
    x.interpolate_texts(symbols)
    mapped={k:next(iter(x.maps[v])) for k,v in es_audit['mapped'].items() if v in x.maps and len(x.maps[v])==1}
    evidence={}
    for label in ('ItemNames','PokemonNames','TrainerClassNames','MoveNames','MoveDescriptions','ItemDescriptions','Font','FontBattleExtra'):
        src=offset(*manifest['symbols'][label]);mid=es_audit['mapped'][str(src)]
        if str(src) in mapped:continue
        try:
            try:dest,refs=recover(es,target,mid//16384,mid%16384+16384)
            except ValueError:
                dest,refs=recover(es,target,mid//16384,mid%16384+16384-1);dest+=1
        except ValueError:
            if label in ('MoveNames','PokemonNames','TrainerClassNames'):
                from build_european_gb import Builder
                gold=Builder('gold','it');gold.gen2()
                cat={'MoveNames':'move_names.lua','PokemonNames':'species_names.lua','TrainerClassNames':'trainer_class_names.lua'}[label]
                spans=[v['parts'][0] for v in gold.cats[cat].values() if 'parts' in v]
                first=min(v['off'] for v in spans);last=max(v['off']+v['size'] for v in spans)+1
                block=gold.rom[first:last];dest=target.find(block)
                assert dest>=0 and target.find(block,dest+1)<0,(label,'unique complete names block')
                mapped[str(src)]=dest;evidence[label]={'matching_name_block_bytes':len(block)}
                continue
            # Fixed-font slots/section starts are verified against source bytes
            # or table structure by the profile builder.
            if label in ('Font','FontBattleExtra','ItemNames','TrainerClassNames','PokemonNames'):dest=mid;refs=[]
            else:raise
        mapped[str(src)]=dest;evidence[label]=refs
    texts={}
    for key,mid in es_audit['texts'].items():
        off=offset(*mid)
        if off in x.maps and len(x.maps[off])==1:
            v=next(iter(x.maps[off]));texts[key]=[v//16384,v%16384+16384]
    report={'game':'crystal','language':'it','sha1':spec['sha1'],'texts':texts,'strings':{},'mapped':mapped,
            'conflicts':{str(k):sorted(v) for k,v in x.maps.items() if len(v)>1},'failures':x.failures,'evidence':evidence,'bridgeSha1':es_audit['sha1']}
    assert not report['failures'] and not report['conflicts']
    (ROOT/'build/crystal-it-relocation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('crystal it texts',len(texts),'mapped',len(mapped),'failures',len(x.failures))


if __name__=='__main__':
    import sys
    run(*sys.argv[1:])
