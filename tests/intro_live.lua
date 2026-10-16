local function wait(n)for _=1,n do coroutine.yield()end end
return function(game)
 local ok,err=xpcall(function()
  local ui=assert(game.mods.exports.german_rom_source.startup)
  local mode=os.getenv('QA_INTRO_MODE');local picker=os.getenv('QA_PICKER')=='true'
  local function shot(label)
   local done=false
   love.graphics.captureScreenshot(function(data)
    local f=assert(io.open(os.getenv('QA_SCREENSHOT')..'-'..label..'.png','wb'));f:write(data:encode('png'):getString());f:close();done=true
   end)
   while not done do wait(1)end
  end
  if mode=='repeat' then
   assert(ui.stage~='intro' and not ui.intro,'Intro replayed on a later launch/edition')
   assert(ui.open==picker)
  else
   assert(ui.stage=='intro' and ui.intro and ui.open,'First run did not show intro')
   local intro=ui.intro
   local wrapped=game.update
   assert(not ui.chooseMenu('de') and not ui.choose('en'),'Input bypassed intro')
   if mode=='abort' then
    wait(20);game.mods.events:removeOwner('german_rom_source');wait(2)
    assert(not ui.open and not ui.intro and intro.closed and game.update~=wrapped,'Unload did not release intro')
    print('INTRO_LIVE_OK',mode,require('src.core.GameVersion').get());love.event.quit(0);return
   elseif mode=='skip' then
    while intro.elapsed<.3 do wait(1)end
    game:keypressed('return')
   else
    for _,t in ipairs({3,7,9})do
     while ui.intro and intro.elapsed<t do wait(1)end
     assert(ui.intro,'Intro finished too soon');shot(t)
    end
    while ui.intro do wait(1)end
   end
   assert(intro.closed and not ui.intro,'Intro resources retained')
   assert(ui.open==picker,'Hidden picker or intro handoff incorrect')
   if not picker then assert(game.update~=wrapped,'Intro frame wrappers remained')end
  end
  if picker then
   if ui.stage=='notice' then assert(ui.confirm()) end
   assert(ui.chooseMenu('de'));assert(ui.choose('en'));assert(not ui.open)
  end
  wait(20)
  print('INTRO_LIVE_OK',mode,require('src.core.GameVersion').get())
 end,debug.traceback)
 if not ok then print('INTRO_LIVE_FAILED',err)end
 love.event.quit(ok and 0 or 1)
end
