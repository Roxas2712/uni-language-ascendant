-- Fingerprint every localized byte and effective registry value. This is a
-- losslessness check, separate from native gameplay and performance evidence.
return function(game)
 local ok,err=xpcall(function()
  local e=assert(game.mods.exports.german_rom_source)
  assert(e.status=='active','Language profile not active')
  local W=require('src.import.LuaWriter')
  local function hash(s)return love.data.encode('string','hex',love.data.hash('string','sha256',s))end
  local result={game=require('src.core.GameVersion').get(),language=e.language,
   luaStartupKiB=collectgarbage('count'),assets={},registries={},assetBytes=0,assetCount=0,ownOperations=0,
   loadSeconds=e.loadSeconds,cacheKey=e.cacheKey,cacheHit=e.coverage.cacheHit}
  for path,bytes in pairs(e.assets)do
   result.assets[path]=hash(bytes);result.assetBytes=result.assetBytes+#bytes;result.assetCount=result.assetCount+1
  end
  if require('src.core.GameVersion').generation()==3 then
   for _,name in ipairs({'text','rom_text','pokemon','moves','items','trainers','strings'})do
    local registry=game.mods.content[name]
    if registry then
     local rows={};result.registries[name]=rows
     for key,value in registry:each()do rows[key]=hash(W.encode(value))end
     for _,ops in pairs(registry.ops)do for _,op in ipairs(ops)do
      if op.owner=='german_rom_source' then result.ownOperations=result.ownOperations+1 end
     end end
    end
   end
  end
  local report={};for k,v in pairs(e.coverage)do if k~='cacheHit' then report[k]=v end end
  result.coverage=hash(W.encode(report));result.coverageData=report
  result.luaBeforeCollectionKiB=collectgarbage('count')
  collectgarbage('collect');result.luaRetainedKiB=collectgarbage('count')
  local path=assert(os.getenv('SHOT_DIR'))..'/'..result.game..'-'..e.language..'-snapshot.json'
  local f=assert(io.open(path,'w'));f:write(require('src.link.Json').encode(result));f:close()
  print('CACHE_SNAPSHOT_OK',result.game,e.language,result.assetCount,result.ownOperations,result.loadSeconds,result.luaRetainedKiB)
 end,debug.traceback)
 if not ok then print('CACHE_SNAPSHOT_FAILED',err)end
 love.event.quit(ok and 0 or 1)
end
