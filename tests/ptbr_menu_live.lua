local function wait(n) for _=1,n do coroutine.yield() end end
return function(game)
 local ok,err=xpcall(function()
  local ui=assert(game.mods.exports.german_rom_source.startup)
  local root=assert(os.getenv('GERMAN_MOD_ROOT'))
  local locales=dofile(root..'/mod/locales.lua')
  local family={ja='jp',ko='kr',['zh-Hans']='sc',['zh-Hant']='tc'}
  for language,strings in pairs(locales) do
   local font=love.graphics.newFont('mods/german_rom_source/fonts/ascendant-'..(family[language] or 'jp')..'.otf',20)
   for key,s in pairs(strings) do assert(font:hasGlyphs(s),'Missing menu glyph: '..language..'/'..key) end
  end
  ui.stage='menu';ui.uiIndex=1;ui.previewLocale('en')
  local function rendered(x,y)
   for _=1,300 do
    for _,box in ipairs(ui.hitboxes or {}) do if box.x==x and box.y==y then return end end
    wait(1)
   end
   error('Picker did not render expected control')
  end
  local function click(x,y)
   local w,h=love.graphics.getDimensions();local scale=math.min(w/960,h/650)
   game:mousepressed(x*scale+(w-960*scale)/2,y*scale+(h-650*scale)/2,1)
  end
  local function shot(name)
   wait(5);local done=false
   love.graphics.captureScreenshot(function(data)
    local f=assert(io.open(os.getenv('SHOT_DIR')..'/'..name..'.png','wb'))
    f:write(data:encode('png'):getString());f:close();done=true
   end)
   for _=1,300 do if done then return end;wait(1) end
   error('Screenshot timed out')
  end
  rendered(872,153);click(891,166)
  assert(ui.uiIndex==10 and ui.uiLanguage=='pt-BR','Portuguese page unreachable by mouse')
  shot('ptbr-menu')
  assert(ui.confirm() and ui.stage=='game' and ui.uiLanguage=='pt-BR')
  for i,choice in ipairs(ui.choices) do if choice.id=='pt-BR' then ui.index=i;assert(choice.noticeKey=='fanTranslation') end end
  assert(ui.choices[ui.index].id=='pt-BR','PT-BR import missing from picker')
  shot('ptbr-game-language')
  assert(ui.back() and ui.stage=='menu');game:keypressed('tab')
  assert(ui.uiIndex==1);game:keypressed('pageup');assert(ui.uiIndex==10)
  assert(ui.chooseMenu('de'))
  local before=assert(love.filesystem.read('mods/german_rom_source/baseroms/.uni-language-profile'))
  local found=false
  for i,choice in ipairs(ui.choices) do
   if not choice.available then
    found=true;ui.index=i;wait(5)
    assert(not ui.choose(choice.id),'disabled language started')
    game:keypressed('return');game:gamepadpressed(nil,'a')
    assert(ui.open and not ui.restarting,'disabled confirmation changed the running game')
    for _,box in ipairs(ui.hitboxes) do assert(not (box.x==654 and box.y==540),'disabled Start button is clickable') end
    click(700,560)
    assert(ui.open and not ui.restarting,'disabled mouse click started game')
    assert(ui.noticeKey==(choice.supported and 'missing' or 'unavailable'))
   end
  end
  assert(found,'QA needs at least one disabled language')
  assert(before==love.filesystem.read('mods/german_rom_source/baseroms/.uni-language-profile'),'disabled choice changed preferences')
  ui.index=4;ui.noticeKey=nil;shot('ptbr-disabled-game-languages')
  ui.index=7;ui.noticeKey=nil;shot('ptbr-disabled-asian-languages')
  assert(ui.chooseMenu('pt-BR'));assert(ui.requestReset());shot('ptbr-reset')
  assert(ui.back() and ui.stage=='game')
  assert(ui.choose('en') and not ui.open)
  print('PTBR_MENU_OK all locale keys/glyphs, mouse/keyboard paging, persistence, Back, reset cancellation, start')
 end,debug.traceback)
 if not ok then print('PTBR_MENU_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
