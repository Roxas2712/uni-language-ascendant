-- Fixture: fresh save, one injured starter and map position. Dialogue and
-- healing are reached only through the normal map NPC interaction.
local function wait(n) for _=1,n do coroutine.yield() end end
return function(game)
 io.stdout:setvbuf('no')
 if love.setDeprecationOutput then love.setDeprecationOutput(false) end
 local ok,err=xpcall(function()
  local version=require('src.core.GameVersion').get()
  local lang=os.getenv('QA_LANGUAGE') or 'pt-BR'
  local e=assert(game.mods.exports.german_rom_source)
  if lang=='pt-BR' then
   assert(e.status=='active',e.status)
   assert(e.coverage.dialogue==(version=='yellow' and 2710 or 2595))
   assert(game.data.moves.TACKLE.name=='INVESTIDA')
  end
  local function capture(name)
   wait(5);local done=false
   love.graphics.captureScreenshot(function(data)
    local path=os.getenv('SHOT_DIR')..'/'..version..'-'..lang..'-'..name..'.png'
    local f=assert(io.open(path,'wb'));f:write(data:encode('png'):getString());f:close();done=true
   end)
   while not done do wait(1) end
  end
  game.stack:clear()
  local title=require('src.ui.TitleState').new(game,{})
  game.stack:push(title)
  for _=1,500 do title:update(1/60) end
  capture('title')
  game:startNewGame({intro=false})
  game.save.playerName='TESTE'
  game.save.player.name='TESTE'
  local Pokemon=require('src.pokemon.Pokemon')
  local mon=Pokemon.new(game.data,'BULBASAUR',12);mon.hp=1;mon.status='PSN'
  game.save.party={mon}
  game.overworld:setMap('VIRIDIAN_POKECENTER',3,3,'up',{via='boot'})
  wait(90)
  game.overworld:interact()
  local seen,healing,hadChoice,farewell={},false,false,false
  for i=1,1600 do
   local top=game.stack:top()
   if top and top.isTextBox then
    local pages=top.pages or {}
    local page=pages[top.page or top.pageIndex or 1]
    local text=type(page)=='table' and table.concat(page,' | ') or tostring(page)
    if not seen[text] then print('GEN1_NURSE_PAGE',version,lang,text);seen[text]=true end
    if text:find(lang=='pt-BR' and 'Esperamos' or 'hope to see',1,true) then farewell=true end
    if mon.hp>1 and top.done and not healing then capture('healing');healing=true end
   elseif top and top.labels then
    hadChoice=true;print('GEN1_CHOICE',table.concat(top.labels,' / '))
   end
   if top and top~=game.overworld then game:keypressed('z');wait(1);game:keyreleased('z') end
   wait(10)
   if mon.hp>1 and game.stack:top()==game.overworld and healing and farewell then break end
  end
  assert(mon.hp==mon.stats.hp,'Nurse did not restore full HP')
  assert(mon.status==nil or mon.status=='','Nurse did not cure status')
  assert(healing and hadChoice and farewell,'Actual nurse sequence was not completed')
  local def=game.data.maps.VIRIDIAN_CITY
  for _,kind in ipairs({'center','mart'}) do
   for _,warp in ipairs(def.warps) do
    if kind=='center' and warp.destMap:find('POKECENTER') or kind=='mart' and warp.destMap:find('MART') then
     game.overworld:setMap('VIRIDIAN_CITY',warp.x,warp.y+1,'up',{via='boot'})
     wait(90);capture(kind);break
    end
   end
  end
  local Dex=require('src.ui.DexEntryMenu')
  for _,species in ipairs({'ABRA','SNORLAX'}) do
   local entry=Dex.new(game,{species=species,forceOwned=true})
   game.stack:push(entry);wait(90)
   local deadline=love.timer.getTime()+10
   while (entry.picDelay or 0)>0 or entry:crying() do
    assert(love.timer.getTime()<deadline,'Dex cry did not finish')
    wait(1)
   end
   for page=1,entry.pageCount do
    assert(entry.page==page);capture('dex-'..species:lower()..'-'..page)
    game:keypressed('z');wait(1);game:keyreleased('z');wait(90)
   end
   assert(game.stack:top()==game.overworld,'Dex did not close')
  end
  local Battle=require('src.battle.BattleState')
  local initialPP=mon.moves[1].pp
  local result,menuShot,moveShot=nil,false,false
  local battle=Battle.newWild(game,'RATTATA',2)
  -- A durable, faster Rattata with Tail Whip exercises real stat changes
  -- through move selection/damage rules rather than injecting a message.
  battle.enemy.mon.moves={{id='TAIL_WHIP',pp=30}}
  battle.enemy.curMoves=battle.enemy.mon.moves
  battle.enemy.mon.hp=40; battle.enemy.mon.stats.hp=40
  battle.enemy.mon.stats.speed=100
  battle.onFinish=function(value) result=value end
  game.stack:push(battle)
  local messages,statShot={},false
  for i=1,2400 do
   if battle.phase=='moveSelect' and not menuShot then capture('move-menu');menuShot=true end
   local text=battle.current and battle.current.text
   if text and not messages[text] then
    messages[text]=true;print('GEN1_BATTLE_PAGE',version,lang,(text:gsub('[\n\v\f]',' | ')))
   end
   if text and text:find(lang=='pt-BR' and 'INVESTIDA' or 'TACKLE',1,true) and not moveShot then
    wait(30);capture('move-used');moveShot=true
   end
   if text and text:find(lang=='pt-BR' and 'DEFESA caiu!' or 'DEFENSE fell!',1,true) and not statShot then
    wait(30);capture('stat-decreased');statShot=true
   end
   if lang=='pt-BR' and text then
    assert(not text:find(' fell!',1,true) and not text:find(' rose!',1,true),'English stat change: '..text)
   end
   game:keypressed('z');wait(1);game:keyreleased('z');wait(10)
   if result then break end
  end
  assert(result=='win','Battle did not finish in a win: '..tostring(result))
  assert(mon.moves[1].pp<initialPP,'Selected move did not consume PP')
  assert(menuShot and moveShot,'Actual move menu/use not observed')
  assert(statShot and battle.player.stages.defense<0,'Real Tail Whip stat change not observed')
  print('GEN1_BATTLE_OK',version,lang,result,initialPP-mon.moves[1].pp)
  -- Actual engine diploma and full credit roll. Open the certificate UI
  -- directly; this fixture does not claim a completed Pokédex/playthrough.
  game.stack:clear()
  local diploma=require('src.ui.Diploma').new(game)
  game.stack:push(diploma);capture('diploma')
  if version=='yellow' then
   local canvas=love.graphics.newCanvas(160,288)
   love.graphics.push('all');love.graphics.setCanvas(canvas)
   love.graphics.origin();love.graphics.clear(1,1,1,1)
   require('src.ui.Diploma').renderPrint(game)
   love.graphics.pop()
   local image=canvas:newImageData()
   local f=assert(io.open(os.getenv('SHOT_DIR')..'/'..version..'-'..lang..'-diploma-print.png','wb'))
   f:write(image:encode('png'):getString());f:close()
  end
  game.stack:clear()
  local credits=require('src.ui.Credits').new(game)
  assert(#credits.screens>=30,'Native credits missing')
  for _,screen in ipairs(credits.screens) do
   for _,line in ipairs(screen.lines) do
    assert((line.column+require('src.render.Font').glyphCount(line.text))*8<=160,'Credit line cropped: '..line.text)
   end
  end
  game.stack:push(credits)
  local frames,shown=0,{}
  while credits.phase~='end_wait' and frames<15000 do
   credits:update(1/60);frames=frames+1
   if credits.phase=='hold' and not shown[credits.index] then
    shown[credits.index]=true
    if credits.index==1 or credits.index==6 or credits.index==28 then capture('credits-'..credits.index) end
   end
  end
  assert(credits.phase=='end_wait','Native credit roll did not finish')
  capture('credits-end')
  print('GEN1_CREDITS_OK',version,lang,#credits.screens,frames)
  print('GEN1_PTBR_LIVE_OK',version,lang,mon.hp)
 end,debug.traceback)
 if not ok then print('GEN1_PTBR_LIVE_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
