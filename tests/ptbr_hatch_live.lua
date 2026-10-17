-- A saved egg fixture enters the game's normal hatch scene. No display text
-- is supplied by this test; hatching, naming prompts and return are native.
return function(game)
 io.stdout:setvbuf('line')
 local function wait(n)for _=1,n do coroutine.yield()end end
 local ok,err=xpcall(function()
  if love.setDeprecationOutput then love.setDeprecationOutput(false)end
  local version=require('src.core.GameVersion').get()
  local rs=version=='ruby' or version=='sapphire'
  local prefix=({ruby='RU_',sapphire='SA_',emerald='EM_',firered='FR_',leafgreen='FR_'})[version]
  game:_handleBootAction({action='new_game',name='TEST',gender=0,start={map=prefix..((version=='firered' or version=='leafgreen') and 'VIRIDIAN_CITY' or 'OLDALE_TOWN'),x=6,y=17,facing='up'}});wait(60)
  assert(require('src.core.game3.party').giveMon(game.session,1,5,nil,{fixedPersonality=0}))
  local mon=game.session.party[1];mon.isEgg=true;mon.eggCycles=0
  local Hatch=require(rs and 'src.ui.game3.rs.egg_hatch' or 'src.ui.game3.egg_hatch')
  local Message=require('src.ui.game3.message');local Choice=require('src.ui.game3.choice')
  local function press(k)game:keypressed(k);wait(1);game:keyreleased(k);wait(3)end
  local function capture(name)
   game.capturePath=os.getenv('SHOT_DIR')..'/'..version..'-pt-BR-hatch-'..name..'.png'
   for _=1,600 do if not game.capturePath then break end;wait(1)end;assert(not game.capturePath)
  end
  local done=false;assert(Hatch.start(mon,{session=game.session,slot=0,onDone=function()done=true end}))
  local pages,seen,shots={},{},{}
  for _=1,3000 do
   local scene=rs and Hatch.active()
   local text=rs and scene and scene.printer and table.concat(scene.printer.lines,'\n') or not rs and Message.currentPage()
   local stage=rs and scene and scene.state or Hatch._state
   if text and text~='' and ((rs and scene.printer and not scene.printer:isActive()) or (not rs and not Message.isTyping())) then
    if not seen[text]then seen[text]=true;pages[#pages+1]=text end
    if not shots.hatched and (stage==5 or stage=='hatched_msg')then capture('hatched');shots.hatched=true end
    if not shots.nickname and (stage==9 or stage=='nickname_ask')then capture('nickname');shots.nickname=true end
   end
   if stage==9 or stage=='nickname_ask'then
    if rs then if scene.choice~=1 then press('down')else press('z')end
    elseif Choice.isOpen()then if Choice.cursor~=2 then press('down')else press('z')end end
   else wait(2)end
   if done then break end
  end
  assert(done and shots.hatched and shots.nickname,'Native hatch sequence incomplete')
  assert(not require('src.core.game3.pokemon').isEgg(mon),'Hatching did not update party state')
  local text=table.concat(pages,' ')
  assert(text:find('OVO',1,true) and not text:find('hatched',1,true) and not text:find('nickname',1,true),'English hatch dialogue')
  print('LANGUAGE_HATCH_EVIDENCE '..require('src.link.Json').encode({game=version,pages=pages,trigger='Native hatch scene, saved egg fixture, keyboard naming decision',completed=true}))
  print('LANGUAGE_HATCH_OK',version)
 end,debug.traceback)
 if not ok then print('LANGUAGE_HATCH_FAILED',err)end;love.event.quit(ok and 0 or 1)
end
