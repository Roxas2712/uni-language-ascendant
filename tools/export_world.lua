-- Developer-only: map canonical US pair names to the selected ROM's tilesets.
local engine,game,romPath,digest,outPath=unpack(arg)
package.path=engine..'/?.lua;'..package.path
require('src.core.GameVersion').set(game)
local V=require('src.import.gba.versions');V.select(digest)
local bytes=assert(io.open(romPath,'rb')):read('*a')
local rom=setmetatable({_raw=bytes,size=#bytes}, {__index=require('src.import.gba.rom')})
local version=assert(V.lookup(digest))
local catalog=require('src.import.gba.map_catalog');catalog.rebuildIndex()
local census=assert(require('src.import.gba.map_tree').walk(rom,version))
local order,by=catalog.allOrder(census,{})
catalog.registerOrder(rom,version,order,by)
local result={maps={},pairs={}}
for _,id in ipairs(order) do
 local pair=V.MAPS[id].pair;result.maps[id]=pair
 local p=V.TILESET_PAIRS[pair]
 result.pairs[pair]={primary=V.TILESETS[p.primary],secondary=V.TILESETS[p.secondary]}
end
local f=assert(io.open(outPath,'w'));f:write(require('src.import.LuaWriter').encode(result));f:close()
print('WORLD_METADATA_OK',game,#order)
