-- Importer invariants only; these synthetic records are not translation evidence.
local root=assert(arg[1]);local W=require('src.import.LuaWriter')
local function ir(s)return {{t='text',s=s},{t='eos'}}end
local original={a=ir('A shared source'),b=ir('A shared source'),c=ir('A unique source'),dynamic={{t='player'},{t='text',s=' suffix'},{t='eos'}}}
local ops={{registry='text',method='override',key='a',value=ir('first choice')},{registry='text',method='override',key='b',value=ir('second choice')},{registry='text',method='override',key='c',value=ir('unique target')},{registry='text',method='override',key='dynamic',value={{t='player'},{t='text',s=' translated suffix'},{t='eos'}}}}
local source={ambiguous='A shared source',unique='A unique source',path='A unique source',symbol='A unique source',dynamic=' suffix',ref={key='a',ir=original.a},authored='Authored source'}
package.loaded['src.core.game3.dataset']={cache=function()return {read=function()return W.encode(source)end}end}
-- Identity digest isolates traversal/control validation from cryptography.
love={data={hash=function(_,_,v)return v end,encode=function(_,_,v)return v end}}
local authored={[W.encode('Authored source')]={target='Authored target'}}
local apply=dofile(root..'/mod/ptbr_scene_text.lua')
local registry={each=function()return pairs(original)end}
local files={};local report=apply(files,{'fixture.lua'},{content={text=registry}},ops,authored)
local out=assert(loadstring(files['fixture.lua']))()
assert(out.ambiguous==source.ambiguous,'Ambiguous source selected arbitrary translation')
assert(out.unique=='unique target' and out.path==source.path and out.symbol==source.symbol)
assert(out.dynamic==source.dynamic,'Dynamic source lost placeholder context')
assert(out.ref.key=='a' and out.ref.ir[1].s=='first choice','Exact key did not disambiguate')
assert(out.authored=='Authored target' and report.authored==1)
local files={['fixture.lua']='already localized'};apply(files,{'fixture.lua'},{content={text=registry}},ops,authored)
assert(files['fixture.lua']=='already localized','Existing language pack overwritten')
local mapPath='data/generated/gba/region_map/map_sections.lua'
local files={[mapPath]=W.encode({sections={[0]={id='MAPSEC_FIXTURE',name='Authored source'},[1]={id='MAPSEC_LOCAL',name='Already local'}}})}
apply(files,{mapPath},{content={text=registry}},ops,authored)
local sections=assert(loadstring(files[mapPath]))().sections
assert(sections[0].name=='Authored target' and sections[1].name=='Already local','Imported map corrections lost')
source.authored={{t='player'},{t='text',s='x'},{t='eos'}}
authored={[W.encode(source.authored)]={target=ir('lost player')}}
local ok,err=pcall(apply,{}, {'fixture.lua'},{content={text=registry}},ops,authored)
assert(not ok and err:find('operands changed',1,true),'Control operand removal accepted')
print('SCENE_TEXT_UNIT_OK exact identity, ambiguity, placeholders, metadata, pretranslated packs')

-- An explicit native Help binding resolves duplicate prose only when its
-- complete source (including placeholder identity) still agrees.
source={article='{PC_OWNER} suffix'}
original.help={{t='strvar',n=1},{t='text',s=' suffix'},{t='eos'}}
ops[#ops+1]={registry='text',method='override',key='help',value={{t='strvar',n=1},{t='text',s=' sufixo'},{t='eos'}}}
local files={};apply(files,{'help.lua'},{content={text=registry}},ops,{}, {['help.lua.article']='help'})
assert(assert(loadstring(files['help.lua']))().article=='{PC_OWNER} sufixo')
source.article='{RIVAL} suffix'
local ok,err=pcall(apply,{}, {'help.lua'},{content={text=registry}},ops,{}, {['help.lua.article']='help'})
assert(not ok and err:find('source changed',1,true))
print('HELP_BINDING_UNIT_OK exact placeholder context and changed-source rejection')
