-- Developer-only export. Pixels remain under ignored build/.
local root=assert(os.getenv('ULA_ROOT'))
package.path=root..'/build/upstream-engine/?.lua;'..package.path
local J=require('src.link.Json')
local function read(p)local f=assert(io.open(p,'rb'));local s=f:read('*a');f:close();return s end
local function write(p,s)local f=assert(io.open(p,'wb'));f:write(s);f:close() end
function love.load()
 local ok,err=xpcall(function()
  local p=J.decode(read(os.getenv('ULA_GFX_PLAN')))
  local m=p.manifest
  local I=require('src.import.ImageWriter')
  local E=require('src.import.RomExtractorGen2').new(read(p.rom),m)
  E.edition=p.game
  local needed={};local current
  local original=E.symbol
  E.symbol=function(self,name)
   current=name;needed[name]=needed[name] or {size=0}
   local out=original(self,name)
   needed[name].bank=out.bank;needed[name].address=out.address
   return out
  end
  local symbols=E.symbols
  E.symbols=setmetatable({},{__index=function(_,name)
   if symbols[name] then current=name;needed[name]=needed[name] or {size=0,bank=symbols[name][1],address=symbols[name][2]};return symbols[name] end
  end})
  local byte=E.rom.byte
  E.rom.byte=function(self,b,a)
   if current and needed[current] and needed[current].bank==b then
    local d=a-needed[current].address
    if d>=0 and d<8192 then needed[current].size=math.max(needed[current].size,d+1)end
   end
   return byte(self,b,a)
  end
  local rb=E.rom.bytes
  E.rom.bytes=function(self,b,a,n)
   if current and needed[current] and needed[current].bank==b then
    local d=a-needed[current].address
    if d>=0 and d<4096 then needed[current].size=math.max(needed[current].size,d+n) end
   end
   return rb(self,b,a,n)
  end
  local decompress=E.decompressLz3Symbol
  E.decompressLz3Symbol=function(self,label)
   local raw=decompress(self,label);needed[label].lz=true;needed[label].size=#raw;return raw
  end
  E.save=function(_,image,path)write(p.out..'/'..path:gsub('/','__'),image:encode('png'):getString()) end
  E.write=function()end
  local result={}
  result.title=E:extractTitle()
  result.menu={pokedex=E:pokedexGfx(),billsPc=E:billsPcGfx(),pokegear=E:pokegearGfx(),trainerCard=E:trainerCardGfx()}
  local function raw(label,size,w,h,path,bits,ink)
   local s=E:symbol(label);local bytes=E.rom:bytes(s.bank,s.address,size)
   local image=(bits==1 and I.decode1bpp or I.decode2bpp)(bytes,w,h,bits==1 or label=='NamingScreenGFX_Cursor')
   if ink then image:mapPixel(function(_,_,r)return 0,0,0,r<.5 and 1 or 0 end)end
   E:save(image,path)
  end
  raw('PackMenuGFX',1536,128,48,'pack/menu.png',2)
  raw('PackGFX',960,40,96,'pack/pack.png',2)
  local s=E:symbol('DrawPocketName.tilemap');result.menu.pack={pocketName={}}
  local cells=E.rom:bytes(s.bank,s.address,60)
  for block=0,3 do local row={};for i=1,15 do row[i]=cells[block*15+i]end;result.menu.pack.pocketName[block+1]=row end
  raw('FontBattleExtra',192,96,8,'battle/hud/hp_bar.png',2)
  raw('EnemyHPBarBorderGFX',32,32,8,'battle/hud/enemy_border.png',1)
  raw('HPExpBarBorderGFX',48,48,8,'battle/hud/player_border.png',1)
  -- This fixed-size font section immediately precedes the HP border.
  local hp=E:symbol('EnemyHPBarBorderGFX')
  E:save(I.decode2bpp(E.rom:bytes(hp.bank,hp.address-272,272),136,8),'menu/stats_tiles.png')
  result.menu.stats={sheet='assets/generated/menu/stats_tiles.png',tiles=17,firstTile=0x31}
  for name,size,w,h,bits in (function()local rows={
   {'NamingScreenGFX_Border',16,8,8,2,'border'}, {'NamingScreenGFX_Cursor',32,8,16,2,'cursor'},
   {'NamingScreenGFX_MiddleLine',8,8,8,1,'middleline'},{'NamingScreenGFX_UnderLine',8,8,8,1,'underline'}}
   local i=0;return function()i=i+1;local v=rows[i];if v then return unpack(v)end end end)() do
   raw(name,size,w,h,'naming/'..(name:match('_([^_]+)$'):lower())..'.png',bits)
  end
  write(p.report,J.encode({needed=needed,layouts=result}))
  print('GFX_EXPORT_OK',p.game)
 end,debug.traceback)
 if not ok then print('GFX_EXPORT_FAILED',err)end
 love.event.quit(ok and 0 or 1)
end
