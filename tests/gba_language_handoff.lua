-- Read real native naming/ability/trainer consumers after a language handoff.
-- These assertions do not supply displayed text or replace game dialogue.
return function(game,language)
 local Cache=require('src.import.CacheFs');local V=require('src.core.GameVersion');local version=V.get()
 if language=='en'then assert(Cache._germanROMOverlay==nil,'English retained the previous language payload');print('LIVE_GBA_UI_OK',version,language,'native English');return end
 local s=assert(Cache._germanROMOverlay);assert(s.bus==require('src.mods.Runtime').events)
 local W=require('src.core.SaveSerializer');local Naming=require('src.ui.game3.naming')
 local path='data/generated/gba/naming/manifest.lua';local count=0
 if s.files[path]then
  local expected=assert(loadstring(s.files[path]))()
  local native=assert(loadstring(assert(Cache._germanROMRead(version..'/'..path))))()
  for i,key in ipairs(Naming.TEMPLATE_ORDER)do
   local actual,wanted=Naming.templateFromManifest(native,key),expected.templates[i]
   if wanted then assert(actual and W.encode(actual)==W.encode(wanted),'Native naming localization lost: '..key);count=count+1
   else assert(actual==nil,'Native naming invented an absent template: '..key)end
  end
  assert(count==(expected.layout=='rs'and 4 or 5),'Wrong native naming template coverage')
  assert(W.encode(require('src.ui.game3.rse.scene_kit').loadLua(path))==W.encode(expected),'Native manifest consumer lost the selected language')
 end
 local abilities,classes=0,0
 if not game.mods.exports.ORIGAMI_ASCENDANT then
  local Pokemon=require('src.core.game3.pokemon')
  for id,name in pairs(s.display.abilities or {})do assert(Pokemon.abilityName(id)==name,'Native ability localization lost at '..tostring(id));abilities=abilities+1 end
  local Trainers=require('src.core.game3.scripting.trainers')
  for id=1,24 do local row=Trainers.get(id)
   if row and s.display.classes[row.class]then assert(row.className==s.display.classes[row.class],'Native trainer class localization lost');classes=classes+1 end
  end
  assert(abilities>0 and classes>0,'No native ability/trainer consumers exercised')
 end
 print('LIVE_GBA_UI_OK',version,language,'naming',count,'abilities',abilities,'trainer classes',classes)
end
