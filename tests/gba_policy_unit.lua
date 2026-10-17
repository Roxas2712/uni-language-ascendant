local root=assert(arg[1]);local IR=require('src.core.game3.scripting.text_ir')
local translate=dofile(root..'/mod/translate.lua')
local policy=dofile(root..'/mod/gba/policy.lua')
local ui=dofile(root..'/mod/gba/ui.lua')
local function test(game,language)
 local rules=policy(game,ui[language]);local base={};local writes={}
 for key in pairs(rules)do base[key]=IR.fromAscii('Credit '..key)end
 local empty={each=function()return pairs({})end,patch=function()end}
 local m={content={text={each=function()return pairs(base)end,override=function(_,k,v)writes[k]=v end},
  rom_text={override=function()end},pokemon=empty,moves=empty,items=empty,trainers=empty}}
 local stats=translate(m,{game=game,texts={},fields={MOVE_NAME_LENGTH=12}},string.char(255),rules)
 assert(stats.covered==stats.total and stats.translated==0 and #stats.missing==0)
 for key,rule in pairs(rules)do
  if rule.kind=='retainedProperNames'then assert(writes[key]==base[key],'Credit identity was replaced')
  elseif rule.kind=='inapplicable'then assert(#writes[key]==1 and writes[key][1].t=='eos')
  else assert(IR.toPlain(writes[key],{})==ui[language][({Text_Version=game=='ruby' and'POKéMON RUBY VERSION'or'POKéMON SAPPHIRE VERSION',Category_Translator='Translator',Category_NOAProductTesting='NOA Product Testing',Category_EnglishVersionCoordinators='English Version Coordinators'})[key]])end
 end
 -- Unknown additions must remain visible as gaps; never silently call every
 -- unmapped entry a proper name or mark it translated.
 base.unexpected=IR.fromAscii('New untranslated dialogue')
 local uncovered=translate(m,{game=game,texts={},fields={MOVE_NAME_LENGTH=12}},string.char(255),rules)
 assert(#uncovered.missing==1 and uncovered.missing[1]=='unexpected')
end
for _,game in ipairs({'firered','leafgreen','ruby','sapphire','emerald'})do
 for _,lang in ipairs({'de','es','fr','it'})do test(game,lang)end
end
print('GBA_POLICY_UNIT_OK explicit categories, proper-name identities, regional suffix removal, authored credit roles, unknown-key reporting')
