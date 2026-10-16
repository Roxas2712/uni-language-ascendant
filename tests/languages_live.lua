local function wait(n) for _=1,n do coroutine.yield() end end
return function(game)
 local ok,err=xpcall(function()
  local lang=assert(os.getenv('QA_LANGUAGE'))
  local e=assert(game.mods.exports.german_rom_source,'mod did not load')
  assert(e.status==(lang=='en' and 'english' or 'active'),e.status)
  assert(e.language==lang,'wrong active language')
  local Json=require('src.link.Json')
  print('LANGUAGE_LOAD '..Json.encode({language=lang,seconds=e.loadSeconds,cacheHit=e.coverage and e.coverage.cacheHit,
   translated=e.coverage and e.coverage.translated,total=e.coverage and e.coverage.total}))
  if os.getenv('QA_MODE')=='load' then love.event.quit();return end
  if love.setDeprecationOutput then love.setDeprecationOutput(false) end
  local Text=require('src.core.game3.rom_text')
  local Pokemon=require('src.core.game3.pokemon')
  local expected={fr={'OUI','BULBIZARRE','ENGRAIS'},it={'SÌ','BULBASAUR','ERBAIUTO'},es={'SÍ','BULBASAUR','ESPESURA'},de={'JA','BISASAM','NOTDÜNGER'},en={'YES','BULBASAUR','OVERGROW'}}
  assert(Text.plain('gText_Yes')==expected[lang][1],Text.plain('gText_Yes'))
  assert(Pokemon._names[1]==expected[lang][2],Pokemon._names[1])
  assert(Pokemon.abilityName(65)==expected[lang][3],Pokemon.abilityName(65))
  if lang~='en' then
   assert(e.coverage.translated>15500,'text coverage too low')
   local naming=assert(loadstring(e.assets['data/generated/gba/naming/manifest.lua']))()
   assert(#naming.keyboard.chars[1][1]==((lang=='it' or lang=='es') and 8 or 9),'wrong keyboard layout')
  end
  local function capture(name)
   wait(50)
   require('src.ui.game3.map_name_popup').dismiss()
   game.capturePath=os.getenv('SHOT_DIR')..'/'..lang..'-'..name..'.png'
   for _=1,600 do if not game.capturePath then break end;wait(1) end
   assert(not game.capturePath,'screenshot timeout');wait(2)
   print('LANGUAGE_CAPTURE',lang,name)
  end
  game:returnToTitle({skipIntro=true});wait(420);capture('title')
  local Map=require('src.core.game3.map')
  game:_handleBootAction({action='new_game',name='TEST',gender=0,start={map='EM_OLDALE_TOWN',x=6,y=17,facing='up'}})
  wait(60);assert(game.phase=='field')
  capture('center')
  assert(Map.load(nil,game,'EM_OLDALE_TOWN',{x=14,y=7,facing='up'}));capture('mart')
  local nurse=Text.plain('gText_WouldYouLikeToRestYourPkmn')
  print('LANGUAGE_NURSE',lang,nurse)
  require('src.ui.game3.hud').openMessage(game,nurse);wait(10);require('src.ui.game3.message').advance();capture('dialogue')
  game:_handleBootAction({action='new_game',name='TEST',gender=0,start={map='EM_OLDALE_TOWN',x=6,y=17,facing='up'}})
  wait(60)
  require('src.core.game3.rng').SeedRng(12345)
  assert(require('src.core.game3.party').giveMon(game.session,1,15,nil,{fixedPersonality=0}))
  local Summary=require('src.ui.game3.summary_menu')
  Summary.openMenu(game.session.party,1,{session=game.session,page=1});capture('summary');Summary.close()
  assert(game:saveGame(),'save failed')
  local saved=assert(require('src.core.SaveData').load());assert(saved.engine=='game3')
  print('LANGUAGE_LIVE_OK',lang)
 end,debug.traceback)
 if not ok then print('LANGUAGE_LIVE_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
