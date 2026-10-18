-- Destructive fault injection only inside the isolated QA mod profile.
return function(game)
 local root=os.getenv('GERMAN_MOD_ROOT');local Engine=assert(loadfile(root..'/mod/session_engine.lua'))()
 local function wait(n)for _=1,n do coroutine.yield()end end
 local function service()return game.mods.exports.german_rom_source.session end
 local Cache=require('src.import.CacheFs');local version=require('src.core.GameVersion').get()
 local function raw(fn)local old=Cache.prefix;Cache.prefix='';local ok,a,b=pcall(fn);Cache.prefix=old;assert(ok,a);return a,b end
 local manifest=game.mods.mods.german_rom_source.manifest;local row
 for _,r in ipairs(manifest.optional_imports)do if r.id==version..'_de'then row=r end end;assert(row)
 local source='mods/german_rom_source/baseroms/'..row.file
 local bytes=raw(function()return assert(Cache.read(source))end)
 local s=service();assert(s:request('de'));local before=s.snapshot
 raw(function()Cache.remove(source);assert(not Cache.read(source))end)
 for _=1,900 do wait(1);if service()~=s and service().error then break end end
 local restored=service();assert(restored~=s and restored.error and game.mods.exports.german_rom_source.language=='en','rollback failed')
 restored.opened=false;wait(30);assert(restored:importBytes(bytes))
 assert(loadfile(root..'/tests/live_switch_state.lua'))()(before.save,Engine.capture(restored.game).save)
 print('LIVE_ROLLBACK_OK',version,'source removed after snapshot; unsaved progress retained')
 local path='mods/german_rom_source/baseroms/.uni-language-recovery-'..version..'.bin'
 local codec=assert(loadfile(root..'/mod/cache_codec.lua'))()
 local snapshot=Engine.capture(restored.game);local began=os.time()-100;snapshot.sessionStartedAt=began
 local backup=codec.encode({format=1,version=version,language='en',snapshot=snapshot,capturedAt=os.time()-60})
 raw(function()assert(Cache.write(path,backup))end);restored.recoveryAvailable=true;assert(restored:recover())
 assert(math.abs(restored.snapshot.sessionStartedAt-began-60)<3,'Offline time added to played time')
 for _=1,900 do wait(1);if service()~=restored and service().lastSwitch then break end end
 assert(service()~=restored and service().lastSwitch and not service().recoveryAvailable)
 raw(function()assert(not Cache.read(path))end)
 local current=service();raw(function()assert(Cache.write(path,'invalid recovery'))end);current.recoveryAvailable=true
 assert(not current:recover(),'corrupt backup accepted');raw(function()assert(Cache.read(path))end)
 assert(current:discardRecovery());assert(not current.recoveryAvailable);raw(function()assert(not Cache.read(path))end)
 print('LIVE_RECOVERY_OK',version,'valid backup restored; invalid backup retained then explicitly discarded')
end
