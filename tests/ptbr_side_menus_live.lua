-- Native menu coverage with fixture inventory. Text is always read by the
-- game's own UI/data modules; this driver never supplies display text.
return function(game)
 io.stdout:setvbuf("line")
 local function wait(n)for _=1,n do coroutine.yield()end end
 local ok,err=xpcall(function()
  if love.setDeprecationOutput then love.setDeprecationOutput(false)end
  local version=require('src.core.GameVersion').get()
  local rs=version=='ruby' or version=='sapphire'
  local prefix=assert(({ruby='RU_',sapphire='SA_',emerald='EM_'})[version])
  assert(game.mods.exports.german_rom_source.language=='pt-BR')
  game:_handleBootAction({action='new_game',name='TEST',gender=0,start={map=prefix..'OLDALE_TOWN',x=6,y=17,facing='up'}})
  wait(90)
  assert(require('src.core.game3.party').giveMon(game.session,1,20,nil,{fixedPersonality=0}))
  local Font=require('src.ui.game3.frlg_font');local original=Font.draw;local drawn={}
  Font.draw=function(text,x,y,opts)drawn[text]={x=x,y=y,width=Font.measure(text,opts)};return original(text,x,y,opts)end
  local function capture(name)
   wait(30);game.capturePath=os.getenv('SHOT_DIR')..'/'..version..'-pt-BR-side-'..name..'.png'
   for _=1,600 do if not game.capturePath then break end;wait(1)end
   assert(not game.capturePath);print('LANGUAGE_SIDE_CAPTURE',version,name)
  end
  local function press(key)game:keypressed(key);wait(1);game:keyreleased(key);wait(8)end
  if not os.getenv('QA_SIDE_DECOR_ONLY')then
  local f=assert(io.open(os.getenv('GERMAN_MOD_ROOT')..'/translations/pt-BR/berry-descriptions.json'))
  local expected=require('src.link.Json').decode(f:read('*a'));f:close()
  local Tag=require(rs and 'src.ui.game3.rs.berry_tag' or 'src.ui.game3.rse.berry_tag')
  local bad={}
  for id=1,43 do
   Tag.show({session=game.session,berryId=id});wait(30)
   local info=Tag.berryInfo(id)
   for line=1,2 do
    local text=info['description'..line]
    assert(text==expected[tostring(id)][line],'Berry description not translated '..id..' / '..text)
    assert(drawn[text],'Native berry screen did not draw description '..id)
    if drawn[text].x+drawn[text].width>240 then bad[#bad+1]={berry=id,line=line,text=text,draw=drawn[text]}end
   end
   if id==1 or id==17 or id==43 then capture('berry-'..id)end
   Tag.reset();wait(2)
  end
  print('LANGUAGE_BERRY_LAYOUT',require('src.link.Json').encode(bad));assert(#bad==0,'Berry description exceeds native screen')
  local Blocks=require('src.core.game3.rse.pokeblock')
  for i=1,14 do assert(Blocks.add(game.session,{color=i,spicy=20,dry=15,sweet=10,bitter=5,sour=0,feel=20}))end
  local Case=require(rs and 'src.ui.game3.rs.pokeblock_case' or 'src.ui.game3.rse.pokeblock_case')
  Case.show({session=game.session});capture('pokeblocks');press('z');capture('pokeblock-actions');Case.reset();wait(10)
  for i=0,13 do
   local name=Blocks.name(Blocks.get(game.session,i))
   assert(Font.measure(name,rs and {font='native_3'} or {font='narrow'})<=90,'Pokeblock name overlaps level: '..name)
  end
  end
  local Inv=require('src.core.game3.rse.decoration_inventory')
  for id=1,120 do assert(Inv.add(id,game.session))end
  local Decor=require(rs and 'src.ui.game3.rs.decoration' or 'src.ui.game3.rse.decoration')
  Decor.open({session=game.session});capture('decorations');press('z');capture('decoration-categories')
  local host=require('src.ui.game3.rse.decoration');local overflow={}
  local descOpts=rs and {font='native_3'} or {}
  local nameOpts=rs and {font='native_3'} or {font='narrow'}
  for cat=0,7 do
   assert(host.view=='categories');press('z');assert(host.view=='items')
   local inv=Inv.inventories(game.session)[cat]
   for index,id in ipairs(inv)do if id~=0 then
    local row=assert(Inv.info(id));wait(2)
    assert(drawn[row.description],'Description not rendered by native menu: '..id)
    local lines,maxWidth={},0;for line in (row.description..'\n'):gmatch('(.-)\n')do lines[#lines+1]=line;maxWidth=math.max(maxWidth,Font.measure(line,descOpts))end
    if #lines>3 or maxWidth>104 or Font.measure(row.name,nameOpts)>96 then overflow[#overflow+1]={id=id,name=row.name,lines=lines,width=Font.measure(row.name,nameOpts),descriptionWidth=maxWidth}end
    if index==1 then capture('decoration-category-'..cat)end
    press('down')
   end end
   press('x');assert(host.view=='categories');press('down')
  end
  print('LANGUAGE_DECORATION_LAYOUT',require('src.link.Json').encode(overflow));assert(#overflow==0,'Decoration panel overflow')
  Decor.reset();wait(10)
  Font.draw=original
  local f=assert(io.open(os.getenv('SHOT_DIR')..'/'..version..'-side-drawn-text.json','w'));f:write(require('src.link.Json').encode(drawn));f:close()
  print('LANGUAGE_SIDE_MENUS_OK',version,43)
 end,debug.traceback)
 if not ok then print('LANGUAGE_SIDE_MENUS_FAILED',err)end
 love.event.quit(ok and 0 or 1)
end
