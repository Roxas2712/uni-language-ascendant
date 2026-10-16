local root,lang=assert(arg[1]),assert(arg[2])
local Json=require('src.link.Json')
local function read(path)local f=assert(io.open(path,'rb'));local s=f:read('*a');f:close();return s end
local inputs=Json.decode(read(root..'/build/emerald-new-language-inputs.json'))
local path
for _,r in ipairs(inputs.roms) do if r.language==lang then path=r.staged_file end end
local bytes=read(assert(path))
local p=dofile(root..'/mod/profiles/emerald_'..lang..'.lua')
local IR=require('src.core.game3.scripting.text_ir')
local glyphs=assert(loadfile(root..'/mod/latin_glyphs.lua'))(lang)
local saved={}
for k,v in pairs(glyphs) do saved[k]=IR.CHARMAP[k];IR.CHARMAP[k]=v end
local dialect=IR.dialect('rse')
local bad={};local count=0
for key,v in pairs(p.texts) do
 count=count+1
 if not v[3] then
  local offset=v[1];local pos=offset+1;local unknown={};local terminated=false
  while pos<=math.min(#bytes,offset+16384) do
   local c=bytes:byte(pos)
   if c==255 then terminated=true;break
   elseif c==252 then
    local cmd=bytes:byte(pos+1);if cmd>0x18 then unknown[#unknown+1]='FC'..string.format('%02X',cmd) end
    pos=pos+2+(IR.EXT_ARGS[cmd] or 0)
   elseif c==253 or c==247 or c==248 or c==249 then pos=pos+2
   else
    if not IR.CHARMAP[c] and not IR.LIGATURE[c] and not (dialect.CHARMAP_EXTRA and dialect.CHARMAP_EXTRA[c]) and c~=250 and c~=251 and c~=254 then unknown[#unknown+1]=string.format('%02X',c) end
    pos=pos+1
   end
  end
  if not terminated or #unknown>0 then
   local sample={};for _,seg in ipairs(IR.decode(bytes:sub(offset+1,pos),{dialect='rse',battle=v[2]})) do if seg.s then sample[#sample+1]=seg.s end end
   bad[#bad+1]={key=key,offset=offset,unknown=unknown,terminated=terminated,sample=table.concat(sample)}
  end
 end
end
table.sort(bad,function(a,b)return a.key<b.key end)
local f=assert(io.open(root..'/build/emerald-'..lang..'-text-validation.json','w'));f:write(Json.encode({count=count,bad=bad}));f:close()
print('TEXT_SCAN',lang,count,#bad)
for i=1,math.min(12,#bad) do print(bad[i].key,table.concat(bad[i].unknown,','),bad[i].sample:sub(1,120)) end

local legacy={};local unexpected={}
for _,v in ipairs(bad) do
 local key=v.key:lower()
 local japanese=key:find('jp',1,true) or key:find('japan',1,true)
  or key:find('gstatusconditionstringstable',1,true) or key=='sactiontexts[5]'
 if japanese and v.terminated then legacy[#legacy+1]=v else unexpected[#unexpected+1]=v end
end
print('TEXT_VALIDATION',lang,'mapped',count,'legacyJapanese',#legacy,'unexpected',#unexpected)
assert(#unexpected==0,'Unexpected undecodable localized text; see validation report')

for k in pairs(glyphs) do IR.CHARMAP[k]=saved[k] end
