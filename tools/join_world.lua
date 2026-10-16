local root=arg[1]
package.path=root..'/build/upstream-engine/?.lua;'..package.path
local W=require('src.import.LuaWriter')
for _,game in ipairs((arg[2] and {arg[2]} or {'firered','leafgreen','ruby','sapphire','emerald'})) do
 local a=dofile(root..'/build/'..game..'-en-world.lua')
 local b=dofile(root..'/build/'..game..'-de-world.lua')
 local out={pairs={},reference={}}
 for id,pair in pairs(a.maps) do
  local target=assert(b.maps[id],id)
  local value=assert(b.pairs[target])
  if out.pairs[pair] then assert(W.encode(out.pairs[pair])==W.encode(value),'Ambiguous '..pair) end
  out.pairs[pair]=value;out.reference[pair]=target
 end
 local f=assert(io.open(root..'/mod/profiles/'..game..'_world.lua','w'));f:write(W.encode(out));f:close()
end
