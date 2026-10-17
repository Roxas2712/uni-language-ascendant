-- In-memory reads only. The event owner and bus identity make this overlay
-- inactive immediately when the loader removes the mod or replaces its bus.
return function(mod,game,files,display)
  local Cache=require('src.import.CacheFs')
  local Runtime=require('src.mods.Runtime')
  local Version=require('src.core.GameVersion')
  local marker='mod.german_rom_source.overlay'
  mod.events:on(marker,function() end)
  local state={bus=Runtime.events,game=game,files=files,display=display}
  Cache._germanROMOverlay=state
  local function active()
    local s=Cache._germanROMOverlay
    return s and Runtime.events==s.bus and Runtime.wants(marker) and Version.get()==s.game and s
  end
  if not Cache._germanROMRead then
    Cache._germanROMRead=Cache.readAt
    Cache.readAt=function(path,...)
      local s=active()
      if s and type(path)=='string' then
        local prefix=s.game..'/'
        if path:sub(1,#prefix)==prefix then
          local data=s.files[path:sub(#prefix+1)]
          if data then return data end
        end
      end
      return Cache._germanROMRead(path,...)
    end
    -- FRLG boot art also uses filename-based LÖVE reads. Resolve just the
    -- generated PNGs owned by this overlay, including those direct loads.
    local imageData=love.image.newImageData
    local newImage=love.graphics.newImage
    local function imageBytes(path)
      local s=active()
      if not s or type(path)~='string' or not path:match('%.png$') then return nil end
      local prefix=s.game..'/'
      if path:sub(1,#prefix)==prefix then path=path:sub(#prefix+1) end
      return s.files[path]
    end
    love.image.newImageData=function(path,...)
      local data=imageBytes(path)
      if data then return imageData(love.data.newByteData(data)) end
      return imageData(path,...)
    end
    love.graphics.newImage=function(path,...)
      local data=imageBytes(path)
      if data then return newImage(imageData(love.data.newByteData(data)),...) end
      return newImage(path,...)
    end
    local Indexed=require('src.core.game3.indexed_png')
    local indexedLoad=Indexed.load
    Indexed.load=function(path)
      local data=imageBytes(path)
      if data then return Indexed.decode(data,Indexed.loveInflate) end
      return indexedLoad(path)
    end
    local function manifest(path)
      local s=active()
      local source=s and s.files[path]
      if not source then return nil end
      s.tables=s.tables or {}
      if not s.tables[path] then s.tables[path]=assert(loadstring(source,'@german/'..path))() end
      return s.tables[path]
    end
    local Machine=require('src.ui.game3.rse.gba_machine')
    local machineManifest=Machine.manifest
    Machine.manifest=function(self,path) return manifest(path) or machineManifest(self,path) end
    local Kit=require('src.ui.game3.rse.scene_kit')
    local kitLua=Kit.loadLua
    Kit.loadLua=function(path) return manifest(path) or kitLua(path) end
    -- pokeruby/src/title_screen.c, GERMAN: 64x64 banner, x=108/172,
    -- y goal=84 (the US runtime assumes x=98/162 and y=66).
    local Title=require('src.ui.game3.rs.title')
    for _,name in ipairs({'bannerLeftCb','bannerRightCb'}) do
      local callback=Title[name]
      Title[name]=function(self,s)
        local state=active()
        if not state or (state.game~='ruby' and state.game~='sapphire') or state.display.language~='de' then return callback(self,s) end
        if s._germanBanner then s.y=s.y-18 else s.x=s.x+10;s._germanBanner=true end
        callback(self,s)
        s.y=s.y+18
      end
    end
    local Pokemon=require('src.core.game3.pokemon')
    local original=Pokemon.abilityName
    Pokemon.abilityName=function(id,...)
      local s=active()
      return s and s.display.abilities[id] or original(id,...)
    end
    local Trainers=require('src.core.game3.scripting.trainers')
    local trainer=Trainers.get
    Trainers.get=function(id,...)
      local row=trainer(id,...)
      local s=active()
      if s and row then row.className=s.display.classes[row.class] or row.className end
      return row
    end
  end
  -- A worker has a separate Lua state and cannot see our scoped overlay.
  -- Route owned atlases through the cache-aware synchronous decoder.
  local dataset=require('src.core.game3.dataset').cache()
  if not dataset._languageWorkerSpec then
    dataset._languageWorkerSpec=dataset.assetWorkerSpec
    local write=dataset.write
    dataset.write=function(self,path,bytes)
      local s=active()
      local pairRoot=path:match('^(data/generated/gba/native/[^/]+)/')
      if s and pairRoot and s.files[pairRoot..'/mids.idx'] then
        s.files[path]=bytes
        return true
      end
      return write(self,path,bytes)
    end
    dataset.assetWorkerSpec=function(self,root,kind,key)
      local s=active()
      if s and s.files[root..'/'..tostring(key)..'/mids.idx'] then return nil end
      return self._languageWorkerSpec(self,root,kind,key)
    end
  end
  require('src.core.game3.tileset_native').invalidate()
  require('src.core.game3.gba_ppu').clearCache()
  require('src.ui.game3.rse.scene_kit').resetCaches()
  require('src.ui.game3.rse.mapsec').reset()
  mod.exports.assets=files
  return active
end
