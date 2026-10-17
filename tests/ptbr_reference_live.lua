-- Real native reference screens. Save flags unlock records; no fixture supplies
-- displayed prose. All navigation below uses the game's ordinary key input.
return function(game)
 io.stdout:setvbuf('line')
 local function wait(n)for _=1,n do coroutine.yield()end end
 local ok,err=xpcall(function()
  local version=require('src.core.GameVersion').get();assert(version=='firered' or version=='leafgreen')
  if love.setDeprecationOutput then love.setDeprecationOutput(false)end
  game:_handleBootAction({action='new_game',name='TEST',gender=0,start={map='FR_VIRIDIAN_CITY',x=6,y=17,facing='up'}});wait(60)
  local exports=assert(game.mods.exports.german_rom_source)
  local Json=require('src.link.Json');local W=require('src.import.LuaWriter')
  local function capture(name)
   wait(5);game.capturePath=os.getenv('SHOT_DIR')..'/'..version..'-pt-BR-reference-'..name..'.png'
   for _=1,600 do if not game.capturePath then break end;wait(1)end;assert(not game.capturePath)
   print('LANGUAGE_REFERENCE_CAPTURE',version,name)
  end
  local function press(k)game:keypressed(k);wait(1);game:keyreleased(k);wait(5)end
  local f=assert(io.open(os.getenv('SHOT_DIR')..'/'..version..'-scene-audit.json','w'));f:write(Json.encode(exports.coverage.assets.sceneText));f:close()
  local Fame=require('src.ui.game3.fame_checker');local Data=require('src.core.game3.fame_checker')
  local expected=assert(loadstring(assert(exports.assets['data/generated/gba/fame_checker/pack.lua'])))()
  assert(W.encode(Fame.pack())==W.encode(expected),'Fame Checker retained stale language data')
  assert(Data.fullyUnlock(game.session));local pages={}
  for gender=0,1 do
   game.session.gender=gender
   Fame.show(game.session);wait(15)
   for person=0,15 do
    assert(Fame.selectedPerson()==person,'Fame cursor order differs')
    press('z');assert(Fame.mode=='flavor')
    for slot=0,5 do
     assert(Fame.iconCursor==slot)
     local native=assert(Fame._pages)
     for page=1,#native do
      assert(Fame.textPage==page)
      local text=assert(Fame.messageText());assert(not text:find('{ULA_',1,true),'Unresolved gender operand')
      pages[#pages+1]={person=person,slot=slot,gender=gender,text=text}
      if (person==0 and slot==0 and page==2 and gender==0) or (person==4 and slot==1 and page==2) then capture('fame-'..person..'-'..slot..'-gender-'..gender)end
      press('z')
     end
     if slot==2 then press('right');press('down') elseif slot~=5 then press('right')end
    end
    press('x');press('escape');assert(Fame.pickMode)
    local text=assert(Fame.messageText());assert(not text:find('{ULA_',1,true));pages[#pages+1]={person=person,gender=gender,quote=text}
    if person==1 then capture('daisy-quote-gender-'..gender)end
    press('x');if person<15 then press('down')end
   end
   Fame.close()
  end
  local Help=require('src.ui.game3.help_system')
  expected=assert(loadstring(assert(exports.assets['data/generated/gba/help/pack.lua'])))()
  assert(Help.show(game,1));assert(W.encode(Help.pack)==W.encode(expected),'Help retained stale language data');wait(20);capture('help-welcome');if Help.level=='welcome'then press('z')end
  local topics=#Help.rows-1;local articles=0
  for index=1,topics do
   assert(Help.level=='main' and Help.cursor==index);press('z');assert(Help.level=='submenu')
   local count=math.min(3,#Help.rows-1)
   for row=1,count do
    press('z');assert(Help.level=='article');articles=articles+1;capture('help-'..Help.topic..'-'..row)
    for _=1,Help.maxArticleScroll do press('down')end
    press('x');if row<count then press('down')end
   end
   press('x');if index<topics then press('down')end
  end
  Help.close()
  local f=assert(io.open(os.getenv('SHOT_DIR')..'/'..version..'-reference-pages.json','w'));f:write(Json.encode(pages));f:close()
  print('LANGUAGE_REFERENCE_OK',version,#pages,articles)
 end,debug.traceback)
 if not ok then print('LANGUAGE_REFERENCE_FAILED',err)end;love.event.quit(ok and 0 or 1)
end
