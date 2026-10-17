-- Targeted gameplay integration in the isolated QA identity. Fixtures establish
-- progress; nurse interactions and battle choices use the real input handlers.
local function wait(n)for _=1,n do coroutine.yield()end end
return function(game)
 io.stdout:setvbuf("no")
 local ok,err=xpcall(function()
  local V=require('src.core.GameVersion');local v,gen=V.get(),V.generation()
  local lang=assert(os.getenv('LANGUAGE_SHOT'));local exp=assert(game.mods.exports.german_rom_source)
  assert(exp.status=='active' and exp.language==lang)
  local Save=require(gen==1 and 'src.core.SaveData' or 'src.core.gen2.Save')
  if gen==1 then game:startNewGame({intro=false})
  else game:continueGame(Save.newGame({playerName='TEST',trainerId=12345}))end
  game.speedOverride=tonumber(os.getenv('QA_SPEED')) or 1
  local world=gen==1 and game.overworld or game.world
  local Mon=require(gen==1 and 'src.pokemon.Pokemon' or 'src.battle.gen2.Mon')
  local Font=require('src.render.Font')
  local function press(key,n)
   game:keypressed(key);wait(1);game:keyreleased(key);wait(n or 8)
  end
  local function capture(name)
   game.capturePath=os.getenv('SHOT_DIR')..'/'..v..'-play-'..name..'-'..lang..'.png'
   for _=1,300 do if not game.capturePath then return end;wait(1)end
   error('Screenshot timeout '..name)
  end
  -- Numeric trade data must remain identical, except the two proper names.
  local base=assert(loadfile(love.filesystem.getSaveDirectory()..'/'..v..'/data/generated/'..(gen==1 and 'field.lua' or 'events.lua')))().trades
  local trades=gen==1 and game.data.field.trades or game.data.gen2EventTables.trades
  local function same(a,b)
   if type(a)~='table'then return a==b end
   if type(b)~='table'then return false end
   for k,x in pairs(a)do if not same(x,b[k])then return false end end
   for k in pairs(b)do if a[k]==nil then return false end end
   return true
  end
  for i,row in ipairs(base)do
   for k,x in pairs(row)do if k~='nickname' and k~='otName'then assert(same(x,trades[i][k]),'Trade mechanics changed '..i..'/'..k)end end
  end
  assert(exp.identityCoverage.trades.matched==#base and exp.identityCoverage.trades.unexpected==0,'Incomplete native trade identities')
  -- A name colliding with an English UI key is still a saved user name.
  game.save.party={Mon.new(game.data,'BULBASAUR',15)}
  local mon=game.save.party[1];local maxHp=mon.maxHp or mon.stats.hp;mon.nickname='RUN'
  local original=assert(Font.__ulaEuropeanStrings).original
  assert(same(Font.encode('RUN'),original('RUN')),'Nickname was translated')
  game.save.player.name='ITEM'
  assert(same(Font.encode('ITEM'),original('ITEM')),'Player name was translated')
  if gen==2 then
   game.save.boxNames[1]='BOX 7'
   assert(same(Font.encode('BOX 7'),original('BOX 7')),'Custom box name was translated')
  end
  assert(exp.localizeUi('RUN')~='RUN','UI label not localized')
  game.save.player.name='TEST';mon.nickname='TESTMON'
  -- The real special handlers must persist localized nicknames and OT names.
  if gen==2 then
   local S=require('src.script.gen2.Specials')
   local vm={specials={party=function()return game.save.party end,save=function()return game.save end,data=function()return game.data end}}
   S.ALL.GiveShuckle(vm)
   local gift=game.save.party[#game.save.party]
   local native=({es={'SHUCKI','MANÍA'},fr={'NESSY','MANIA'},it={'SHUCKI','MATTIA'}})[lang]
   assert(gift.species=='SHUCKLE' and gift.nickname==native[1] and gift.ot==native[2],'Gift identity not persisted')
   assert(gift.level==15 and gift.otId==518 and gift.item=='BERRY','Gift mechanics changed')
   vm.specials.selectPartyMon=function(_,done)done(#game.save.party,gift)end
   gift.ot='INVENTED';S.ALL.ReturnShuckie(vm);assert(vm.scriptVar==S.SHUCKIE_WRONG_MON,'Foreign OT accepted')
   gift.ot=native[2];gift.happiness=0;S.ALL.ReturnShuckie(vm)
   assert(vm.scriptVar==S.SHUCKIE_RETURNED and #game.save.party==1,'Official gift cannot be returned')
   S.ALL.GiveShuckle(vm)
   if v=='crystal'then
    S.ALL.GiveOddEgg(vm);local egg=game.save.party[#game.save.party]
    assert(egg.isEgg and egg.nickname==(lang=='es' and 'HUEVO' or 'UOVO'),'Odd Egg nickname')
    assert(egg.ot==(lang=='es' and 'Raro' or 'Strano'),'Odd Egg OT')
   end
  end
  -- Heal a poisoned, injured party through the normal nurse script.
  mon.hp=1;mon.status='PSN'
  local map=gen==1 and 'VIRIDIAN_POKECENTER' or 'CHERRYGROVE_POKECENTER_1F'
  world:setMap(map,3,3,'up',{via='boot',continue=true});wait(60)
  world:interact();wait(15);capture('nurse')
  for _=1,150 do
   if mon.hp==maxHp and not mon.status then break end
   press('z',8)
  end
  assert(mon.hp==maxHp and not mon.status,'Nurse did not heal/cure')
  for _=1,35 do press('z',3)end
  print('EU_NURSE_OK',v,lang)
  -- Native naming values survive the normal save writer/validator.
  assert(game:writeSave(),'Save writer rejected fixture')
  local loaded=assert(Save.load(v),'Cannot load saved game')
  assert(loaded.party[1].nickname=='TESTMON' and loaded.player.name=='TEST','Names changed across save/load')
  if gen==2 then
   assert(loaded.party[2].ot==game.save.party[2].ot and loaded.party[2].nickname==game.save.party[2].nickname,'Gift identity lost on disk')
   assert(loaded.boxNames[1]=='BOX 7','Custom box name lost')
   if v=='crystal'then
    assert(loaded.party[3].isEgg and loaded.party[3].nickname==game.save.party[3].nickname and loaded.party[3].ot==game.save.party[3].ot,'Odd Egg identity lost on disk')
   end
  end
  print('EU_SAVE_IDENTITIES_OK',v,lang)
  -- A wild battle with actual FIGHT/move choices, through its win callback.
  game.save.party={mon};mon.hp=maxHp;mon.status=nil;mon.moves={{id='TACKLE',pp=35}}
  local outcome,battle
  if gen==1 then
   battle=require('src.battle.BattleState').newWild(game,'RATTATA',2)
   battle.onFinish=function(result)outcome=result end
   world:pushBattle(battle)
  else
   world:startBattle({wild=Mon.new(game.data,'RATTATA',2)},function(result)outcome=result end)
  end
  local sawMenu,sawMoves=false,false
  for _=1,750 do
   local top=game.stack:top()
   if top and top.isBattle then
    if top.phase=='menu' and not sawMenu then capture('battle-menu');sawMenu=true end
    if (top.phase=='moves' or top.phase=='moveSelect') and not sawMoves then capture('battle-moves');sawMoves=true end
   end
   if outcome then break end
   press('z',3)
  end
  if not outcome then
   local top=game.stack:top();capture('battle-timeout')
   print('EU_BATTLE_TIMEOUT',tostring(sawMenu),tostring(sawMoves),top and top.phase,top and top.message,top and top.isBattle,mon.hp)
  end
  assert(sawMenu and sawMoves and outcome=='win','Wild battle failed: '..tostring(outcome))
  print('EU_BATTLE_INPUT_OK',v,lang,outcome)
  -- Diploma/credits use the actual native art and final text rendering.
  local prefix=gen==1 and 'src.ui.' or 'src.ui.gen2.'
  game.stack:clear();local diploma;local diplomaClosed=false
  if gen==1 then diploma=require(prefix..'Diploma').new(game,function()diplomaClosed=true end)
  else diploma=require(prefix..'Diploma').new(game,{playerName='TEST',onClose=function()diplomaClosed=true;game.stack:pop()end})end
  game.stack:push(diploma);wait(2);capture('diploma');press('z',3)
  assert(diplomaClosed and game.stack:top()~=diploma,'Diploma exit failed')
  game.stack:clear();local done=false
  local credits
  if gen==1 then credits=require(prefix..'Credits').new(game,function()done=true end,function()done=true end)
  else credits=require(prefix..'Credits').new(game,{onDone=function()done=true;game.stack:pop()end})end
  game.stack:push(credits)
  if gen==2 then assert(credits:runToEnd(),'Credits never finished')
  else for _=1,100000 do if credits.phase=='end_wait'then break end;credits:update(1/60)end;assert(credits.phase=='end_wait','Credits never finished')end
  capture('credits');press('z',3)
  assert(done and game.stack:top()~=credits,'Credits exit failed')
  if gen==2 then assert(credits.done,'Credits finish failed')end
  print('EUROPEAN_GAMEPLAY_LIVE_OK',v,lang)
 end,debug.traceback)
 if not ok then print('EUROPEAN_GAMEPLAY_LIVE_FAILED',err)end
 love.event.quit(ok and 0 or 1)
end
