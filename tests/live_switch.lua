local function wait(n)for _=1,n do coroutine.yield()end end
return function(game)
 io.stdout:setvbuf('no');if love.setDeprecationOutput then love.setDeprecationOutput(false)end
 local ok,err=xpcall(function()
  local Version=require('src.core.GameVersion');local generation=Version.generation();local version=Version.get()
  local service=assert(game.mods.exports.german_rom_source.session)
  if generation==1 then
   game:startNewGame({intro=false})
   game.save.player.name='ULA';game.save.playerName='ULA'
   game.save.party={require('src.pokemon.Pokemon').new(game.data,'BULBASAUR',12)}
   assert(require('src.inventory.Bag').add(game.save,'POTION',3,game.data))
   game.overworld:setMap('VIRIDIAN_POKECENTER',3,3,'up',{via='boot'})
  elseif generation==2 then
   game:continueGame(require('src.core.gen2.Save').newGame({playerName='ULA',trainerId=12345}))
   game.save.party={require('src.battle.gen2.Mon').new(game.data,'BULBASAUR',15,{nickname='ULA'})}
   assert(require('src.inventory.Bag').add(game.save,'POTION',3,game.data))
   game.world:setMap('CHERRYGROVE_POKECENTER_1F',3,3,'up',{via='boot',continue=true})
  else
   local Schema=require('src.core.game3.save_schema_firered')
   local s=Schema.newGame({name='ULA',gender=0})
   s.map=version=='emerald' and 'EM_OLDALE_TOWN' or version=='ruby' and 'RU_OLDALE_TOWN' or version=='sapphire' and 'SA_OLDALE_TOWN' or 'FR_VIRIDIAN_CITY';s.x=6;s.y=17
   assert(require('src.core.game3.party').giveMon(s,1,15,'ULA',{fixedPersonality=0}))
   assert(require('src.core.game3.bag').add(s.bag,13,3))
   game:_enterField(s,'new_game')
  end
  wait(120)
  if generation==2 then game.world:cancelMapNameSign()end
  -- Prepare a normally loaded mod save before making unsaved changes.
  -- In Gen1 the first native checkpoint also assigns its playthrough ID.
  if generation==1 then assert(require('src.core.Checkpoint').capture(service.game))end
  require('src.mods.Runtime').emit('save.loaded',{game=service.game,save=game.session or game.save,meta=game.save.meta})
  wait(90)
  if game.save.modData and game.save.modData.kanto_ascendant then game.save.modData.kanto_ascendant.trainer_step_clock=143 end
  game.save.modData=game.save.modData or {};game.save.modData.ula_state_probe={counter=47,nested={inventory='preserve',flag=true}}
  if generation==3 then game.session.modData=game.save.modData end
  service=game.mods.exports.german_rom_source.session
  print('LIVE_SWITCH_INITIAL',version,service:canSwitch())
  local function capture(name)
   local done=false;love.graphics.captureScreenshot(function(d)
    local f=assert(io.open(os.getenv('SHOT_DIR')..'/'..version..'-'..name..'.png','wb'));f:write(d:encode('png'):getString());f:close();done=true
   end);while not done do wait(1)end
  end
  assert(loadfile(os.getenv('GERMAN_MOD_ROOT')..'/tests/live_switch_controls.lua'))()(game,capture)
  local targets={'de','pt-BR','en'}
  if version=='gold' or version=='silver'then targets={'de','ko','pt-BR','en'}elseif version=='crystal'then targets={'de','ja','pt-BR','en'}end
  if os.getenv('QA_ALL')=='1'then
   targets={};for _,r in ipairs(service:choices())do if r.id~='en' and r.available then targets[#targets+1]=r.id end end;targets[#targets+1]='en'
  end
  for _=1,tonumber(os.getenv('QA_REPEAT')or'0')do targets[#targets+1]='de';targets[#targets+1]='en'end
  for _,target in ipairs(targets)do
   local started=love.timer.getTime()
   service=game.mods.exports.german_rom_source.session
   local before=game.save
   local party=before.party and #before.party or 0
   local success,why=service:request(target);assert(success,why);assert(service.pending==target)
   local snapshot=service.snapshot
   assert(snapshot and snapshot.save)
   for i=1,900 do
    wait(1);local e=game.mods.exports.german_rom_source
    if e.session~=service and e.session.lastSwitch then break end
   end
   local e=game.mods.exports.german_rom_source
   assert(e.language==target,'wrong live language: '..tostring(e.language))
   assert(e.session~=service and e.session.lastSwitch and e.session.lastSwitch.restored,'handoff did not complete')
   assert(game.save.party and #game.save.party==party,'party changed')
   local captureEngine=assert(loadfile(os.getenv('GERMAN_MOD_ROOT')..'/mod/session_engine.lua'))()
   local settled
   for _=1,120 do if e.session:canSwitch()then settled=true;break end;wait(1)end;assert(settled,'not settled')
   local after=captureEngine.capture(e.session.game)
   local check=assert(loadfile(os.getenv('GERMAN_MOD_ROOT')..'/tests/live_switch_state.lua'))()
   print('LIVE_SWITCH_STATE_OK',target,check(snapshot.save,after.save))
   wait(60)
   collectgarbage('collect');collectgarbage('collect')
   print('LIVE_SWITCH_APPLIED',version,target,'without restarting application','seconds',love.timer.getTime()-started,'luaKiB',collectgarbage('count'),'textureBytes',love.graphics.getStats().texturememory)
   assert(e.session:canSwitch(),'not settled after switch')
   capture('live-'..target)
   if generation==3 then assert(loadfile(os.getenv('GERMAN_MOD_ROOT')..'/tests/gba_language_handoff.lua'))()(e.session.game,target)end
   if os.getenv('QA_NURSE')=='1'then
    assert(loadfile(os.getenv('GERMAN_MOD_ROOT')..'/tests/live_switch_nurse.lua'))()(e.session.game,function(name)capture(name)end,target)
   end
  end
  if os.getenv('QA_RECOVERY')=='1'then assert(loadfile(os.getenv('GERMAN_MOD_ROOT')..'/tests/live_switch_recovery.lua'))()(game)end
  print('LIVE_SWITCH_OK',version)
 end,debug.traceback)
 if not ok then print('LIVE_SWITCH_FAILED',err)end
 love.event.quit(ok and 0 or 1)
end
