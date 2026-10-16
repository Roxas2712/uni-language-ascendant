-- Real-ROM extraction comparison against independently extracted DE caches.
local root=assert(arg[1]);local caches=assert(arg[2]);local roms=assert(arg[3])
local Json=require('src.link.Json')
local specs={
 {'firered','german-rom-mod-reference','Pokemon - Feuerrote Edition (Germany).gba'},
 {'sapphire','german-rom-mod-reference','Pokemon - Saphir-Edition (Germany) (Rev 1).gba'},
 {'leafgreen','oasc-de-leafgreen-test','Pokemon - Blattgruene Edition (Germany).gba'},
 {'ruby','oasc-de-ruby-test','Pokemon - Rubin-Edition (Germany).gba'},
 {'emerald','oasc-de-emerald-final-test','Pokemon - Smaragd-Edition (Germany).gba'},
}
local function read(p) local f=assert(io.open(p,'rb'));local b=f:read('*a');f:close();return b end
local function equal(a,b)
 if type(a)~=type(b) then return false end
 if type(a)~='table' then return a==b end
 for k,v in pairs(a) do if not equal(v,b[k]) then return false end end
 for k in pairs(b) do if a[k]==nil then return false end end
 return true
end
for _,s in ipairs(specs) do
 local game,identity,file=unpack(s)
 require('src.core.GameVersion').set(game)
 local base=dofile(caches..'/german-rom-mod-qa/'..game..'/data/generated/gba/scripts/text.lua')
 local target=dofile(caches..'/'..identity..'/'..game..'/data/generated/gba/scripts/text.lua')
 local profile=dofile(root..'/mod/profiles/'..game..'.lua')
 local got={}
 local text={each=function() return pairs(base) end,override=function(_,k,v) got[k]=v end}
 local empty={each=function() return pairs({}) end}
 local mod={content={text=text,rom_text={override=function()end},pokemon=empty,moves=empty,items=empty,trainers=empty}}
 local before=require('src.core.game3.scripting.text_ir').CHARMAP[0xF1]
 local stats=dofile(root..'/mod/translate.lua')(mod,profile,read(roms..'/'..file))
 assert(require('src.core.game3.scripting.text_ir').CHARMAP[0xF1]==before,'shared decoder was not restored')
 local matched,compared,mismatched=0,0,{}
 for key,ir in pairs(got) do
  local k=key
  if k:match('^g3:') then k=string.format('g3:%08x',0x08000000+profile.texts[key][1]) end
  if target[k] then
   compared=compared+1
   if equal(ir,target[k]) then matched=matched+1 else mismatched[#mismatched+1]=key;if #mismatched<3 then print('DIFF',key,Json.encode(ir),Json.encode(target[k])) end end
  end
 end
 assert(#mismatched==0,'Translated dialogue differs from reference')
 table.sort(mismatched)
 local report={game=game,total=stats.total,translated=stats.translated,compared=compared,matched=matched,mismatched=mismatched,missing=stats.missing}
 local f=assert(io.open(root..'/build/'..game..'-coverage.json','w'));f:write(Json.encode(report));f:close()
 print(game,stats.translated..'/'..stats.total,'reference '..matched..'/'..compared)
 for i=1,math.min(8,#mismatched) do print(' MISMATCH',mismatched[i]) end
end
