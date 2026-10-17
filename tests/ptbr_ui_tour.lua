-- Native UI screens with a controlled fresh save. This is UI coverage, not a
-- story playthrough or fabricated NPC dialogue.
return function(game)
 local function wait(n)for _=1,n do coroutine.yield() end end
 local ok,err=xpcall(function()
  if love.setDeprecationOutput then love.setDeprecationOutput(false) end
  local version=require('src.core.GameVersion').get()
  assert(game.mods.exports.german_rom_source.language=='pt-BR')
  if os.getenv('QA_DUMP_ASSETS') then
   local out=os.getenv('SHOT_DIR')..'/assets-'..version
   os.execute('mkdir -p '..string.format('%q',out))
   for path,bytes in pairs(game.mods.exports.german_rom_source.assets) do
    if path:find('/naming/',1,true) or path:find('/summary/',1,true) or path:find('/storage/',1,true)
     or path:find('/trainer_card/',1,true) or path:find('/pokedex/',1,true) then
     local name=path:gsub('/','__')
     local f=assert(io.open(out..'/'..name,'wb'));f:write(bytes);f:close()
    end
   end
  end
  local unresolved=game.mods.exports.german_rom_source.coverage.assets.pokenavUnresolved
  if unresolved then
   local f=assert(io.open(os.getenv('SHOT_DIR')..'/'..version..'-pokenav-unresolved.json','w'));f:write(require('src.link.Json').encode(unresolved));f:close()
  end
  local scene=game.mods.exports.german_rom_source.coverage.assets.sceneText
  if scene then local f=assert(io.open(os.getenv('SHOT_DIR')..'/'..version..'-scene-audit.json','w'));f:write(require('src.link.Json').encode(scene));f:close()end
  local prefix=({ruby='RU_',sapphire='SA_',emerald='EM_',firered='FR_',leafgreen='FR_'})[version]
  local rs=version=='ruby' or version=='sapphire'
  local rse=rs or version=='emerald'
  local Font=require('src.ui.game3.frlg_font');local draw=Font.draw;local observed={}
  Font.draw=function(text,x,y,opts)
   observed[text]={x=x,y=y,width=Font.measure(text,opts),font=opts and opts.font}
   return draw(text,x,y,opts)
  end
  game:_handleBootAction({action='new_game',name='TEST',gender=0,start={map=prefix..(rse and 'OLDALE_TOWN' or 'VIRIDIAN_CITY'),x=6,y=17,facing='up'}})
  wait(90)
  assert(require('src.core.game3.party').giveMon(game.session,1,15,nil,{fixedPersonality=0}))
  require('src.core.game3.bag').add(game.session.bag,13,3)
  for _,id in ipairs({14,179,200,80})do assert(require('src.core.game3.bag').add(game.session.bag,id,1))end
  local function capture(name)
   wait(100)
   game.capturePath=os.getenv('SHOT_DIR')..'/'..version..'-pt-BR-ui-'..name..'.png'
   for _=1,600 do if not game.capturePath then break end;wait(1) end
   assert(not game.capturePath,'UI screenshot timeout '..name)
   print('LANGUAGE_UI_CAPTURE',version,name)
  end
  if not os.getenv('QA_NAV_ONLY') then
  local Summary=require('src.ui.game3.summary_menu')
  for _,page in ipairs(rse and {0,1,2,3} or {0,1}) do
   Summary.openMenu(game.session.party,1,{session=game.session,page=page});capture('summary-'..page);Summary.close();wait(15)
  end
  local mon=game.session.party[1];local hp=mon.hp
  for _,row in ipairs({{'poison',8},{'sleep',1},{'burn',16},{'paralysis',64},{'freeze',32},{'faint',0}})do
   mon.status=row[2];mon.hp=row[1]=='faint' and 0 or hp
   Summary.openMenu(game.session.party,1,{session=game.session,page=rse and 0 or 1});capture('status-'..row[1]);Summary.close();wait(15)
  end
  mon.status=0;mon.hp=hp
  if rse then
   local mapsec=require('src.ui.game3.rse.mapsec')
   local sections=mapsec.pack().sections
   local saved={location=mon.metLocation,name=mon.metLocationName,level=mon.metLevel}
   for _,wanted in ipairs({'MAPSEC_GRANITE_CAVE','MAPSEC_SECRET_BASE',version=='emerald' and 'MAPSEC_BATTLE_FRONTIER' or 'MAPSEC_BATTLE_TOWER'})do
    local id,row
    for k,v in pairs(sections)do if v.id==wanted then id,row=k,v;break end end
    assert(row,'Missing location fixture '..wanted)
    mon.metLocation=id;mon.metLocationName=nil;mon.metLevel=5
    Summary.openMenu(game.session.party,1,{session=game.session,page=0})
    capture('location-'..wanted:lower());Summary.close();wait(15)
   end
   mon.metLocation=saved.location;mon.metLocationName=saved.name;mon.metLevel=saved.level
  end
  local Bag=require('src.ui.game3.bag_menu')
  Bag.show(game.session,{session=game.session});capture('bag');Bag.close();wait(15)
  local Card=require(rs and 'src.ui.game3.rs.trainer_card' or 'src.ui.game3.trainer_card')
  Card.show({session=game.session});capture('trainer-front')
  game:keypressed('z');wait(1);game:keyreleased('z');capture('trainer-back');Card.close();wait(15)
  local PC=require('src.ui.game3.pc_menu')
  PC.show({session=game.session,startMode='storage'});capture('pc');PC.close();wait(15)
  local Box=require('src.ui.game3.box_storage_ui')
  Box.show({session=game.session});capture('boxes');Box.close();wait(15)
  local Naming=require('src.ui.game3.naming')
  Naming.open({template='PLAYER',session=game.session,initialText='TEST'});capture('naming')
  assert(Naming._state.title:find('SEU NOME',1,true),'Actual naming screen used English manifest: '..Naming._state.title)
  Naming.close();wait(15)
  local Dex=require(rse and 'src.ui.game3.rse.pokedex' or 'src.ui.game3.pokedex')
  Dex.show(game.session.dex,{session=game.session});capture('dex-list')
  if rse then Dex.reset() else Dex.close() end
  end
  if rse then
   game.session.party[1].contest={cool=255,beauty=255,cute=255,smart=255,tough=255,sheen=255}
   local Nav=require(rs and 'src.ui.game3.rs.pokenav.init' or 'src.ui.game3.rse.pokenav.init')
   local state=Nav.show({session=game.session,game=game});capture('pokenav')
   if rs then
    state:setMenu('condition');capture('pokenav-condition')
    state:setMenu('search');capture('pokenav-search')
    state:openCondition();capture('pokenav-graph')
    state:setMenu('main');wait(25);state:openMap();capture('pokenav-map')
    local Data=require('src.ui.game3.rs.pokenav.data')
    local store=require('src.core.game3.scripting.space').store or game.session
    for _,row in pairs(state.detail.rematches)do store.flags[Data.TRAINER_FLAG_START+row.opponentIDs[1]]=true end
    for _,row in pairs(state.detail.leaders)do store.flags[Data.TRAINER_FLAG_START+row.opponentId]=true end
    state:setMenu('main');wait(25);state:openEyes();capture('pokenav-trainers')
    local entries=assert(state.feature).entries;assert(#entries==69,'Trainer fixture registration incomplete')
    local over={}
    for i,row in ipairs(entries)do
     state.feature.index=i;state.feature.detail=true;state.feature.portraitX=0
     wait(3)
     for _,line in ipairs(state.detail.descriptions[row.descriptionId])do
      if Font.measure(line,{font='native_3'})>136 then over[#over+1]={id=row.descriptionId,line=line,width=Font.measure(line,{font='native_3'})} end
      assert(observed[line],'Trainer text was not drawn by native screen: '..line)
     end
     if i==1 or i==6 or i==69 then capture('pokenav-trainer-'..row.descriptionId)end
    end
    print('LANGUAGE_POKENAV_TRAINER_LAYOUT',require('src.link.Json').encode(over))
    assert(#over==0,'Trainer description overflows native panel')
   else
    local function press(key)
     game:keypressed(key);wait(1);game:keyreleased(key);wait(100)
    end
    press('down');press('z');capture('pokenav-condition_menu')
    assert(state.screen.handler=='condition')
    press('down');press('z');capture('pokenav-condition_search_menu')
    assert(state.screen.handler=='search')
    press('x');press('up');press('z')
    capture('pokenav-condition_graph_party')
    assert(state.menuId=='condition_graph_party',state.menuId)
    press('x');press('x');press('up');press('z')
    capture('pokenav-region_map');assert(state.menuId=='region_map',state.menuId)
    press('z');capture('pokenav-region_map-zoom')

   end
   Nav.reset();wait(15)
  end
  Font.draw=draw
  local f=assert(io.open(os.getenv('SHOT_DIR')..'/'..version..'-ui-drawn-text.json','w'))
  f:write(require('src.link.Json').encode(observed));f:close()
  print('LANGUAGE_UI_TOUR_OK',version)
 end,debug.traceback)
 if not ok then print('LANGUAGE_UI_TOUR_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
