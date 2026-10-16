local function wait(n) for _=1,n do coroutine.yield() end end
return function(game)
 local ok,err=xpcall(function()
  local version=require('src.core.GameVersion').get()
  local lang=assert(os.getenv('QA_LANGUAGE'))
  local e=assert(game.mods.exports.german_rom_source,'mod did not load')
  assert(e.status==(lang=='en' and 'english' or 'active') and e.language==lang,'Wrong language state')
  print('LANGUAGE_LOAD '..require('src.link.Json').encode({game=version,language=lang,seconds=e.loadSeconds,cacheHit=e.coverage and e.coverage.cacheHit,translated=e.coverage and e.coverage.translated,total=e.coverage and e.coverage.total}))
  if os.getenv('QA_MODE')=='load' then love.event.quit();return end
  if love.setDeprecationOutput then love.setDeprecationOutput(false) end
  local Text=require('src.core.game3.rom_text')
  assert(Text.plain('OtherText_Yes')==(lang=='pt-BR' and 'SIM' or 'YES'))
  local function capture(name)
   wait(50);require('src.ui.game3.map_name_popup').dismiss()
   game.capturePath=os.getenv('SHOT_DIR')..'/'..version..'-'..lang..'-'..name..'.png'
   for _=1,600 do if not game.capturePath then break end;wait(1) end
   assert(not game.capturePath,'Screenshot timeout')
   print('LANGUAGE_CAPTURE',version,lang,name)
  end
  game:returnToTitle({skipIntro=true});wait(420);capture('title')
  local prefix=version=='ruby' and 'RU_' or 'SA_'
  local Map=require('src.core.game3.map')
  game:_handleBootAction({action='new_game',name='TEST',gender=0,start={map=prefix..'OLDALE_TOWN',x=6,y=17,facing='up'}})
  wait(90);assert(game.phase=='field');capture('center')
  assert(Map.load(nil,game,prefix..'OLDALE_TOWN',{x=14,y=7,facing='up'}));capture('mart')
  assert(Map.load(nil,game,prefix..'OLDALE_TOWN_POKEMON_CENTER_1F',{x=7,y=4,facing='up'}))
  local Message=require('src.ui.game3.message')
  local Hud=require('src.ui.game3.hud')
  assert(loadfile(os.getenv('GERMAN_MOD_ROOT')..'/tests/ptbr_nurse_live.lua'))()(game,capture,lang)
  assert(Map.load(nil,game,prefix..'OLDALE_TOWN',{x=6,y=17,facing='up'}));wait(60)
  require('src.core.game3.rng').SeedRng(12345)
  assert(require('src.core.game3.party').giveMon(game.session,1,15,nil,{fixedPersonality=0}))
  if version=='sapphire' and lang=='pt-BR' then
   local authored=dofile(os.getenv('GERMAN_MOD_ROOT')..'/mod/profiles/sapphire_ptbr_authored.lua')
   local Font=require('src.ui.game3.frlg_font')
   local entries=0
   for key,row in pairs(authored) do
    if key:find('DexDescription_',1,true)==1 then
     local plain=Text.plain(key);local lines=0
     for line in plain:gmatch('[^\n]+') do
      lines=lines+1;assert(Font.measure(line)<=208,'Pokédex line too wide: '..key..' / '..line)
     end
     assert(lines<=3,'Pokédex page too long: '..key);entries=entries+1
    end
   end
   assert(entries==405,'Unexpected authored dex page count: '..entries)
   local Dex=require('src.ui.game3.rse.pokedex')
   for _,case in ipairs({{63,'abra'},{375,'metang'}}) do
    local s=Dex.showCaughtMon(Dex.speciesOf(case[1]),{session=game.session,personality=0,otId=1,otSecretId=0})
    assert(s.caught.dexNum==case[1],'Wrong National Dex species in fixture')
    wait(250);capture('dex-'..case[2]..'-1')
    game:keypressed('z');wait(1);game:keyreleased('z');wait(100)
    assert(s.descriptionPage==1,'Pokédex did not flip to second page')
    capture('dex-'..case[2]..'-2');Dex.reset()
   end
   print('LANGUAGE_DEX_OK',version,entries,'authored pages, native font widths')
  end
  local Summary=require('src.ui.game3.summary_menu')
  Summary.openMenu(game.session.party,1,{session=game.session,page=1});capture('summary');Summary.close()
  local mon=game.session.party[1];mon.moves={33};mon.pp={35};mon.maxPp={35}
  local Runtime=require('src.core.game3.runtime');local Battle=require('src.core.game3.battle')
  local outcome
  assert(require('src.core.game3.battle_bridge').startWild(Runtime._mod,game,{species=19,level=2},{autoFight=true,done=function(result)outcome=result end}))
  for _=1,600 do if Battle.isActive() then break end;wait(1) end
  assert(Battle.isActive());wait(240);capture('battle')
  for _=1,450 do if outcome then break end;game:keypressed('z');wait(1);game:keyreleased('z');wait(5) end
  assert(outcome=='win','Battle did not complete: '..tostring(outcome))
  wait(90);assert(game.phase=='field' and not Battle.isActive())
  assert(game:saveGame());local saved=assert(require('src.core.SaveData').load());assert(saved.engine=='game3')
  print('LANGUAGE_BATTLE_OK',version,lang,outcome)
  print('LANGUAGE_LIVE_OK',version,lang)
 end,debug.traceback)
 if not ok then print('LANGUAGE_LIVE_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
