return function(mod)
 local version=require('src.core.GameVersion').get()
 local function own(file, ...) return assert(loadstring(assert(mod:read(file)),'@rom_language/'..file))(...) end
 local started=love.timer.getTime()
 local language=own('startup.lua')(mod,version,own)
 if language=='en' then
  if require('src.core.GameVersion').generation()==2 then
   own('gb/shared/official_mon_names.lua').installGen2ReturnCompatibility(require('src.script.gen2.Specials'))
  end
  if require('src.core.GameVersion').generation()==2 then own('gb/runtime/asian_fallback.lua')(mod,version,own,language) end
  mod.exports.status='english';mod.exports.language='en';mod.exports.loadSeconds=love.timer.getTime()-started;return
 end
 local required,requirements
 for _,row in ipairs(own('rom_requirements.lua')) do if row.game==version then required=row.base.sha1;requirements=row end end
 local marker=require('src.import.CacheFs').readAt(require('src.core.GameVersion').cachePrefix()..'rom-cache.complete')
 if not required or not marker or marker:sub(-40)~=required then
  mod.exports.status='needs_base';mod.exports.startup.noticeKey='wrongBase'
  mod.log:warn('Language profile needs base SHA-1 %s',tostring(required));return
 end
 local adapters=own('adapters.lua')
 local adapter=assert(adapters[require('src.core.GameVersion').generation()],'No language adapter for this generation')
 if adapter~='main.lua' then own(adapter)(mod,version,own,language);if require('src.core.GameVersion').generation()==2 then own('gb/runtime/asian_fallback.lua')(mod,version,own,language) end;mod.exports.loadSeconds=love.timer.getTime()-started;return end
 local selected,source,info
 for _,entry in ipairs(own('catalog.lua')) do
  if entry.game==version and entry.language==language then
   local candidate=mod.imports:info(entry.sourceId or entry.id)
   if candidate then
    local identity
    for _,row in ipairs(requirements.sources)do
     if row.language==language and row.md5==candidate.md5 and row.size==candidate.size then identity=row end
    end
    assert(identity,'ROM does not match language profile')
    assert(not selected,'Multiple language ROMs installed for this game; keep one active import.')
    selected,source,info=entry,identity,candidate
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
 local W=require('src.import.LuaWriter')
 local function hash(bytes) return love.data.encode('string','hex',love.data.hash('string','sha256',bytes)) end
 local recipe={'compiler-v3',source.sha1,version}
 local paths={'main.lua','catalog.lua','rom_requirements.lua','cache_codec.lua','compiler.lua','translate.lua','extract.lua','assets.lua','world.lua','overlay.lua','gba/ui.lua','gba/policy.lua','gba/runtime.lua',selected.profile,selected.assets,selected.world}
 if selected.authored then paths[#paths+1]=selected.authored;paths[#paths+1]='authored.lua' end
 if language=='pt-BR' then
  paths[#paths+1]='ptbr_moves.lua';paths[#paths+1]='ptbr_names.lua';paths[#paths+1]='ptbr_graphics.lua'
  paths[#paths+1]='ptbr_items.lua';paths[#paths+1]='ptbr_item_descriptions.lua'
  paths[#paths+1]='ptbr_classes.lua'
  paths[#paths+1]='ptbr_text_layout.lua'
  paths[#paths+1]='ptbr_move_descriptions.lua';paths[#paths+1]='ptbr_world_graphics.lua';paths[#paths+1]='ptbr_ability_descriptions.lua'
  paths[#paths+1]='ptbr_summary_graphics.lua';paths[#paths+1]='ptbr_credits.lua';paths[#paths+1]='ptbr_title_graphics.lua';paths[#paths+1]='ptbr_asset_text.lua';paths[#paths+1]='ptbr_pixel_labels.lua';paths[#paths+1]='ptbr_pokenav.lua';paths[#paths+1]='ptbr_pokenav_trainers.lua';paths[#paths+1]='ptbr_side_assets.lua';paths[#paths+1]='ptbr_scene_paths.lua';paths[#paths+1]='ptbr_scene_text.lua';paths[#paths+1]='ptbr_scene_authored.lua';paths[#paths+1]='ptbr_scene_bindings.lua';paths[#paths+1]='ptbr_easy_chat_ui.lua';paths[#paths+1]='ptbr_easy_chat.lua';paths[#paths+1]='ptbr_easy_chat_words.lua'
  paths[#paths+1]='ptbr_types.lua';paths[#paths+1]='ptbr_abilities.lua';paths[#paths+1]='ptbr_gender.lua'
 end
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
 if language=='pt-BR' and (version=='ruby' or version=='sapphire') then
  recipe[#recipe+1]=hash(assert(base:read('data/generated/gba/rse/diploma/manifest.lua')))
 end
 if language=='pt-BR' and (version=='firered' or version=='leafgreen') then
  -- These chrome assets have no FRLG language extractor. Authored labels are
  -- based on the current native assets, so extractor updates invalidate them.
  for _,name in ipairs({'page_swap_lower','page_swap_upper','page_swap_others','back_button'})do
   recipe[#recipe+1]=hash(assert(base:read('data/generated/gba/naming/'..name..'.png')))
  end
  for star=0,4 do for _,suffix in ipairs({'','_female'})do
   recipe[#recipe+1]=hash(assert(base:read('data/generated/gba/trainer_card/front_'..star..suffix..'.rgba')))
  end end
 end
 if language=='pt-BR' then
  local nav=own('ptbr_pokenav.lua')(version);local rows={}
  nav['data/generated/gba/easy_chat/words.lua']=assert(base:read('data/generated/gba/easy_chat/words.lua'))
  for path,bytes in pairs(own('ptbr_side_assets.lua')(version))do nav[path]=bytes end
  for _,path in ipairs(own('ptbr_scene_paths.lua')[version])do nav[path]=assert(base:read(path))end
  for path,bytes in pairs(nav)do rows[#rows+1]=path..':'..hash(bytes)end
  table.sort(rows);recipe[#recipe+1]=table.concat(rows,'\n')
 end
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
 local files,result,materialize=own('compiler.lua')(mod,key,function()
  -- Address maps and authored IR are needed only on a cache miss.
  local profile=own(selected.profile)
  assert(profile.sha1==source.sha1 and profile.md5==info.md5 and profile.size==info.size,'Profile identity mismatch')
  profile.glyphs,profile.assetsPath,profile.worldPath=selected.glyphsPath and own(selected.glyphsPath,selected.language) or selected.glyphs,selected.assets,selected.world
  for code,text in pairs(profile.decodeGlyphs or {}) do profile.glyphs[code]=text end
  if selected.authored then profile.authored=own(selected.authored) end
  if language=='pt-BR' then profile.abilityDescriptions=own('ptbr_ability_descriptions.lua');profile.moveDescriptions=own('ptbr_move_descriptions.lua') end
  profile.metricUnits=selected.language=='pt-BR'
  local chunks={}
  for offset=0,info.size-1,4*1024*1024 do
   local length=math.min(4*1024*1024,info.size-offset)
   local bytes,err=mod.imports:read(selected.sourceId or selected.id,offset,length)
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
  if language=='pt-BR' then
   own('ptbr_pokenav.lua')(version,assets)
   own('ptbr_side_assets.lua')(version,assets)
   report.authoredLabels=own('ptbr_graphics.lua')(assets,version)
   report.authoredSummaryLabels=own('ptbr_summary_graphics.lua')(assets,version)
   report.authoredPixelLabels=own('ptbr_pixel_labels.lua')(assets,version)
   report.shopSignAtlases=own('ptbr_world_graphics.lua')(assets,version)
  end
  -- Retail European UI is a fallback below native ROM string pairs.
  -- PT-BR keeps its separate authored translation and compatibility path.
  local ui=own('gba/ui.lua')[selected.language]
  local uiCount=0
  if ui then
   for source,target in pairs(ui) do proxy.content.strings:override(source,target);uiCount=uiCount+1 end
  end
  local translated=own('translate.lua')(proxy,profile,bytes,ui and own('gba/policy.lua')(version,ui))
  if ui then
   proxy.content.strings:override('SPEED',ui.SPEED)
   translated.authoredUI=uiCount
  end
  if language=='pt-BR' then
   local itemNames=own('ptbr_items.lua');local descriptions=own('ptbr_item_descriptions.lua')
   translated.authoredItemNames=0
   for key,row in proxy.content.items:each()do
    local id=tonumber(row.index)
    if id and itemNames[id] then
     proxy.content.items:patch(key,{name=itemNames[id],description=descriptions[id]})
     translated.authoredItemNames=translated.authoredItemNames+1
    else assert(not id or not row.name or not row.name:match('%a'),'Missing PT-BR item name: '..tostring(id))end
   end
   translated.authoredMoveNames=own('ptbr_names.lua')(proxy,own('ptbr_moves.lua'),354)
   translated.easyChat=own('ptbr_easy_chat.lua')(proxy,own('ptbr_easy_chat_words.lua'),own('ptbr_moves.lua'))
   translated.display.types=own('ptbr_types.lua')
   translated.display.abilities=own('ptbr_abilities.lua')
   -- Portuguese keeps species names. Preserve base names instead of typos
   -- introduced by older language patches, without changing species IDs.
   for id,row in proxy.content.pokemon:each() do proxy.content.pokemon:patch(id,{name=row.name}) end
  end
  if profile.authored then
   translated.authored=own('authored.lua')(proxy,profile.authored)
   local missing={}
   for _,key in ipairs(translated.missing) do
    if profile.authored[key] then translated.translated=translated.translated+1 else missing[#missing+1]=key end
   end
   translated.missing=missing
   -- Authored PT-BR corrections are applied after native extraction.
   translated.covered=translated.translated+#translated.retainedProperNames+#translated.inapplicable
  end
  if language=='pt-BR' then
   local classes=assert(own('ptbr_classes.lua')[version]);local originals={}
   for key,row in proxy.content.text:each()do
    local id=key:match('^gTrainerClassNames%[(%d+)%]$')
    if id then originals[tonumber(id)]=row end
   end
   for id,row in pairs(classes)do
    assert(hash(W.encode(assert(originals[id])))==row.sourceSha256,'Trainer class source changed: '..id)
    translated.display.classes[id]=row.target
    proxy.content.text:override('gTrainerClassNames['..id..']',{{t='text',s=row.target},{t='eos'}})
   end
   own('ptbr_asset_text.lua')(assets,version,proxy,operations)
   report.sceneText=own('ptbr_scene_text.lua')(assets,own('ptbr_scene_paths.lua')[version],proxy,operations,own('ptbr_scene_authored.lua'),own('ptbr_scene_bindings.lua'))
   report.pokenavUnresolved=own('ptbr_pokenav.lua')(version,assets,proxy,operations,own('ptbr_pokenav_trainers.lua'))
  end
  if selected.preserveTitle then
   for path in pairs(assets) do if path:find('/title/',1,true) then assets[path]=nil end end
  end
  if language=='pt-BR' then
   report.authoredTitleLabels=own('ptbr_title_graphics.lua')(assets,version)
   report.authoredCreditHeadings=own('ptbr_credits.lua')(assets,version)
  end
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
  translated.display.glyphs=profile.renderGlyphs
  if next(translated.display.types) then assets['data/generated/gba/pokemon/type_names.lua']=W.encode(translated.display.types) end
  -- Report the final cache payload, including authored labels and generated
  -- names, after edition-specific assets have been filtered.
  report.count,report.bytes=0,0
  for _,data in pairs(assets) do report.count=report.count+1;report.bytes=report.bytes+#data end
  return {files=assets,operations=operations,report=translated}
 end,{lazyAssets=true})
 if result.display.genderPlaceholders then own('ptbr_gender.lua')() end
 local active=own('overlay.lua')(mod,version,files,result.display,own('ptbr_easy_chat_ui.lua'),materialize)
 if language~='pt-BR' then own('gba/runtime.lua')(mod,version,active) end
 own('compat.lua')(mod)
 mod.exports.loadSeconds=love.timer.getTime()-started
 mod.exports.status='active'
 mod.exports.coverage=result
 mod.exports.language=selected.language
 mod.exports.cacheKey=key
 mod.log:info('ROM language %s: %s, %d/%d texts (%s).',selected.language,version,result.translated,result.total,result.cacheHit and 'cached' or 'compiled')
end
