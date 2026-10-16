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
  expected['pt-BR']={'SIM','BULBASAUR','ENORME'}
  assert(Text.plain('gText_Yes')==expected[lang][1],Text.plain('gText_Yes'))
  assert(Pokemon._names[1]==expected[lang][2],Pokemon._names[1])
  assert(Pokemon.abilityName(65)==expected[lang][3],Pokemon.abilityName(65))
  if lang=='pt-BR' then
   local Font=require('src.ui.game3.frlg_font')
   for ch,id in pairs({['ã']=0xF4,['õ']=0xF5,['Ã']=0xF1,['Õ']=0xF2,['í']=0x21,['Í']=0x0C}) do
    assert(Font.glyphId(ch)==id,'Wrong Portuguese font cell: '..ch)
   end
   assert(Text.plain('gText_RestoredPkmnToFullHealth'):find('Missão',1,true),'Portuguese tilde not decoded')
   local Runtime=require('src.mods.Runtime')
   local bus=Runtime.events;Runtime.events={}
   assert(Font.glyphId('ã')==0,'Portuguese glyph override leaked after deactivation')
   Runtime.events=bus;assert(Font.glyphId('ã')==0xF4)
  end
  if lang~='en' then
   assert(e.coverage.translated>15500,'text coverage too low')
   local naming=assert(loadstring(e.assets['data/generated/gba/naming/manifest.lua']))()
   assert(#naming.keyboard.chars[1][1]==((lang=='it' or lang=='es' or lang=='pt-BR') and 8 or 9),'wrong keyboard layout')
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
  assert(Map.load(nil,game,'EM_OLDALE_TOWN_POKEMON_CENTER_1F',{x=7,y=4,facing='up'}))
  local nurse=Text.plain('gText_WouldYouLikeToRestYourPkmn')
  print('LANGUAGE_NURSE',lang,nurse)
  require('src.ui.game3.hud').openMessage(game,nurse);wait(10);require('src.ui.game3.message').advance();capture('dialogue')
  if lang=='pt-BR' then
   require('src.ui.game3.message').close()
   local restored=Text.plain('gText_RestoredPkmnToFullHealth'):match('\n\n(.+)')
   require('src.ui.game3.hud').openMessage(game,assert(restored),{speed=0})
   capture('accents')
  end
  game:_handleBootAction({action='new_game',name='TEST',gender=0,start={map='EM_OLDALE_TOWN',x=6,y=17,facing='up'}})
  wait(60)
  require('src.core.game3.rng').SeedRng(12345)
  assert(require('src.core.game3.party').giveMon(game.session,1,15,nil,{fixedPersonality=0}))
  local Summary=require('src.ui.game3.summary_menu')
  Summary.openMenu(game.session.party,1,{session=game.session,page=1});capture('summary');Summary.close()
  assert(game:saveGame(),'save failed')
  local saved=assert(require('src.core.SaveData').load());assert(saved.engine=='game3')
  if lang=='pt-BR' or os.getenv('QA_BATTLE')=='1' then
   local Runtime=require('src.core.game3.runtime')
   local Battle=require('src.core.game3.battle')
   require('src.ui.game3.message').close()
   -- A fixed damaging move keeps the smoke battle finite; Bulbasaur's
   -- normal level-15 first slot is Growl, which autoFight repeats forever.
   game.session.party[1].moves={33};game.session.party[1].pp={35};game.session.party[1].maxPp={35}
   local outcome
   assert(require('src.core.game3.battle_bridge').startWild(Runtime._mod,game,{species=19,level=2},
    {autoFight=true,done=function(result)outcome=result end}))
   for _=1,600 do if Battle.isActive() then break end;wait(1) end
   assert(Battle.isActive(),'Wild battle failed to start')
   wait(240);capture('battle')
   for _=1,300 do
    if outcome then break end
    game:keypressed('z');wait(1);game:keyreleased('z');wait(5)
   end
   local Ui=require('src.core.game3.battle.ui')
   local Anim=require('src.core.game3.battle.anim')
   local Seq=require('src.core.game3.battle.anim_seq')
   print('BATTLE_DIAGNOSTIC',game.phase,Battle._phase,Anim.busy(),Ui._showing,#Ui._queue,Seq._i,Seq._waiting,Seq._waitingMsg)
   assert(outcome=='win','Wild battle did not complete: '..tostring(outcome)..' / '..tostring(Battle._phase))
   print('LANGUAGE_BATTLE_OK',lang,outcome)
  end
  print('LANGUAGE_LIVE_OK',lang)
 end,debug.traceback)
 if not ok then print('LANGUAGE_LIVE_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
