-- Actual first-launch picker/intro, then real movement and an in-game switch.
local function wait(n)for _=1,n do coroutine.yield()end end
return function(game)
 io.stdout:setvbuf('no')
 local ok,err=xpcall(function()
  local root=os.getenv('GERMAN_MOD_ROOT');local e=game.mods.exports.german_rom_source;local picker=assert(e.startup)
  assert(picker.open,'Fresh profile did not open setup')
  if picker.stage=='intro'then
   for _=1,300 do picker.skipIntro();wait(1);if picker.stage~='intro'then break end end
  end
  if picker.stage=='notice'then picker.confirm()end
  assert(picker.chooseMenu('pt-BR'));assert(picker.choose('en'));assert(not picker.open)
  game:startNewGame({intro=false});game.save.party={require('src.pokemon.Pokemon').new(game.data,'BULBASAUR',12)}
  game.overworld:setMap('VIRIDIAN_POKECENTER',3,3,'down',{via='boot'});wait(30)
  local y=game.overworld.player.cellY
  game:keypressed('down');wait(20);game:keyreleased('down');wait(40)
  assert(game.overworld.player.cellY>y,'Closing setup left normal gameplay paused')
  local S=e.session;local x,y=game.overworld.player.cellX,game.overworld.player.cellY
  game:keypressed('right');assert(S:open(S.game));game:keyreleased('right');S:back();wait(30)
  assert(game.overworld.player.cellX==x and game.overworld.player.cellY==y,'Menu back left a direction held')
  assert(S:open(S.game));assert(S:text('title')=='Idiomas'and S.uiLanguage=='pt-BR','First setup locale did not reach in-game menu')
  assert(S:menuLanguage('de'));S.opened=false
  assert(S:request('pt-BR'))
  for _=1,900 do wait(1);local nextE=game.mods.exports.german_rom_source;if nextE.session~=S and nextE.session.lastSwitch then break end end
  local nextE=game.mods.exports.german_rom_source;assert(nextE.language=='pt-BR'and nextE.session~=S)
  for _=1,120 do if nextE.session:canSwitch()then break end;wait(1)end
  assert(nextE.session:canSwitch())
  local path=love.filesystem.getSaveDirectory()..'/mods/german_rom_source/baseroms/.uni-language-profile'
  local f=assert(io.open(path,'rb'));local profile=f:read('*a');f:close()
  for _,value in ipairs({'preferences/notice.txt=accepted','preferences/ascendant-intro-v1.txt=seen','preferences/ui-language.txt=de','preferences/red.txt=pt-BR'})do assert(profile:find(value,1,true),'First setup preference lost: '..value)end
  assert(not nextE.startup.open and not nextE.startup.intro,'Intro/setup repeated during handoff')
  assert(loadfile(root..'/tests/live_switch_nurse.lua'))()(nextE.session.game,function()end,'pt-BR')
  print('INITIAL_LANGUAGE_PROFILE_OK actual intro/picker, resumed movement, live locale, preserved intro/profile, real nurse')
 end,debug.traceback)
 if not ok then print('INITIAL_LANGUAGE_PROFILE_FAILED',err)end
 love.event.quit(ok and 0 or 1)
end
