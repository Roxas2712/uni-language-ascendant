local root=assert(arg[1])
local translate=dofile(root..'/mod/translate.lua')
local IR=require('src.core.game3.scripting.text_ir')
local saved=IR.CHARMAP[0xF1]
local writes={}
local function fakeMod(base)
 local noop=function() end
 local empty={each=function() return pairs({}) end,patch=noop}
 return {content={text={each=function() return pairs(base) end,
   override=function(_,k,v) writes[k]=v end},rom_text={override=noop},
   pokemon=empty,moves=empty,items=empty,trainers=empty}}
end
local function profile(offset,battle)
 return {game='leafgreen',texts={test={offset,battle}},fields={MOVE_NAME_LENGTH=12}}
end
local m=fakeMod({test={{t='text',s='before'},{t='eos'}}})
local stats=translate(m,profile(0),string.char(0xF1,0xF2,0xF3,0xF4,0xF5,0xF6,0x15,255))
assert(writes.test[1].s=='ÄÖÜäöüß','German glyphs')
assert(IR.CHARMAP[0xF1]==saved,'decoder restored on success')
assert(stats.translated==1 and stats.total==1,'coverage')
writes={}
assert(not pcall(translate,m,profile(100),string.char(255)),'out-of-range pointer')
assert(next(writes)==nil,'invalid ROM registered partial output')
assert(IR.CHARMAP[0xF1]==saved,'decoder restored on failure')
assert(not pcall(translate,m,profile(0),string.char(0xBB)),'unterminated text')
writes={}
translate(m,profile(0,true),string.char(0xFD,0x0D,0xFE,0xFC,1,2,255))
assert(writes.test[1].t=='bph' and writes.test[1].code==13,'battle placeholder preserved')
assert(writes.test[2].t=='nl' and writes.test[3].t=='ext','control codes preserved')
for _,case in ipairs({{'pt-BR',{0xF1,0xF2,0xF4,0xF5,0x0C,0x21},'ÃÕãõÍí'},{'fr',{0x2C,0x84,0x64},'erePC'},{'es',{0x52,0xCD,0x6F},'¡Sí'},{'it',{0x5E,0x5F,0x60,0x61,0x62},'POKéMELLA'},{'it',{0x5E,0x5F,0x60,0x61,0x63},'POKéMELLE'}}) do
 local p=profile(0);p.glyphs=assert(loadfile(root..'/mod/latin_glyphs.lua'))(case[1])
 local old={};for k in pairs(p.glyphs) do old[k]=IR.CHARMAP[k] end
 local b={};for _,v in ipairs(case[2]) do b[#b+1]=string.char(v) end;b[#b+1]=string.char(255)
 translate(m,p,table.concat(b));assert(writes.test[1].s==case[3],writes.test[1].s)
 for k in pairs(p.glyphs) do assert(IR.CHARMAP[k]==old[k],'locale decoder leaked') end
end
love={timer={getTime=function() return 0 end}}
local Cache=require('src.import.CacheFs')
Cache.readAt=function() return 'rom-cache:574fa542ffebb14be69902d1d36f1ec0a4afd71e' end
local loadMod=dofile(root..'/mod/main.lua')
require('src.core.GameVersion').set('leafgreen')
local function mainMod(info,read)
 return {exports={},log={warn=function() end},imports={info=function() return info end,read=read},
  read=function(_,file) if file=='session.lua' then return 'return function()return{install=function()end}end' end;if file=='startup.lua' then return "return function() return 'de' end" end;local f=assert(io.open(root..'/mod/'..file));local s=f:read('*a');f:close();return s end}
end
local no=mainMod(nil,function() error('missing ROM was read') end)
loadMod(no);assert(no.exports.status=='needs_import','missing source state')
assert(not pcall(loadMod,mainMod({size=16777216,md5='bad'},function()error('bad ROM read')end)),'wrong hash rejected')
local p=dofile(root..'/mod/profiles/leafgreen.lua')
assert(not pcall(loadMod,mainMod({size=1,md5=p.md5},function()error('bad size read')end)),'wrong size rejected')
print('UNIT_OK glyphs, controls, bounds, atomic extraction, decoder cleanup, missing/wrong ROM')
