-- Exhaustive key and battle-variable audit against private owned inputs.
local root,game,romPath,basePath=assert(arg[1]),assert(arg[2]),assert(arg[3]),assert(arg[4])
local function read(path)local f=assert(io.open(path,'rb'));local b=f:read('*a');f:close();return b end
local J=require('src.link.Json');local IR=require('src.core.game3.scripting.text_ir')
local p=dofile(root..'/mod/profiles/'..game..'_ptbr.lua')
local authored=dofile(root..'/mod/profiles/'..game..'_ptbr_authored.lua')
local bytes=read(romPath);local base=J.decode(read(basePath))
for code,ch in pairs(assert(loadfile(root..'/mod/latin_glyphs.lua'))('pt-BR')) do IR.CHARMAP[code]=ch end
for code,ch in pairs(p.decodeGlyphs or {}) do IR.CHARMAP[code]=ch end
local function tokens(ir)
 local out={}
 for _,s in ipairs(ir) do if s.t=='bph' then out[s.code]=(out[s.code] or 0)+1 end end
 return out
end
local count,battles=0,0
for key,source in pairs(base) do
 local row=p.texts[key];local own=authored[key]
 assert(row or own,'Missing text: '..key)
 count=count+1
 if own or not row[3] or row[3]=='fragment' then
  local before=tokens(source)
  local target=own and own.target or IR.decode(bytes:sub(row[1]+1,row[1]+(row[4] or 16384)),{dialect=IR.dialectOf(game),battle=row[2] or next(before)~=nil})
  assert((row and row[3]=='fragment') or target[#target].t=='eos','Unterminated text: '..key)
  if next(before) then
   local after=tokens(target)
   for code,n in pairs(before) do assert(after[code]==n,'Lost battle variable '..code..': '..key) end
   for code,n in pairs(after) do assert(before[code]==n,'Added battle variable '..code..': '..key) end
   battles=battles+1
  end
 end
end
assert(count==13457 and battles>0)
assert(IR.toPlain(IR.decode(string.char(0x44,0x45,0x40,0x41,0x42,255),{dialect='ruby'}),{})=='VELOCIDADE')
print('GEN3_PTBR_PROFILE_OK',game,count,'keys',battles,'battle-variable texts')
