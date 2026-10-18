-- Persist an actual unsaved session, then restore it in a separate process.
local function wait(n)for _=1,n do coroutine.yield()end end
return function(game)
 io.stdout:setvbuf('no')
 local ok,err=xpcall(function()
  local root=os.getenv('GERMAN_MOD_ROOT');local V=require('src.core.GameVersion');local generation=V.generation();local version=V.get()
  local Engine=assert(loadfile(root..'/mod/session_engine.lua'))();local codec=assert(loadfile(root..'/mod/cache_codec.lua'))()
  local Cache=require('src.import.CacheFs');local function raw(fn)local old=Cache.prefix;Cache.prefix='';local ok,a=pcall(fn);Cache.prefix=old;assert(ok,a);return a end
  local path='mods/german_rom_source/baseroms/.uni-language-recovery-'..version..'.bin'
  if os.getenv('QA_RESTART_MODE')=='write'then
   if generation==1 then
    game:startNewGame({intro=false});game.save.party={require('src.pokemon.Pokemon').new(game.data,'BULBASAUR',12)}
    game.overworld:setMap('VIRIDIAN_POKECENTER',3,3,'up',{via='boot'})
   elseif generation==2 then
    game:continueGame(require('src.core.gen2.Save').newGame({playerName='ULA',trainerId=12345}))
    game.save.party={require('src.battle.gen2.Mon').new(game.data,'BULBASAUR',15,{nickname='RESTART'})}
    game.world:setMap('CHERRYGROVE_POKECENTER_1F',3,3,'up',{via='boot',continue=true})
   else
    local s=require('src.core.game3.save_schema_firered').newGame({name='ULA',gender=0});s.map='EM_OLDALE_TOWN';s.x=6;s.y=17
    assert(require('src.core.game3.party').giveMon(s,1,15,'RESTART',{fixedPersonality=0}));game:_enterField(s,'new_game')
   end
   wait(120);if generation==2 then game.world:cancelMapNameSign()end
   game.save.modData=game.save.modData or {};game.save.modData.restart_probe={unsaved=143}
   if game.session then game.session.modData=game.save.modData end
   local snapshot=Engine.capture(game.mods.exports.german_rom_source.session.game)
   assert(raw(function()return Cache.write(path,codec.encode({format=1,version=version,language='en',snapshot=snapshot,capturedAt=os.time()}))end))
   print('INTERRUPTED_BACKUP_WRITTEN',version)
  else
   local S=game.mods.exports.german_rom_source.session
   assert(S.recoveryAvailable and S.opened,'Fresh boot did not expose recovery')
   assert(not S:canSwitch(),'Expected a fresh title session, not an active save')
   local record=codec.decode(raw(function()return assert(Cache.read(path))end))
   assert(S:recover())
   for _=1,900 do wait(1);local nextS=game.mods.exports.german_rom_source.session;if nextS~=S and nextS.lastSwitch then break end end
   local nextS=game.mods.exports.german_rom_source.session
   for _=1,120 do if nextS:canSwitch()then break end;wait(1)end
   assert(nextS~=S and nextS.lastSwitch and nextS:canSwitch(),'Recovery did not resume overworld')
   assert(game.save.modData.restart_probe.unsaved==143)
   assert(loadfile(root..'/tests/live_switch_state.lua'))()(record.snapshot.save,Engine.capture(nextS.game).save)
   assert(not raw(function()return Cache.read(path)end),'Recovery backup retained after successful restore')
   print('INTERRUPTED_FRESH_PROCESS_RECOVERY_OK',version)
  end
 end,debug.traceback)
 if not ok then print('INTERRUPTED_RESTART_FAILED',err)end
 love.event.quit(ok and 0 or 1)
end
