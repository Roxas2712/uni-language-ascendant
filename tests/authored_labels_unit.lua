-- Registry behavior test. Fixtures are not gameplay/translation evidence.
local W=require('src.import.LuaWriter')
local apply=assert(loadfile(assert(arg[1])..'/mod/authored.lua'))()
love={data={hash=function(_,_,v)return v end,encode=function(_,_,v)return v end}}
local function text(s)return {{t='text',s=s},{t='eos'}} end
local function fixture(source,targets)
 local ops,entries={},{}
 for key,row in pairs(targets) do entries[key]={sourceSha256=W.encode(source[key]),target=row} end
 local function registry(name)
  return {each=function()return pairs(source)end,override=function(_,key,value)ops[#ops+1]={name,key,value}end}
 end
 local mod={content={text=registry('text'),rom_text=registry('rom_text'),strings=registry('strings')}}
 return mod,entries,ops
end
local source={hp=text('HP'),one=text('ITEM'),two=text('ITEM'),long=text('A description longer than the short-label budget.'),space=text(' POKéMON')}
local mod,entries,ops=fixture(source,{hp=text('PS'),one=text('ITEM'),two=text('OBJETO'),long=text('Uma descrição longa.'),space=text(' POKéMON')})
assert(apply(mod,entries)==5)
local strings={};for _,op in ipairs(ops) do if op[1]=='strings' then strings[op[2]]=op[3] end end
assert(strings.HP=='PS' and strings.ITEM==nil,'Ambiguous labels must not leak into context-free menus')
assert(strings['A description longer than the short-label budget.']==nil)
assert(strings.space==' POKéMON','Intentional separator lost')
local m,e,o=fixture({a=text('HP'),b=text('HP')},{a=text('PS'),b=text('PS')});e.b.sourceSha256='wrong'
assert(not pcall(apply,m,e) and #o==0,'Rejected source must not partially mutate registries')
local dynamic={{t='player'},{t='text',s=' arrived.'},{t='eos'}}
local m2,e2,o2=fixture({a=dynamic},{a={{t='player'},{t='text',s=' chegou.'},{t='eos'}}})
assert(apply(m2,e2)==1)
for _,op in ipairs(o2) do assert(op[1]~='strings','Dynamic dialogue became a global literal') end
print('AUTHORED_UNIT_OK short labels, ambiguity, separators, transactional validation, dynamic context')
