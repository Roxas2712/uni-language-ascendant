-- Actual FRLG field scripts and battle execution; no substitute dialogue text.
local function wait(n) for _=1,n do coroutine.yield() end end
return function(game)
 local ok,err=xpcall(function()
  local version=require('src.core.GameVersion').get()
  local lang=assert(os.getenv('QA_LANGUAGE'))
  local e=assert(game.mods.exports.german_rom_source)
  assert(e.status==(lang=='en' and 'english' or 'active') and e.language==lang)
  print('LANGUAGE_LOAD '..require('src.link.Json').encode({game=version,language=lang,seconds=e.loadSeconds,cacheHit=e.coverage and e.coverage.cacheHit,translated=e.coverage and e.coverage.translated,total=e.coverage and e.coverage.total}))
  if e.coverage then print('LANGUAGE_MISSING '..require('src.link.Json').encode(e.coverage.missing)) end
  if os.getenv('QA_MODE')=='load' then love.event.quit();return end
  if love.setDeprecationOutput then love.setDeprecationOutput(false) end
  local Text=require('src.core.game3.rom_text')
  local Map=require('src.core.game3.map')
  local Message=require('src.ui.game3.message')
  local Field=require('src.core.game3.field')
  local Party=require('src.core.game3.party')
  local function capture(name)
   wait(30);require('src.ui.game3.map_name_popup').dismiss()
   game.capturePath=os.getenv('SHOT_DIR')..'/'..version..'-'..lang..'-'..name..'.png'
   for _=1,600 do if not game.capturePath then break end;wait(1) end
   assert(not game.capturePath,'Screenshot timeout')
   print('LANGUAGE_CAPTURE',version,lang,name)
  end
  game:returnToTitle({skipIntro=true});wait(420);capture('title')
  game:_handleBootAction({action='new_game',name='TEST',gender=0,start={map='FR_VIRIDIAN_CITY',x=26,y=28,facing='up'}})
  wait(90);assert(game.phase=='field');capture('center')
  assert(Map.load(nil,game,'FR_VIRIDIAN_CITY',{x=36,y=21,facing='up'}));capture('mart')
  assert(Party.giveMon(game.session,1,15,nil,{fixedPersonality=0}))
  local mon=game.session.party[1];mon.hp=1
  assert(Map.load(nil,game,'FR_VIRIDIAN_CITY_POKEMON_CENTER_1F',{x=7,y=4,facing='up'}));wait(60)
  local expected=Text.plain('Text_RestoredPkmnToFullHealth')
  print('LANGUAGE_HEALING_SOURCE',lang,expected:gsub('\n',' | '))
  local seen,healedShot={},false
  Field.interact(game)
  for i=1,1500 do
   local page=Message.currentPage() or ''
   if page~='' and not seen[page] then
    seen[page]=true;print('LANGUAGE_NURSE_PAGE',lang,page:gsub('\n',' | '))
   end
   if mon.hp>1 and page~='' and (page:find('saúde',1,true) or page:find('recuperad',1,true) or page:find('curad',1,true) or (lang=='en' and page:find('full health',1,true))) and not healedShot then
    Message.skipReveal();capture('healing');healedShot=true
   end
   game:keypressed('z');wait(1);game:keyreleased('z');wait(10)
   if mon.hp>1 and not Field.isLocked() and not Message.isOpen() then break end
  end
  assert(mon.hp>1,'Actual nurse script did not heal')
  assert(healedShot,'Actual healing dialogue was not observed in the selected language')
  assert(not Field.isLocked(),'Nurse did not release player')
  print('LANGUAGE_HEALING_OK',version,lang,mon.hp)
  assert(loadfile(os.getenv('GERMAN_MOD_ROOT')..'/tests/frlg_ptbr_field.lua'))()(game,capture,lang)
  local Summary=require('src.ui.game3.summary_menu')
  for page=1,3 do Summary.openMenu(game.session.party,1,{session=game.session,page=page});capture('summary-'..page);Summary.close() end
  if lang=='pt-BR' then
   local Font=require('src.ui.game3.frlg_font')
   local Data=require('src.core.game3.summary_data')
   local own=assert(love.filesystem.load('mods/german_rom_source/ptbr_ability_descriptions.lua'))()
   for id=0,77 do
    local desc=Data.abilityDescription(id)
    assert(desc==own[id],'Ability description mismatch '..id)
    assert(not desc:find('\n',1,true) and Font.measure(desc)<=222,'Ability line too wide '..id..': '..desc)
    for ch in Font.utf8Chars(desc) do assert(ch==' ' or Font.glyphId(ch)~=0,'Missing ability glyph '..ch) end
   end
   print('LANGUAGE_ABILITY_DESCRIPTIONS_OK',78)
   assert(loadfile(os.getenv('GERMAN_MOD_ROOT')..'/tests/ptbr_moves_live.lua'))()()
   local profile
   for _,entry in ipairs(assert(love.filesystem.load('mods/german_rom_source/catalog.lua'))()) do
    if entry.game==version and entry.language=='pt-BR' then profile=entry end
   end
   local authored=assert(love.filesystem.load('mods/german_rom_source/'..assert(profile).authored))()
   local n=0
   for key,row in pairs(authored) do
    for _,seg in ipairs(row.target) do if seg.t=='text' then
     assert(Font.measure(seg.s)<=208,'Authored line too wide: '..key..' / '..seg.s)
     for ch in Font.utf8Chars(seg.s) do assert(ch==' ' or Font.glyphId(ch)~=0,'Missing authored glyph: '..key..' / '..ch) end
    end end
    n=n+1
   end
   print('LANGUAGE_AUTHORED_WIDTH_OK',n)
  end
  if lang=='pt-BR' then assert(Text.plain('gText_PokedexPokemon')==' POKéMON','Lost category separator') end
  local Dex=require('src.ui.game3.pokedex')
  require('src.core.game3.dex').setCaught(game.session.dex,80)
  Dex.showRegistration(80,{session=game.session});wait(60);capture('dex-slowbro');Dex.close()
  assert(Map.load(nil,game,'FR_VIRIDIAN_CITY',{x=26,y=28,facing='up'}));wait(60)
  mon.moves={33};mon.pp={35};mon.maxPp={35}
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
