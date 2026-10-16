local function wait(n) for _=1,n do coroutine.yield() end end
return function(game)
 local ok,err=xpcall(function()
  local e=assert(game.mods.exports.german_rom_source)
  local ui=assert(e.startup)
  assert(ui.open,'Picker did not open before title')
  assert(e.language==os.getenv('QA_LANGUAGE'),'Wrong selected language')
  while ui.stage=='intro' do wait(1) end
  if ui.stage=='notice' then assert(ui.confirm()) end
  local function shot(name)
   wait(3)
   local captured=false
   love.graphics.captureScreenshot(function(data)
    local f=assert(io.open(name,'wb'));f:write(data:encode('png'):getString());f:close();captured=true
   end)
   while not captured do wait(1) end
  end
  ui.stage='menu';ui.previewLocale('en')
  shot(os.getenv('QA_SCREENSHOT'):gsub('.png$','-languages.png'))
  for _,id in ipairs({'en','de','fr','it','es','ja','ko','zh-Hans','zh-Hant'}) do
   assert(ui.chooseMenu(id));assert(ui.stage=='game' and ui.uiLanguage==id)
   shot(os.getenv('QA_SCREENSHOT'):gsub('.png$','-'..id..'.png'))
  end
  assert(ui.chooseMenu('de'))
  shot(os.getenv('QA_SCREENSHOT'))
  assert(ui.choose(e.language))
  assert(not ui.open,'Picker did not release the game')
  wait(30)
  print('STARTUP_LIVE_OK',require('src.core.GameVersion').get(),e.language)
 end,debug.traceback)
 if not ok then print('STARTUP_LIVE_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
