function love.load()
 local ok,err=xpcall(function()
  love.filesystem.setIdentity('uni-language-ptbr-install-qa')
  local engine=assert(os.getenv('QA_ENGINE'))
  package.path=engine..'/?.lua;'..engine..'/?/init.lua;'..package.path
  local L=require('src.mods.LauncherMods')
  local Cache=require('src.import.CacheFs')
  assert(not Cache.portable,'This test must use an isolated save directory')
  local zip=assert(os.getenv('QA_ZIP'))
  assert(L.installZip(zip,{expectId='german_rom_source',replace=true}))
  local profile='mods/german_rom_source/baseroms/.uni-language-profile'
  assert(love.filesystem.createDirectory('mods/german_rom_source/baseroms'))
  assert(love.filesystem.write(profile,'ULA1\npreferences/ui-language.txt=pt-BR\n'))
  assert(L.installZip(zip,{expectId='german_rom_source',replace=true}))
  assert(love.filesystem.read(profile):find('pt-BR',1,true),'Update lost profile')
  assert(L.uninstall('german_rom_source'))
  assert(not love.filesystem.getInfo(profile),'Uninstall retained profile')
  assert(L.installZip(zip,{expectId='german_rom_source'}))
  assert(not love.filesystem.getInfo(profile),'Reinstall restored stale profile')
  print('PTBR_INSTALL_OK install update preserves profile uninstall clears profile reinstall starts fresh')
 end,debug.traceback)
 if not ok then print(err) end
 love.event.quit(ok and 0 or 1)
end
