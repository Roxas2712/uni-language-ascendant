-- Lookup checks only; separate field/battle drivers provide gameplay evidence.
return function(game)
 io.stdout:setvbuf('no')
 local ok,err=xpcall(function()
  assert(game.mods.exports.german_rom_source.status=='active','PT-BR not active')
  local root=os.getenv('GERMAN_MOD_ROOT')..'/tests/'
  assert(loadfile(root..'ptbr_moves_live.lua'))()()
  assert(loadfile(root..'ptbr_abilities_live.lua'))()()
  local Items=require('src.core.game3.items_data');local rows={}
  local own=assert(love.filesystem.load('mods/german_rom_source/ptbr_items.lua'))()
  local ownDescriptions=assert(love.filesystem.load('mods/german_rom_source/ptbr_item_descriptions.lua'))()
  local Font=require('src.ui.game3.frlg_font');local bad={}
  for id=0,376 do
   local row=Items.info(id)
   if row then
    local name=Items.displayName(id)
    rows[#rows+1]={id=id,name=name,description=Items.description(id)}
    if own[id]then assert(name==own[id],'Item name override missing: '..id)end
    local version=require('src.core.GameVersion').get()
    local opts=(version=='ruby' or version=='sapphire') and {font='native_3'} or {}
    if ownDescriptions[id] then
     assert(Items.description(id)==ownDescriptions[id],'Item description override missing: '..id)
     for line in (Items.description(id)..'\n'):gmatch('(.-)\n')do
      assert(Font.measure(line,opts)<=((version=='firered' or version=='leafgreen') and 200 or 104),'Item description exceeds native panel: '..id..'/'..line..'/'..Font.measure(line,opts))
     end
    end
    if Font.measure(name,opts)>80 then bad[#bad+1]={id=id,name=name,width=Font.measure(name,opts)}end
   end
  end
  local version=require('src.core.GameVersion').get()
  local f=assert(io.open(os.getenv('SHOT_DIR')..'/'..version..'-actual-items.json','w'))
  f:write(require('src.link.Json').encode(rows));f:close()
  local exports=game.mods.exports.german_rom_source
  local classCount=0
  for id,row in pairs(assert(love.filesystem.load('mods/german_rom_source/ptbr_classes.lua'))()[version])do
   assert(exports.coverage.display.classes[id]==row.target,'Trainer class missing: '..id)
   assert(Font.measure(row.target)<=208,'Trainer class exceeds dialogue width: '..id)
   classCount=classCount+1
  end
  print('LANGUAGE_TRAINER_CLASSES_OK',classCount)
  local pack=exports.assets['data/generated/gba/region_map/map_sections.lua']
  local areas=assert(loadstring(assert(pack)))()
  local sectionRows={};local english={}
  for id,row in pairs(areas.sections)do
   sectionRows['id_'..id]=row
   for _,word in ipairs({'CITY','TOWN','CAVE','ROAD','ROUTE','ISLAND','TOWER','FOREST','HIDEOUT','CHAMBER','BATTLE','SECRET BASE','NEW MAUVILLE','ANCIENT TOMB','DESERT RUINS','INSIDE OF TRUCK'})do
    if row.name:find('%f[%a]'..word..'%f[%A]') then english[#english+1]={id=id,name=row.name};break end
   end
  end
  areas.sections=sectionRows
  print('LANGUAGE_LOCATION_REMAINDERS '..require('src.link.Json').encode(english))
  assert(#english==0,'English map-location labels remain')
  local f=assert(io.open(os.getenv('SHOT_DIR')..'/'..version..'-actual-labels.json','w'))
  f:write(require('src.link.Json').encode({classes=exports.coverage.display.classes,areas=areas}));f:close()
  print('LANGUAGE_ITEM_LAYOUT '..require('src.link.Json').encode(bad))
  assert(#bad==0,'Item names exceed the compact native list')
  print('LANGUAGE_VOCABULARY_OK',require('src.core.GameVersion').get())
 end,debug.traceback)
 if not ok then print('LANGUAGE_VOCABULARY_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
