local function wait(n)for _=1,n do coroutine.yield()end end
return function(game)
 local Shell=require('src.core.HostShell');local original=Shell.restart;local restarts=0;Shell.restart=function()restarts=restarts+1 end
 local ok,err=xpcall(function()
  local e=assert(game.mods.exports.german_rom_source);local ui=assert(e.startup)
  assert(e.language=='en','Fresh profile inherited removed installation options')
  assert(ui.stage=='intro','Fresh profile must replay intro')
  while ui.intro and ui.intro.elapsed<.3 do wait(1)end
  game:keypressed('return');assert(ui.stage=='notice')
  local function shot(label)
   wait(3);local done=false
   love.graphics.captureScreenshot(function(data)
    local f=assert(io.open(os.getenv('QA_SCREENSHOT')..'-'..label..'.png','wb'));f:write(data:encode('png'):getString());f:close();done=true
   end)
   while not done do wait(1)end
  end
  game:keypressed('l');assert(ui.stage=='notice','English notice bypassed')
  assert(not ui.choose('en') and not ui.chooseMenu('de'))
  shot('notice')
  game:keypressed('return');assert(ui.stage=='menu')
  game:keypressed('right');game:keypressed('return');assert(ui.stage=='game' and ui.uiLanguage=='de')
  game:keypressed('l');ui.previewLocale('ja');game:keypressed('escape');assert(ui.stage=='game' and ui.uiLanguage=='de','Back did not discard preview')
  shot('game')
  local Cache=require('src.import.CacheFs');local path='mods/german_rom_source/baseroms/.uni-language-profile'
  local saved=assert(Cache.readAt(path))
  game:keypressed('r');assert(ui.stage=='reset' and ui.resetIndex==1)
  for _,id in ipairs({'en','de','fr','it','es','ja','ko','zh-Hans','zh-Hant'})do ui.previewLocale(id);shot('reset-'..id)end
  ui.previewLocale('de');game:gamepadpressed(nil,'b');assert(ui.stage=='game' and Cache.readAt(path)==saved and restarts==0)
  game:keypressed('r');game:gamepadpressed(nil,'dpright');game:gamepadpressed(nil,'a')
  assert(restarts==1 and Cache.readAt(path)=='ULA1\n','Reset did not clear all mod profile fields')
  local opts=require('src.core.SaveData').loadOptions()
  assert(opts.modOptions.german_rom_source.language=='auto' and opts.modOptions.german_rom_source.showPicker==true)
  print('PROFILE_LIVE_OK English notice, first setup, back/discard, cancel, reset/restart, nine locales')
 end,debug.traceback)
 Shell.restart=original
 if not ok then print('PROFILE_LIVE_FAILED',err)end
 love.event.quit(ok and 0 or 1)
end
