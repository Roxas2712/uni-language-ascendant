-- Original field scripts and NPCs. Fixtures only set saved state and position.
return function(game)
 io.stdout:setvbuf("line")
 local function wait(n)for _=1,n do coroutine.yield()end end
 local ok,err=xpcall(function()
  assert(require('src.core.GameVersion').get()=='emerald')
  if love.setDeprecationOutput then love.setDeprecationOutput(false)end
  game:_handleBootAction({action='new_game',name='TEST',gender=0,start={map='EM_OLDALE_TOWN',x=6,y=17,facing='up'}});wait(90)
  assert(require('src.core.game3.party').giveMon(game.session,1,30,nil,{fixedPersonality=0}))
  local Map=require('src.core.game3.map');local Field=require('src.core.game3.field')
  local Message=require('src.ui.game3.message');local Choice=require('src.ui.game3.choice')
  local Rse=require('src.core.game3.rse.init');local Space=require('src.core.game3.scripting.space')
  local Flags=require('src.core.game3.scripting.flags');local IR=require('src.core.game3.scripting.text_ir')
  local D=require('src.core.game3.rse.frontier.trainers')
  local function press(k)game:keypressed(k);wait(1);game:keyreleased(k);wait(8)end
  local function normal(s)return s:gsub('%s+',' '):match('^%s*(.-)%s*$')end
  local cases={}
  for facility=0,9 do cases[#cases+1]={id='maniac-'..facility,map='EM_BATTLE_FRONTIER_LOUNGE2',kind='maniac',index=facility}end
  for nature=0,24 do cases[#cases+1]={id='nature-'..nature,map='EM_BATTLE_FRONTIER_LOUNGE5',kind='nature',index=nature}end
  for challenge=0,11 do cases[#cases+1]={id='gambler-'..challenge,map='EM_BATTLE_FRONTIER_LOUNGE3',kind='gambler',index=challenge}end
  if os.getenv('QA_FRONTIER_SAMPLE')then cases={cases[1],cases[5],cases[11],cases[36]}end
  for _,case in ipairs(cases)do
   assert(Map.load(nil,game,case.map,{x=8,y=5,facing='up'}));wait(30)
   local target
   if case.kind=='maniac' then
    Flags.setFlag(Space.store,Space.vm.ctx,0x154,true)
    Rse.setVar('VAR_FRONTIER_MANIAC_FACILITY',case.index,game.session)
    target=D.manifest().maniacMessages[case.index*3+1].ir
   elseif case.kind=='nature' then
    game.session.party[1].nature=case.index;target=D.manifest().natureGirlMessages[case.index+1].ir
   else
    Flags.setFlag(Space.store,Space.vm.ctx,0x157,true)
    Rse.setVar('VAR_FRONTIER_GAMBLER_STATE',0,game.session)
    Rse.setVar('VAR_FRONTIER_GAMBLER_CHALLENGE',case.index,game.session)
    target=D.manifest().gamblerLookingMessages[case.index+1].ir
   end
   local expected=IR.toPlain(target,{})
   assert(not expected:find('This one',1,true) and not expected:find('BATTLE TOWER',1,true),'Untranslated Frontier record')
   local object=assert(require('src.core.game3.objects').find(1))
   local Player=require('src.core.game3.player');Player.reset(object.cellX,object.cellY+1,'up');Player.syncSavePosition(game)
   assert(not Field.isLocked() and not Message.isOpen())
   Field.interact(game)
   local pages,seen={},{};local shot=false
   local tail=normal(expected:match('([^\n]+)$'))
   for _=1,850 do
    local page=Message.currentPage()
    if page and page~='' and not seen[page]then
     pages[#pages+1]=page;seen[page]=true
     if normal(expected):find(normal(page),1,true) and normal(page)~='Hmhm…' and not shot then
      Message.skipReveal();wait(5)
      if os.getenv('QA_FRONTIER_SAMPLE') or case.index==0 then
       game.capturePath=os.getenv('SHOT_DIR')..'/emerald-pt-BR-frontier-'..case.id..'.png'
       for _=1,600 do if not game.capturePath then break end;wait(1)end;assert(not game.capturePath)
      end;shot=true
     end
    end
    if Choice.isOpen() and case.kind=='gambler' then
     assert(Choice.kind=='yesno');if Choice.cursor~=2 then press('down')end;press('z')
    else press('z')end
    if not Field.isLocked() and not Message.isOpen() and not Choice.isOpen()then break end
   end
   assert(shot,'Native NPC record not reached: '..case.id..' / '..table.concat(pages,' | '))
   assert(not Field.isLocked(),'NPC script still locked: '..case.id)
   assert(normal(table.concat(pages,' ')):find(tail,1,true),'NPC tail missing: '..case.id)
   if case.id=='maniac-9' then
    local name=require('src.core.game3.rom_text').plain('stdstring:29')
    assert(name~='29' and normal(table.concat(pages,' ')):find(normal(name),1,true),
     'Battle Pyramid placeholder was not resolved in the actual NPC dialogue')
   end
   print('LANGUAGE_FRONTIER_EVIDENCE '..require('src.link.Json').encode({case=case.id,map=case.map,trigger='Field.interact / keyboard',pages=pages,completed=true}))
  end
  print('LANGUAGE_FRONTIER_OK',#cases)
 end,debug.traceback)
 if not ok then print('LANGUAGE_FRONTIER_FAILED',err)end;love.event.quit(ok and 0 or 1)
end
