-- Real native summary screen; controlled party fixture, no message injection.
return function(game)
 local function wait(n)for _=1,n do coroutine.yield() end end
 local ok,err=xpcall(function()
  local version=require('src.core.GameVersion').get()
  if love.setDeprecationOutput then love.setDeprecationOutput(false) end
  assert(game.mods.exports.german_rom_source.language=='pt-BR')
  if os.getenv('QA_DUMP_ASSETS') then
   for path,bytes in pairs(game.mods.exports.german_rom_source.assets) do
    if path:find('/rse/summary/',1,true) then
     local f=assert(io.open(os.getenv('SHOT_DIR')..'/native-'..version..'-summary-'..path:match('[^/]+$'),'wb'));f:write(bytes);f:close()
    end
   end
  end
  if version=='ruby' or version=='sapphire' then
   local path='data/generated/gba/rse/summary/interface.gfx'
   assert(require('src.import.CacheBlob').readFs(path)==game.mods.exports.german_rom_source.assets[path],
    'Native raw summary tiles bypassed the active language overlay')
  end
  local prefix=({ruby='RU_',sapphire='SA_',emerald='EM_',firered='FR_',leafgreen='FR_'})[version]
  local town=(version=='firered' or version=='leafgreen') and 'VIRIDIAN_CITY' or 'OLDALE_TOWN'
  game:_handleBootAction({action='new_game',name='TEST',gender=0,start={map=prefix..town,x=6,y=17,facing='up'}})
  wait(90)
  assert(require('src.core.game3.party').giveMon(game.session,1,15,nil,{fixedPersonality=0}))
  local Summary=require('src.ui.game3.summary_menu')
  local Data=require('src.core.game3.summary_data')
  local Font=require('src.ui.game3.frlg_font')
  local draw=Font.draw
  local observed={}
  local memoRuns
  Font.draw=function(text,x,y,opts)
   observed[text]={x=x,y=y,opts=opts}
   if memoRuns and x>=88 and y>=112 then memoRuns[#memoRuns+1]={text=text,x=x,y=y,opts=opts} end
   return draw(text,x,y,opts)
  end
  if version=='emerald' then
   local mon=game.session.party[1]
   local sections=require('src.ui.game3.rse.mapsec').pack().sections
   local saved={location=mon.metLocation,level=mon.metLevel,ot=mon.otName,personality=mon.personality}
   Summary.openMenu(game.session.party,1,{session=game.session,page=0});wait(100)
   local count=0
   local function checkMemo(label)
    memoRuns={};wait(2)
    assert(#memoRuns>0,'Native memo was not rendered: '..label)
    for _,run in ipairs(memoRuns)do
     assert(run.x+Font.measure(run.text,run.opts)<=232,'Native memo clips horizontally: '..label..' / '..run.text)
     assert(run.y<152,'Native memo clips vertically: '..label..' / '..run.text)
    end
    count=count+1;memoRuns=nil
   end
   for id,row in pairs(sections)do
    mon.metLocation=id;mon.metLevel=100;mon.metLocationName=nil
    checkMemo(row.id)
    if row.id=='MAPSEC_BATTLE_FRONTIER' then
     game.capturePath=os.getenv('SHOT_DIR')..'/emerald-pt-BR-memo-frontier.png'
     while game.capturePath do wait(1)end
    end
   end
   for nature=0,24 do
    mon.personality=nature
    for _,scenario in ipairs({{1,5,saved.ot},{1,0,saved.ot},{1,5,'OTHER'},{nil,5,saved.ot},{nil,0,saved.ot},{nil,5,'OTHER'}})do
     mon.metLocation,mon.metLevel,mon.otName=scenario[1],scenario[2],scenario[3]
     checkMemo('nature-'..nature)
    end
   end
   mon.metLocation,mon.metLevel,mon.otName,mon.personality=saved.location,saved.level,saved.ot,saved.personality
   Summary.close();wait(10)
   print('LANGUAGE_MEMO_LAYOUT_OK',version,count)
  end
  for _,id in ipairs({18,143,165,263}) do
   local mon=game.session.party[1];mon.moves={id};mon.pp={10};mon.maxPp={10}
   observed={}
   Summary.openMenu(game.session.party,1,{session=game.session,mode='select_move',forgetMove=true})
   wait(100)
   local text=Data.moveDescription(id,require('src.core.game3.pokemon').moveName(id))
   assert(observed[text],'Native summary did not draw selected description '..id)
   local point=observed[text];local rows=0
   for _ in (text..'\n'):gmatch('(.-)\n') do rows=rows+1 end
   local pitch=point.opts and point.opts.linePitch or Font.linePitch()
   assert(point.y+(rows-1)*pitch<152,'Description last row outside screen: '..id)
   game.capturePath=os.getenv('SHOT_DIR')..'/'..version..'-pt-BR-move-'..id..'.png'
   for _=1,600 do if not game.capturePath then break end;wait(1) end
   assert(not game.capturePath)
   print('LANGUAGE_PANEL_EVIDENCE '..require('src.link.Json').encode({game=version,id=id,text=text,x=point.x,y=point.y,rows=rows,
    fixture='Controlled party move; native select-move screen, actual Font.draw observed'}))
   Summary.close();wait(10)
  end
  Font.draw=draw
  print('LANGUAGE_PANELS_OK',version)
 end,debug.traceback)
 if not ok then print('LANGUAGE_PANELS_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
