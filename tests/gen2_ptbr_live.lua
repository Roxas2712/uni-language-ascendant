-- Real Gen-2 NPC and battle paths. Only party/map setup is a QA fixture.
local function wait(n) for _=1,n do coroutine.yield() end end
return function(game)
 io.stdout:setvbuf('no')
 if love.setDeprecationOutput then love.setDeprecationOutput(false) end
 local ok,err=xpcall(function()
  local version=require('src.core.GameVersion').get()
  local lang=os.getenv('QA_LANGUAGE') or 'pt-BR'
  local e=assert(game.mods.exports.german_rom_source)
  if lang=='pt-BR' then assert(e.status=='active',e.status);assert(game.data.moves.TACKLE.name=='INVESTIDA') end
  local function capture(name)
   wait(15);local done=false
   love.graphics.captureScreenshot(function(data)
    local path=os.getenv('SHOT_DIR')..'/'..version..'-'..lang..'-'..name..'.png'
    local f=assert(io.open(path,'wb'));f:write(data:encode('png'):getString());f:close();done=true
   end)
   while not done do wait(1) end
  end
  local Font=require('src.render.Font')
  local originalEncode=Font.encode
  local observed={}
  Font.encode=function(text)
   if type(text)=='string' then
    local hook=Font.__ulaPtbrGen2
    observed[text]=hook and hook.active() and hook.localize(text) or text
   end
   return originalEncode(text)
  end
  game:showTitle();wait(180);capture('title')
  local Save=require('src.core.gen2.Save')
  game:continueGame(Save.newGame({playerName='TESTE',trainerId=12345}))
  local Mon=require('src.battle.gen2.Mon')
  local mon=assert(Mon.new(game.data,'CHIKORITA',12));mon.hp=1;mon.status='PSN'
  game.save.party={mon}
  local world=game.world
  world:setMap('CHERRYGROVE_POKECENTER_1F',3,3,'up',{via='boot',continue=true})
  for _=1,600 do if not world:busy() then break end;wait(1) end
  print('GEN2_INTERACT',world.player.cellX,world.player.cellY,world.player.facing,world:busy(),world:facingObjectCell())
  assert(world:interact(),'Nurse interaction did not start')
  local seen,healing,farewell,choice={},false,false,false
  for _=1,600 do
   local top=game.stack:top()
   if top and top.isTextBox then
    local page=top.pages[top.pageIndex or 1];local text=table.concat(page,' | ')
    if not seen[text] then print('GEN2_NURSE_PAGE',version,lang,text);seen[text]=true end
    if text:find(lang=='pt-BR' and 'Esperamos' or 'hope to see',1,true) then farewell=true end
    if mon.hp>1 and top.done and not healing then capture('healing');healing=true end
   elseif top and top.labels then
    if not choice then capture('choice') end
    local Strings=require('src.core.Strings')
    local labels={};for i,label in ipairs(top.labels) do labels[i]=Strings(label) end
    if lang=='pt-BR' then
     assert(labels[1]=='SIM' and labels[2]=='NÃO','Untranslated actual choice labels')
     assert(observed[labels[1]]=='SIM' and observed[labels[2]]=='NÃO','Choice labels were not rendered')
    end
    choice=true;print('GEN2_CHOICE',table.concat(labels,' / '))
   end
   if top then game:keypressed('z');wait(1);game:keyreleased('z') end
   wait(10)
   if mon.hp>1 and not game.stack:top() and healing and farewell then break end
  end
  assert(mon.hp==mon.maxHp and not mon.status,'Nurse did not heal/cure actual party')
  assert(healing and farewell and choice,'Nurse sequence did not complete')
  local def=game.data.gen2Maps.CHERRYGROVE_CITY
  for _,kind in ipairs({'center','mart'}) do
   for _,warp in ipairs(def.warps) do
    if kind=='center' and warp.destMap:find('POKECENTER') or kind=='mart' and warp.destMap:find('MART') then
     world:setMap('CHERRYGROVE_CITY',warp.x,warp.y+1,'up',{continue=true});wait(90);world:cancelMapNameSign();capture(kind);break
    end
   end
  end
  local gymMap=game.data.gen2Maps.VIOLET_CITY
  for _,warp in ipairs(gymMap.warps) do
   if warp.destMap:find('GYM') then
    world:setMap('VIOLET_CITY',warp.x,warp.y+1,'up',{continue=true})
    wait(90);world:cancelMapNameSign();capture('gym');break
   end
  end
  do
   local Font=require('src.render.Font')
   if lang=='pt-BR'then
    local f=assert(io.open(os.getenv('GERMAN_MOD_ROOT')..'/translations/pt-BR/gen2-catalog-corrections.json'))
    local names=require('src.link.Json').decode(f:read('*a')).item_names;f:close()
    for id,target in pairs(names)do
     assert(game.data.items[id].name==target,'Item name not applied: '..id)
     assert(Font.width(target)<=96,'Item name exceeds native list: '..id)
    end
   end
   for _,category in ipairs({'moves','items'}) do
    for id,record in pairs(game.data[category]) do
     if type(record)=='table' and record.description then
      local lines=0
      for line in record.description:gsub('<NEXT>','\n'):gmatch('[^\n]+') do
       lines=lines+1;assert(#Font.encode(line)<=18,category..' description overflow '..id..': '..line)
      end
      assert(lines<=2,category..' description line count '..id)
     end
    end
   end
   print('GEN2_DESCRIPTION_LAYOUT_OK',version,lang)
   for id,entry in pairs(game.data.gen2Pokedex.entries) do
    assert(Font.width(entry.kind)<=88,'Dex category clips: '..id)
    for _,field in ipairs({'text','text2'}) do
     local lines=0
     for line in (entry[field]..'<NEXT>'):gmatch('(.-)<NEXT>') do
      assert(Font.width(line)<=144,'Dex line clips: '..id..'/'..field..'/'..line);lines=lines+1
     end
     assert(lines<=3,'Dex page overflows: '..id..'/'..field)
    end
   end
   print('GEN2_DEX_LAYOUT_OK',version,lang,251)
   local Dex=require('src.ui.gen2.PokedexMenu')
   for _,species in ipairs({'ABRA','SNORLAX'}) do
    game.save.pokedex.seen[species]=true;game.save.pokedex.caught[species]=true
    local dex=Dex.new(game,{onClose=function() game.stack:pop() end})
    for i,row in ipairs(dex.rows) do if row.species==species then dex.index=i;break end end
    game.stack:push(dex);game:keypressed('z');wait(1);game:keyreleased('z');wait(90)
    assert(dex.view=='entry','Did not open actual Pokédex entry')
    for page=1,2 do
     assert(dex.page==page)
     print('GEN2_DEX_PAGE',version,lang,species,page,game.data.gen2Pokedex.entries[species][page==1 and 'text' or 'text2'])
     capture('dex-'..species:lower()..'-'..page)
     game:keypressed('z');wait(1);game:keyreleased('z');wait(60)
    end
    game:keypressed('x');wait(1);game:keyreleased('x');wait(30)
    game:keypressed('x');wait(1);game:keyreleased('x');wait(30)
    assert(not game.stack:top(),'Pokédex did not close')
   end
  end
  local function press(key)
   game:keypressed(key);wait(1);game:keyreleased(key);wait(30)
  end
  local function closeMenu()
   press('x');assert(not game.stack:top(),'Actual menu did not close')
  end
  -- These are the normal game menus and key paths. Only inventory/card
  -- acquisition is seeded, just as the injured party above is a fixture.
  local Bag=require('src.inventory.Bag')
  assert(Bag.add(game.save,'POTION',3,game.data))
  assert(Bag.add(game.save,'SACRED_ASH',1,game.data))
  assert(Bag.add(game.save,'LEFTOVERS',1,game.data))
  assert(Bag.add(game.save,'POKE_BALL',5,game.data))
  local pack=require('src.ui.gen2.PackMenu').new(game,{onClose=function() game.stack:pop() end})
  game.stack:push(pack);wait(30);capture('pack-items');press('right');capture('pack-balls');closeMenu()
  local card=require('src.ui.gen2.TrainerCard').new(game,{onClose=function() game.stack:pop() end})
  game.stack:push(card);wait(30);capture('trainer-card');press('right');capture('trainer-badges');closeMenu()
  game.save.pokegearFlags={map=true,phone=true,radio=true}
  local gear=require('src.ui.gen2.Pokegear').new(game,{onClose=function() game.stack:pop() end})
  game.stack:push(gear);wait(30)
  for _,name in ipairs({'clock','map','phone','radio'}) do
   assert(gear:card().id==name,gear:card().id)
   capture('pokegear-'..name);press('right')
  end
  -- B first returns from the radio card to the card strip, then exits.
  press('x');assert(gear.mode=='strip');closeMenu()
  local dex=require('src.ui.gen2.PokedexMenu').new(game,{onClose=function() game.stack:pop() end})
  game.stack:push(dex);wait(30);capture('dex-list');closeMenu()
  local diploma=require('src.ui.gen2.Diploma').new(game,{onClose=function()game.stack:pop()end})
  game.stack:push(diploma);wait(30);capture('diploma');closeMenu()
  local pp=mon.moves[1].pp;local result,menuShot,moveShot=nil,false,false
  world:startBattle({wild=Mon.new(game.data,'RATTATA',2)},function(value) result=value end)
  local messages={}
  for _=1,3000 do
   local top=game.stack:top()
   if top and top.isBattle then
    if top.phase=='moves' and not menuShot then capture('move-menu');menuShot=true end
    local text=top.message
    if text and not messages[text] then print('GEN2_BATTLE_PAGE',version,lang,(text:gsub('[\n\v\f]',' | ')));messages[text]=true end
    if text and text:find(lang=='pt-BR' and 'INVESTIDA' or 'TACKLE',1,true) and not moveShot then wait(50);capture('move-used');moveShot=true end
   end
   game:keypressed('z');wait(1);game:keyreleased('z');wait(10)
   if result then break end
  end
  assert(result=='win','Battle outcome: '..tostring(result))
  assert(mon.moves[1].pp<pp,'Move did not consume PP')
  local credits=require('src.ui.gen2.Credits').new(game,{onDone=function()game.stack:pop()end})
  local frames=assert(credits:runToEnd(),'Actual credit script did not finish')
  game.stack:push(credits);wait(10);capture('credits-end');press('z')
  assert(credits.done and not game.stack:top(),'Credits did not exit through A')
  print('GEN2_CREDITS_SCRIPT_OK',version,lang,frames)
  assert(menuShot and moveShot,'Move selection/use not observed')
  if lang=='pt-BR' then
   for text in pairs(messages) do assert(not text:match('Wild ') and not text:match(' fainted') and not text:match(' gained ') and not text:match('Enemy '),'English battle remainder: '..text) end
  end
  local trace=assert(io.open(os.getenv('SHOT_DIR')..'/'..version..'-'..lang..'-observed-ui.json','w'))
  trace:write(require('src.link.Json').encode(observed));trace:close()
  Font.encode=originalEncode
  print('GEN2_PTBR_LIVE_OK',version,lang,pp-mon.moves[1].pp)
 end,debug.traceback)
 if not ok then print('GEN2_PTBR_LIVE_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
