function love.load()
 local ok,err=xpcall(function()
  love.filesystem.setIdentity(os.getenv('QA_INSTALL_IDENTITY') or 'uni-language-ptbr-install-qa')
  local engine=assert(os.getenv('QA_ENGINE'))
  package.path=engine..'/?.lua;'..engine..'/?/init.lua;'..package.path
  local L=require('src.mods.LauncherMods')
  local Cache=require('src.import.CacheFs')
  assert(not Cache.portable,'This test must use an isolated save directory')
  local zip=assert(os.getenv('QA_ZIP'))
  assert(L.installZip(os.getenv('QA_PREVIOUS_ZIP') or zip,{expectId='german_rom_source',replace=true}))
  local profile='mods/german_rom_source/baseroms/.uni-language-profile'
  assert(love.filesystem.createDirectory('mods/german_rom_source/baseroms'))
  local saved='ULA1\npreferences/ui-language.txt=pt-BR\npreferences/emerald.txt=de\npreferences/ascendant-intro-v1.txt=seen\n'
  assert(love.filesystem.write(profile,saved))
  local recovery='mods/german_rom_source/baseroms/.uni-language-recovery-red.bin'
  assert(love.filesystem.write(recovery,'QA recovery sentinel, not a save'))
  local imported='mods/german_rom_source/baseroms/qa-import.bin'
  assert(love.filesystem.write(imported,'QA import sentinel, not a ROM'))
  assert(love.filesystem.write('qa-save-sentinel.bin','QA save sentinel'))
  assert(L.installZip(zip,{expectId='german_rom_source',replace=true}))
  assert(love.filesystem.read(recovery)=='QA recovery sentinel, not a save','Update lost interrupted-switch backup')
  for _,name in ipairs({'session.lua','session_engine.lua','session_menu.lua','session_locales.lua'})do assert(love.filesystem.getInfo('mods/german_rom_source/'..name),'Update omitted '..name)end
  assert(love.filesystem.read(profile)==saved,'Update changed preferences or intro status')
  assert(love.filesystem.read(imported)=='QA import sentinel, not a ROM','Update lost imported file')
  assert(love.filesystem.getInfo('mods/german_rom_source/cache_codec.lua'),'Update omitted binary codec')
  assert(L.uninstall('german_rom_source'))
  assert(not love.filesystem.getInfo(profile),'Uninstall retained profile')
  assert(not love.filesystem.getInfo(recovery),'Uninstall retained recovery')
  assert(L.installZip(zip,{expectId='german_rom_source'}))
  assert(not love.filesystem.getInfo(profile),'Reinstall restored stale profile')
  assert(not love.filesystem.getInfo(imported),'Reinstall restored stale import')
  assert(love.filesystem.read('qa-save-sentinel.bin')=='QA save sentinel','Mod lifecycle touched game save area')
  love.filesystem.remove('qa-save-sentinel.bin')
  print('PTBR_INSTALL_OK install update preserves profile uninstall clears profile reinstall starts fresh')
 end,debug.traceback)
 if not ok then print(err) end
 love.event.quit(ok and 0 or 1)
end
