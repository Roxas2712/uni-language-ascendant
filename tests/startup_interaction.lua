local function wait(n) for _=1,n do coroutine.yield() end end
return function(game)
 local ok,err=xpcall(function()
  local ui=assert(game.mods.exports.german_rom_source.startup)
  local wrappedUpdate=game.update
  assert(ui.open)
  game:keypressed('l');assert(ui.stage=='menu')
  local index=ui.uiIndex
  game:keypressed('right');assert(ui.uiIndex==index%9+1)
  game:keypressed('return');assert(ui.stage=='game')
  -- Exercise the actual scaled mouse hit areas in a small window.
  love.window.setMode(640,480,{resizable=true})
  wait(4)
  local w,h=love.graphics.getDimensions();local scale=math.min(w/960,h/650)
  game:mousepressed((737*scale)+(w-960*scale)/2,(40*scale)+(h-650*scale)/2,1)
  assert(ui.stage=='menu','scaled language button missed')
  game:gamepadpressed(nil,'dpdown');game:gamepadpressed(nil,'a')
  assert(ui.stage=='game')
  ui.chooseMenu('de');wait(4)
  local captured=false
  love.graphics.captureScreenshot(function(data)
   local f=assert(io.open(os.getenv('QA_SCREENSHOT'),'wb'));f:write(data:encode('png'):getString());f:close();captured=true
  end)
  while not captured do wait(1) end
  game:keypressed('return')
  assert(not ui.open and game.update~=wrappedUpdate,'game wrappers remained installed')
  wait(30)
  print('STARTUP_INTERACTION_OK keyboard, gamepad, scaled mouse, 640x480, restore')
 end,debug.traceback)
 if not ok then print('STARTUP_INTERACTION_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
