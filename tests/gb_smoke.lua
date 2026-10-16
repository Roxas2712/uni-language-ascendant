local function wait(n) for _=1,n do coroutine.yield() end end
return function(game)
 local ok,err=xpcall(function()
  local v=require('src.core.GameVersion').get()
  local e=assert(game.mods.exports.german_rom_source,'Mod not loaded')
  assert(e.status=='active',tostring(e.status))
  assert(game.data.pokemon.BULBASAUR.name=='BISASAM','Species name missing')
  assert(e.coverage.dialogue>1000,'Dialogue coverage too low')
  print('GB_COUNTS',v,e.coverage.dialogue,e.coverage.assets,e.coverage.cacheHit and 'warm' or 'cold')
  local baseRoot=love.filesystem.getSaveDirectory()..'/'..v..'/data/generated/'
  local function same(a,b)
   if type(a)~=type(b) then return false end
   if type(a)~='table' then return a==b end
   for k,x in pairs(a) do if not same(x,b[k]) then return false end end
   for k in pairs(b) do if a[k]==nil then return false end end
   return true
  end
  local base=assert(loadfile(baseRoot..'pokemon.lua'))()
  for id,row in pairs(base) do if type(row)=='table' and row.id then
   local active=assert(game.data.pokemon[id])
   for _,field in ipairs({'baseStats','types','catchRate','baseExp','growthRate','learnset','evolutions','tmhm','eggMoves'}) do
    assert(same(row[field],active[field]),'Mechanical species field changed: '..id..'.'..field)
   end
  end
  end
  base=assert(loadfile(baseRoot..'moves.lua'))()
  for id,row in pairs(base) do if type(row)=='table' and row.id then for _,field in ipairs({'power','accuracy','pp','effect','type','effectChance'}) do
   assert(same(row[field],game.data.moves[id][field]),'Mechanical move field changed: '..id..'.'..field)
  end end end
  -- Decode every compiled catalog and compare to the corrected development
  -- reference. No translations from this reference ship in the ZIP.
  local f=assert(io.open(os.getenv('GERMAN_MOD_ROOT')..'/build/gb-reference/'..v..'.json','rb'))
  local ref=require('src.link.Json').decode(f:read('*a'));f:close()
  local function subset(a,b,path)
   assert(type(a)==type(b),'Type mismatch '..path)
   if type(a)~='table' then assert(a==b,'Text mismatch '..path);return end
   for k,value in pairs(a) do local refValue=b[k];if refValue==nil then refValue=b[tostring(k)] end;subset(value,refValue,path..'/'..tostring(k)) end
  end
  local count=0
  for path,bytes in pairs(e.assets) do
   local name=path:match('^lang/(.+%.lua)$')
   if name and ref[name] and name~='charmap.lua' then
    local data=assert(require('src.core.SaveSerializer').decode(bytes,{maxBytes=16*1024*1024,maxNodes=500000,maxDepth=40}))
    subset(data,ref[name],name);count=count+1
   end
  end
  assert(count>10)
  wait(5)
  print('GB_SMOKE_OK',v)
 end,debug.traceback)
 if not ok then print('GB_SMOKE_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
