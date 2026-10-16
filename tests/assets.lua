return function(game)
  local ok,err=xpcall(function()
    local version=require('src.core.GameVersion').get()
    local exports=assert(game.mods.exports.german_rom_source)
    assert(exports.status=='active')
    local Cache=require('src.import.CacheFs')
    local Blob=require('src.import.CacheBlob')
    local refs={firered='german-rom-mod-reference',sapphire='german-rom-mod-reference',leafgreen='oasc-de-leafgreen-test',ruby='oasc-de-ruby-test',emerald='oasc-de-emerald-final-test'}
    local root=os.getenv('HOME')..'/Library/Application Support/LOVE/'
    local function read(path)
      local f=io.open(path,'rb');if not f then return nil end
      local data=f:read('*a');f:close();return Blob.decode(path,data)
    end
    local checked,different,missing=0,{},{}
    local worldChanged,worldChecked=0,0
    local changedPath
    for path,data in pairs(exports.assets) do
      local base=Cache._germanROMRead(version..'/'..path)
      if base and data~=base then changedPath=path end
      if path:find('/native/',1,true) then
        worldChecked=worldChecked+1
        if base~=data then worldChanged=worldChanged+1 end
      end
      assert(Cache.readAt(version..'/'..path)==data,'overlay not used: '..path)
      local referencePath=path
      local pair=path:match('/native/([^/]+)/')
      if pair then
        local profile=assert(loadfile(os.getenv('GERMAN_MOD_ROOT')..'/mod/profiles/'..version..'_world.lua'))()
        referencePath=path:gsub('/native/'..pair..'/', '/native/'..assert(profile.reference[pair])..'/')
      end
      local reference=read(root..refs[version]..'/'..version..'/'..referencePath)
      if not reference then missing[#missing+1]=path
      else
        checked=checked+1
        if data~=reference then
          if path:match('%.png$') then
            local a=love.image.newImageData(love.filesystem.newFileData(data,'a.png'))
            local b=love.image.newImageData(love.filesystem.newFileData(reference,'b.png'))
            if a:getString()~=b:getString() then different[#different+1]=path end
          elseif path:match('%.idx$') then
            local N=require('src.import.gba.native_pack')
            local a,b=assert(N.decodeIdx(data)),assert(N.decodeIdx(reference))
            local slots={}
            for i,id in ipairs(b.midIds) do slots[id]=i end
            for i,id in ipairs(a.midIds) do
              local j=assert(slots[id], 'Reference lacks metatile '..id)
              for n=1,256 do assert(a.pixels[(i-1)*256+n]==b.pixels[(j-1)*256+n],path..' mid '..id..' pixel '..n) end
            end
          else different[#different+1]=path end
        end
      end
    end
    table.sort(different);table.sort(missing)
    for _,p in ipairs(different) do
      print('ASSET_DIFFERENT',p)
      if p:match('%.lua$') then
        local a=assert(loadstring(exports.assets[p]))()
        local b=assert(loadstring(read(root..refs[version]..'/'..version..'/'..p)))()
        -- These manifests enumerate independent files via pairs(); order has
        -- no meaning. All other metadata must match the reference exactly.
        if a.files and b.files then table.sort(a.files);table.sort(b.files) end
        local function compare(x,y,key)
          if type(x)=='table' and type(y)=='table' then
            for k,v in pairs(x) do compare(v,y[k],key..'.'..tostring(k)) end
            for k in pairs(y) do assert(x[k]~=nil,'Metadata removed: '..key..'.'..tostring(k)) end
          else assert(x==y,'Metadata differs: '..key) end
        end
        compare(a,b,p)
      end
      assert(p:match('%.lua$') or p:match('/intro/meta.json$'),'German artwork differs from independent import: '..p)
    end
    assert(#missing==0,'Generated assets without a reference')
    for _,p in ipairs(missing) do print('ASSET_NO_REFERENCE',p) end
    print('ASSET_COMPARISON',version,checked,#different,#missing)
    print('WORLD_COMPARISON',version,worldChecked,worldChanged)
    print('COMPILE_CACHE',version,exports.coverage.cacheHit)
    if version=='leafgreen' then assert(require('src.core.Strings')('VIRIDIAN CITY')=='VERTANIA CITY','location popup translation') end
    local P=require('src.core.game3.pokemon')
    assert(P.abilityName(65)=='NOTDÜNGER','ability localization')
    local description=require('src.core.game3.summary_data').moveDescription(33,P.moveName(33))
    print('DESCRIPTION_SAMPLE',description)
    assert(description~='---' and not description:find('physical'),'move description localization')
    -- Removing the owner must immediately restore base reads in the same process.
    local imagePath=(version=='leafgreen' or version=='firered') and 'data/generated/gba/intro/title_logo.png' or 'data/generated/gba/title/logo.png'
    assert(love.image.newImageData(love.data.newByteData(exports.assets[imagePath])))
    local path=assert(changedPath,'no translated assets')
    local german=assert(Cache.readAt(version..'/'..path))
    game.mods.events:removeOwner('german_rom_source')
    local english=assert(Cache.readAt(version..'/'..path))
    assert(english~=german,'title overlay did not deactivate')
    assert(P.abilityName(65)=='OVERGROW','ability overlay did not deactivate')
    print('ASSET_LIFECYCLE_OK',version)
  end,debug.traceback)
  if not ok then print('ASSET_TEST_FAILED',err) end
  love.event.quit(ok and 0 or 1)
end
