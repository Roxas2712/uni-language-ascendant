-- Static full-key/battle-token audit against private user-owned inputs.
local root,romPath,basePath=assert(arg[1]),assert(arg[2]),assert(arg[3])
local function read(path)local f=assert(io.open(path,'rb'));local v=f:read('*a');f:close();return v end
local base=require('src.link.Json').decode(read(basePath))
local bytes=read(romPath)
local profile=dofile(root..'/mod/profiles/emerald_ptbr.lua')
local authored=dofile(root..'/mod/profiles/emerald_ptbr_authored.lua')
local IR=require('src.core.game3.scripting.text_ir')
for code,ch in pairs(assert(loadfile(root..'/mod/latin_glyphs.lua'))('pt-BR')) do IR.CHARMAP[code]=ch end
local count,battles,braille=0,0,0
local function placeholders(ir)
 local result={}
 for _,s in ipairs(ir) do if s.t=='bph' then result[s.code]=(result[s.code] or 0)+1 end end
 return result
end
for key,source in pairs(base) do
 local row=assert(profile.texts[key],key);count=count+1
 assert(row[1]>=0 and row[1]<#bytes,'Out-of-bounds text: '..key)
 if row[3] then
  assert(row[3]=='braille_emerald');braille=braille+1
 else
  local before=placeholders(source)
  local ir=authored[key] and authored[key].target or IR.decode(bytes:sub(row[1]+1,row[1]+16384),{dialect='rse',battle=row[2] or next(before)~=nil})
  assert(ir[#ir] and ir[#ir].t=='eos','Unterminated text: '..key)
  if next(before) then
   local after=placeholders(ir)
   for id,n in pairs(before) do assert(after[id]==n,'Lost battle variable: '..key) end
   for id,n in pairs(after) do assert(before[id]==n,'Added battle variable: '..key) end
   battles=battles+1
  end
 end
end
assert(count==15655 and battles>0)
print('PTBR_PROFILE_OK',count,'keys',battles,'battle-variable texts',braille,'braille recipes')
