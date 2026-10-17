-- Parser/integration check against actual patched cartridge strings. This is
-- deliberately not gameplay evidence; real NPC QA is a separate test suite.
local root=assert(arg[1]);local game=assert(arg[2]);local file=assert(arg[3])
local profile=dofile(root..'/build/ptbr-qa/'..game..'-profile/profile.lua')
local f=assert(io.open(file,'rb'));local rom=f:read('*a');f:close()
profile.glyphs=assert(loadfile(root..'/mod/latin_glyphs.lua'))('pt-BR')
for k,v in pairs(profile.decodeGlyphs) do profile.glyphs[k]=v end
profile.fields={MOVE_NAME_LENGTH=16}
local IR=require('src.core.game3.scripting.text_ir')
local Json=require('src.link.Json')
f=assert(io.open(root..'/build/ptbr-qa/'..game..'-base-texts.json'));local source=Json.decode(f:read('*a'));f:close()
local writes={text={},rom_text={}}
local mod={content={}}
for _,name in ipairs({'text','rom_text','pokemon','moves','items','trainers'}) do
 mod.content[name]={each=function()return pairs(name=='text' and source or {})end,
 override=function(_,key,value)writes[name][key]=value end,patch=function()error('No gameplay mutations expected')end}
end
local report=dofile(root..'/mod/translate.lua')(mod,profile,rom)
dofile(root..'/mod/ptbr_gender.lua')()
package.loaded['src.core.game3.scripting.space']={bundle={}}
local RomText=require('src.core.game3.rom_text');RomText.overrides=writes.rom_text
local expected={
 [14]={'o','a'},[15]={'O','A'},[16]={'boné','chapéu'},[17]={'ele','ela'},
 [18]={'meu','minha'},[19]={'seu','sua'},[20]={'Seu','Sua'},[21]={'este','esta'},
 [22]={'herói','heroína'},[23]={'ladrão','ladra'},[24]={'mestre','mestra'},
 [25]={'traidor','traidora'},[26]={'invasor','invasora'},[27]={'CAMPEÃO','CAMPEÃ'},
 [28]={'PROFESSOR','PROFESSORA'},[29]={'CRIADOR','CRIADORA'},[30]={'um','uma'},
 [31]={'TREINADOR','TREINADORA'},[32]={'bom','boa'},
}
for code,words in pairs(expected) do
 for gender=0,1 do
  local value=IR.toPlain({{t='ph',code=code,name='ULA_PTBR_GENDER_'..code}},{dialect='frlg',playerGender=gender})
  assert(value==words[gender+1],code..': '..value..' ~= '..words[gender+1])
 end
end
local count=0
for key,ir in pairs(writes.text) do
 for _,seg in ipairs(ir) do
  if seg.t=='ph' and seg.code and seg.code>=14 then
   assert(seg.name=='ULA_PTBR_GENDER_'..seg.code,key);count=count+1
  end
 end
end
assert(count>300,'Actual cartridge gender placeholders were not decoded')
print('FRLG_GENDER_ROM_OK',game,count,'both genders, original cartridge words; parser check only')
