return function(mod)
 local version=require('src.core.GameVersion').get()
 local function own(file, ...) return assert(loadstring(assert(mod:read(file)),'@rom_language/'..file))(...) end
 local started=love.timer.getTime()
 local language=own('startup.lua')(mod,version,own)
 if language=='en' then
  if require('src.core.GameVersion').generation()==2 then
   own('gb/shared/official_mon_names.lua').installGen2ReturnCompatibility(require('src.script.gen2.Specials'))
  end
  mod.exports.status='english';mod.exports.language='en';mod.exports.loadSeconds=love.timer.getTime()-started;return
 end
 local required
 for _,row in ipairs(own('rom_requirements.lua')) do if row.game==version then required=row.base.sha1 end end
 local marker=require('src.import.CacheFs').readAt(require('src.core.GameVersion').cachePrefix()..'rom-cache.complete')
 if not required or not marker or marker:sub(-40)~=required then
  mod.exports.status='needs_base';mod.exports.startup.noticeKey='wrongBase'
  mod.log:warn('Language profile needs base SHA-1 %s',tostring(required));return
 end
 local adapters=own('adapters.lua')
 local adapter=assert(adapters[require('src.core.GameVersion').generation()],'No language adapter for this generation')
 if adapter~='main.lua' then own(adapter)(mod,version,own,language);mod.exports.loadSeconds=love.timer.getTime()-started;return end
 local selected,profile,info
 for _,entry in ipairs(own('catalog.lua')) do
  if entry.game==version and entry.language==language then
   local candidate=mod.imports:info(entry.id)
   if candidate then
    local p=own(entry.profile)
    assert(candidate.md5==p.md5 and candidate.size==p.size,'ROM does not match language profile')
    assert(not selected,'Multiple language ROMs installed for this game; keep one active import.')
    selected,profile,info=entry,p,candidate
   end
  end
 end
 if not selected then
  mod.exports.status='needs_import'
  mod.log:warn('Please select a supported language ROM under MODS > Uni-Language Ascendant > Imports.')
  return
 end
 if version=='ruby' or version=='sapphire' then
  assert(require('src.import.gba.versions').BUILD==version,'Uni-Language Ascendant requires the matching USA 1.0 base game.')
 end
 profile.glyphs,profile.assetsPath,profile.worldPath=selected.glyphsPath and own(selected.glyphsPath,selected.language) or selected.glyphs,selected.assets,selected.world
 local W=require('src.import.LuaWriter')
 local function hash(bytes) return love.data.encode('string','hex',love.data.hash('string','sha256',bytes)) end
 local recipe={'compiler-v2',profile.sha1,version}
 local paths={'main.lua','catalog.lua','compiler.lua','translate.lua','extract.lua','assets.lua','world.lua','overlay.lua',selected.profile,selected.assets,selected.world}
 if selected.glyphsPath then paths[#paths+1]=selected.glyphsPath end
 for name in pairs(own('vendor/index.lua')) do paths[#paths+1]='vendor/'..name:gsub('%.','/')..'.lua' end
 table.sort(paths)
 for _,path in ipairs(paths) do recipe[#recipe+1]=path..':'..hash(assert(mod:read(path))) end
 -- Registry input is part of the key: engine updates or another earlier mod
 -- must not reuse patches compiled against different names/dialogue/schema.
 for _,name in ipairs({'text','pokemon','moves','items','trainers'}) do
  local rows={}
  for key,value in mod.content[name]:each() do rows[#rows+1]=tostring(key)..':'..hash(W.encode(value)) end
  table.sort(rows);recipe[#recipe+1]=name..':'..hash(table.concat(rows,'\n'))
 end
 local base=require('src.core.game3.dataset').cache()
 local nativeRoot='data/generated/gba/native/'
 local manifestBytes=assert(base:read(nativeRoot..'manifest.lua'))
 recipe[#recipe+1]=hash(manifestBytes)
 local nativePairs=assert(loadstring(manifestBytes))().pairs
 local atlasKeys={}
 for pair in pairs(nativePairs) do atlasKeys[#atlasKeys+1]=pair..':'..hash(assert(base:read(nativeRoot..pair..'/mids.idx'))) end
 table.sort(atlasKeys);recipe[#recipe+1]=hash(table.concat(atlasKeys,'\n'))
 for _,name in ipairs({'descriptions','ability_names','move_names'}) do
  recipe[#recipe+1]=hash(assert(base:read('data/generated/gba/pokemon/'..name..'.lua')))
 end
 if version=='leafgreen' or version=='firered' then recipe[#recipe+1]=hash(assert(base:read('data/generated/gba/region_map/names.lua'))) end
 local key=hash(table.concat(recipe,'\n'))
 local files,result=own('compiler.lua')(mod,key,function()
  local chunks={}
  for offset=0,info.size-1,4*1024*1024 do
   local length=math.min(4*1024*1024,info.size-offset)
   local bytes,err=mod.imports:read(selected.id,offset,length)
   assert(bytes and #bytes==length,err or 'Incomplete language ROM')
   chunks[#chunks+1]=bytes
  end
  local bytes=table.concat(chunks)
  assert(love.data.encode('string','hex',love.data.hash('string','sha1',bytes))==profile.sha1,'ROM SHA-1 mismatch')
  assert(bytes:sub(0xAD,0xB0)==selected.code and bytes:byte(0xBD)==selected.revision,'ROM header/profile mismatch')
  local operations={}
  local proxy={content={}}
  for _,name in ipairs({'text','rom_text','pokemon','moves','items','trainers','strings'}) do
   local registry=mod.content[name]
   if registry then
    local methods={each=function() return registry:each() end}
    for _,method in ipairs({'override','patch'}) do
     methods[method]=function(_,id,value)
      operations[#operations+1]={registry=name,method=method,key=id,value=value}
     end
    end
    proxy.content[name]=methods
   end
  end
  local assets,report=own('assets.lua')(mod,profile,bytes,own)
  local translated=own('translate.lua')(proxy,profile,bytes)
  if version=='leafgreen' or version=='firered' then
   local sections=assert(loadstring(assert(assets['data/generated/gba/map_sections.lua'])))().sections
   local original=assert(loadstring(assert(base:read('data/generated/gba/region_map/names.lua'))))()
   local names={first=original.first,last=original.last,names={}}
   for id,row in pairs(sections) do
    names.names[id]=row.name
    if original.names[id] then proxy.content.strings:override(original.names[id],row.name) end
   end
   assets['data/generated/gba/region_map/names.lua']=W.encode(names)
  end
  translated.assets=report
  translated.language=selected.language
  translated.display.language=selected.language
  if next(translated.display.types) then assets['data/generated/gba/pokemon/type_names.lua']=W.encode(translated.display.types) end
  return {files=assets,operations=operations,report=translated}
 end)
 own('overlay.lua')(mod,version,files,result.display)
 mod.exports.loadSeconds=love.timer.getTime()-started
 mod.exports.status='active'
 mod.exports.coverage=result
 mod.exports.language=selected.language
 mod.exports.cacheKey=key
 mod.log:info('ROM language %s: %s, %d/%d texts (%s).',selected.language,version,result.translated,result.total,result.cacheHit and 'cached' or 'compiled')
end
