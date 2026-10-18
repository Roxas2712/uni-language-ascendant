return function(game)
 local ok,err=xpcall(function()
  if love.setDeprecationOutput then love.setDeprecationOutput(false)end
  local e=assert(game.mods.exports.german_rom_source);local v=require('src.core.GameVersion').get()
  local native=v=='crystal'and 'ja'or 'ko';local name=native=='ja'and 'テスト'or '테스트'
  local mode=os.getenv('QA_MODE');local Font=require('src.render.Font');local Naming=require('src.ui.gen2.NamingScreen')
  local save=assert(require('src.core.gen2.Save').load(v));assert(save.player.name==name and save.party[1].nickname==name)
  if mode=='switch-request'then
   assert(e.status=='active'and e.language==native)
   local Shell=require('src.core.HostShell');local old=Shell.restart;local restarts=0;Shell.restart=function()restarts=restarts+1 end
   local yes,why=e.startup.choose('en');Shell.restart=old;assert(yes and why=='restart'and restarts==1)
   local options=require('src.core.SaveData').loadOptions();assert(options.modOptions.german_rom_source.language=='auto')
   print('ASIAN_SWITCH_REQUEST_OK',v)
  else
   assert(e.status=='english'and e.language=='en'and e.asianNameFont==native,'English/font selection')
   assert(game.data.pokemon.BULBASAUR.name=='BULBASAUR','Native species translation leaked')
   assert(require('src.core.Strings')('YES')=='YES','Native UI translation leaked')
   for _,span in ipairs(Font.split(name))do assert(span.code and span.code~=0x7f,'Native save-name glyph missing after switch')end
   local naming=Naming.new(game,{type='player',initial=name});assert(naming:rows()[1][1]=='A','Native keyboard leaked')
   naming:deleteCharacter();assert(naming.text==(native=='ja'and 'テス'or '테스'),'English editing split a Unicode name')
   game:continueGame(save)
   game.world:setMap('CHERRYGROVE_CITY',18,12,'down',{via='boot',continue=true})
   naming.text=name;game.stack:push(naming)
   for _=1,3 do coroutine.yield()end
   game.capturePath=os.getenv('SHOT_DIR')..'/'..v..'-en-native-name.png'
   for _=1,300 do if not game.capturePath then break end;coroutine.yield()end
   assert(not game.capturePath,'English screenshot timeout')
   print('ASIAN_SWITCH_ENGLISH_OK',v,'saved names readable, English text and keyboard restored')
  end
 end,debug.traceback)
 if not ok then print('ASIAN_SWITCH_FAILED',err)end
 love.event.quit(ok and 0 or 1)
end
