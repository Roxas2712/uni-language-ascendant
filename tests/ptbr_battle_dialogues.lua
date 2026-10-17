-- A real resolved Ingrain turn followed by a damaging turn and field return.
-- Test setup selects a legal Sunkern move; no text is injected into the UI.
local function wait(n) for _=1,n do coroutine.yield() end end
return function(game)
 local ok,err=xpcall(function()
  if love.setDeprecationOutput then love.setDeprecationOutput(false) end
  local lang=assert(os.getenv('QA_LANGUAGE'))
  local version=require('src.core.GameVersion').get()
  local prefix=assert(({emerald='EM_',ruby='RU_',sapphire='SA_'})[version])
  local e=assert(game.mods.exports.german_rom_source)
  assert(e.language==lang and e.status==(lang=='en' and 'english' or 'active'))
  game:_handleBootAction({action='new_game',name='TEST',gender=0,start={map=prefix..'OLDALE_TOWN',x=6,y=17,facing='up'}})
  wait(60)
  if lang=='pt-BR' then assert(loadfile(os.getenv('GERMAN_MOD_ROOT')..'/tests/ptbr_moves_live.lua'))()() end
  local Party=require('src.core.game3.party')
  local Pokemon=require('src.core.game3.pokemon')
  local id=assert(Pokemon.speciesFromName('SUNKERN'))
  assert(Party.giveMon(game.session,id,35,nil,{fixedPersonality=0}))
  local mon=game.session.party[1]
  mon.moves={275,71,74,72};mon.pp={20,25,40,15};mon.maxPp={20,25,40,15}
  local Battle=require('src.core.game3.battle')
  local Runtime=require('src.core.game3.runtime')
  local Message=require('src.ui.game3.message')
  local Ui=require('src.core.game3.battle.ui')
  local outcome,pages,seen,shot,rooted,menuShot=nil,{}, {},false,false,false
  require('src.core.game3.rng').SeedRng(12345)
  assert(require('src.core.game3.battle_bridge').startWild(Runtime._mod,game,{species=19,level=2},
   {autoFight=false,done=function(result)outcome=result end}))
  for _=1,2400 do
   local page=Message.currentPage()
   if page and page~='' and not seen[page] then pages[#pages+1]=page;seen[page]=true end
   local expected=lang=='pt-BR' and 'plantou suas raízes' or 'planted its roots'
   if page and page:gsub('\n',' '):find(expected,1,true) and not shot then
    local state=assert(Battle.getState())
    assert(state.player.rooted and state.player.expIngrain,'Text without Ingrain effect')
    rooted=true
    Message.skipReveal()
    game.capturePath=os.getenv('SHOT_DIR')..'/'..version..'-'..lang..'-ingrain.png'
    for _=1,600 do if not game.capturePath then break end;wait(1) end
    assert(not game.capturePath,'Screenshot timeout')
    shot=true
   end
   if outcome then break end
   local state=Battle.getState()
   assert(shot or not state or (state.turn or 0)<4,
    'Expected translation missing after Ingrain turns: '..table.concat(pages,' | '))
   if Ui._mode=='moves' and not menuShot then
    game.capturePath=os.getenv('SHOT_DIR')..'/'..version..'-'..lang..'-move-menu.png'
    for _=1,600 do if not game.capturePath then break end;wait(1) end
    assert(not game.capturePath,'Move menu screenshot timeout');menuShot=true
   end
   -- Choose Absorb through the actual menu after the first Ingrain turn.
   local key=shot and Ui._mode=='moves' and Ui._moveIndex==1 and 'right' or 'z'
   game:keypressed(key);wait(1);game:keyreleased(key);wait(4)
  end
  assert(shot and rooted,'Actual Ingrain message/effect not observed: '..table.concat(pages,' | '))
  assert(outcome=='win','Battle did not finish: '..tostring(outcome))
  assert(menuShot,'Actual move selection menu not observed')
  assert(mon.pp[1]==19 and mon.pp[2]<25,'The selected moves did not consume PP')
  wait(60);assert(game.phase=='field' and not Battle.isActive())
  print('LANGUAGE_BATTLE_DIALOGUE_EVIDENCE '..require('src.link.Json').encode({game=version,language=lang,
   case='ingrain',fixture='Level 35 Sunkern uses Ingrain, then Absorb against level 2 Rattata',
   trigger='battle_bridge.startWild / keyboard Fight and move selection',pages=pages,
   move_menu=true,rooted=rooted,outcome=outcome,field_return=true}))
  print('LANGUAGE_BATTLE_DIALOGUES_OK',version,lang)
 end,debug.traceback)
 if not ok then print('LANGUAGE_LIVE_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
