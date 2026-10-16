local function wait(n)for _=1,n do coroutine.yield()end end
return function(game)
 if love.setDeprecationOutput then love.setDeprecationOutput(false) end
 local ok,err=xpcall(function()
  local lang=os.getenv('QA_LANGUAGE');local e=assert(game.mods.exports.german_rom_source);local ui=assert(e.startup)
  assert(ui.open and #ui.choices==5)
  local function shot(name)
   wait(4);local done=false
   love.graphics.captureScreenshot(function(data)
    local f=assert(io.open(os.getenv('SHOT_DIR')..'/'..lang..'-'..name..'.png','wb'))
    f:write(data:encode('png'):getString());f:close();done=true
   end)
   for _=1,300 do if done then break end;wait(1) end
   assert(done,'screenshot failed')
  end
  local function click(x,y)
   local w,h=love.graphics.getDimensions();local s=math.min(w/960,h/650)
   game:mousepressed(x*s+(w-960*s)/2,y*s+(h-650*s)/2,1)
  end
  ui.index=1
  -- Updates can run several times before the first draw while loading. The
  -- mouse hitboxes only exist after the picker has actually been rendered.
  for _=1,300 do
   local ready=false
   for _,box in ipairs(ui.hitboxes or {}) do if box.x==872 and box.y==153 then ready=true end end
   if ready then break end
   wait(1)
  end
  click(891,166);assert(ui.index==4,'Mouse cannot reach second language page (stage '..ui.stage..', index '..ui.index..')')
  shot('picker-page2');click(841,166);assert(ui.index==1,'Previous language page failed')
  shot('picker-page1');assert(ui.choose(lang));assert(not ui.open)
  game:_handleBootAction({action='new_game',name='TEST',gender=0,start={map='EM_OLDALE_TOWN',x=14,y=7,facing='up'}})
  wait(60);require('src.ui.game3.map_name_popup').dismiss()
  require('src.ui.game3.hud').openMessage(game,require('src.core.game3.rom_text').plain('gText_WouldYouLikeToRestYourPkmn'))
  wait(10);require('src.ui.game3.message').advance();shot('dialogue')
  print('RELEASE_UI_OK',lang,'five languages, scaled mouse pages, reveal dialogue')
 end,debug.traceback)
 if not ok then print('RELEASE_UI_FAILED',err)end
 love.event.quit(ok and 0 or 1)
end
