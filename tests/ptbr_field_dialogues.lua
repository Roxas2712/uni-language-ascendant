-- Real NPC interactions with explicit saved-story preconditions. Never opens
-- a message or supplies dialogue to the renderer. Pages come from the field VM.
return function(game,capture,lang)
 local Map=require('src.core.game3.map')
 local Field=require('src.core.game3.field')
 local Message=require('src.ui.game3.message')
 local Flags=require('src.core.game3.scripting.flags')
 local Space=require('src.core.game3.scripting.space')
 local Text=require('src.core.game3.rom_text')
 local Json=require('src.link.Json')
 local function wait(n) for _=1,n do coroutine.yield() end end
 local cases={
  {id='rooftop-weather',map='EM_LILYCOVE_CITY_DEPARTMENT_STORE_5F',x=9,y=6,
   objectId=7,key='g3:082201c4',fixture='VAR_SOOTOPOLIS_CITY_STATE=1 (legendary weather)',
   prepare=function() Flags.setVar(Space.vm.store,Space.vm.ctx,0x405E,1) end,
   pt='Acho que fecharam',en='closed the rooftop'},
  {id='captain-scanner',map='EM_ABANDONED_SHIP_CAPTAINS_OFFICE',x=3,y=5,
   objectId=1,key='g3:08238918',fixture='FLAG_EXCHANGED_SCANNER=true (scanner delivered)',
   prepare=function() Flags.setFlag(Space.vm.store,Space.vm.ctx,0x126,true) end,
   pt='Este navio',en='This ship is called'},
  {id='lottery-prize',map='EM_LILYCOVE_CITY_DEPARTMENT_STORE_1F',x=10,y=4,
   objectId=2,distance=2,dynamic=true,key='LilycoveCity_DepartmentStore_1F_Text_PrizeWeveBeenHolding',
   fixture='pending lottery Master Ball prize; actual player name TEST',
   prepare=function()
    local Rse=require('src.core.game3.rse.init')
    Rse.setVar('VAR_POKELOT_PRIZE_ITEM',1,game.session)
    Rse.setVar('VAR_POKELOT_PRIZE_PLACE',4,game.session)
   end,
   pt='Sim, eu estava',en="I've been expecting"},
 }
 for _,case in ipairs(cases) do
  case.prepare()
  assert(Map.load(nil,game,case.map,{x=case.x,y=case.y,facing='up'}))
  wait(45)
  assert(not Message.isOpen() and not Field.isLocked(),'Fixture not ready: '..case.id)
  local Player=require('src.core.game3.player')
  local Objects=require('src.core.game3.objects')
  -- The weather map script relocates the woman to the closed staircase.
  -- Stand beside her actual event object after that script has run.
  local object=assert(Objects.find(case.objectId),'Expected NPC missing')
  Player.reset(object.cellX,object.cellY+(case.distance or 1),'up');Player.syncSavePosition(game)
  local bagBefore=require('src.core.game3.bag').get(game.session.bag,1)
  Field.interact(game)
  local pages,seen,shot={}, {},false
  local expected=lang=='pt-BR' and case.pt or case.en
  for _=1,450 do
   local page=Message.currentPage()
   if type(page)=='string' and page~='' and not seen[page] then
    pages[#pages+1]=page;seen[page]=true
   end
   if page and page:find(expected,1,true) and not shot then
    Message.skipReveal();capture(case.id);shot=true
   end
   game:keypressed('z');wait(1);game:keyreleased('z');wait(10)
   if not Message.isOpen() and not Field.isLocked() then break end
  end
  assert(shot,'Expected actual NPC dialogue not reached: '..case.id..' / '..table.concat(pages,' | '))
  assert(not Field.isLocked(),'NPC script did not release control: '..case.id)
  local normalize=function(s)return s:gsub('%s+',' '):match('^%s*(.-)%s*$') end
  local context={playerName='TEST'}
  local expectedText=normalize(Text.plain(case.key,context))
  -- Scrolling pages overlap; compare every actual page to the complete IR,
  -- and require the dialogue's final line to have appeared on screen.
  if not case.dynamic then for _,page in ipairs(pages) do
   assert(expectedText:find(normalize(page),1,true),'Different NPC text shown: '..case.id)
  end end
  local lastLine=Text.plain(case.key,context):match('([^\n]+)$')
  assert(normalize(table.concat(pages,' ')):find(normalize(lastLine),1,true),'Dialogue tail not observed')
  if case.dynamic then
   assert(pages[1]:find('TEST',1,true),'Actual player name was lost')
   assert(require('src.core.game3.bag').get(game.session.bag,1)==bagBefore+1,'Prize was not delivered')
  end
  print('LANGUAGE_DIALOGUE_EVIDENCE '..Json.encode({game='emerald',language=lang,case=case.id,
   map=case.map,fixture=case.fixture,trigger='Field.interact',key=case.key,pages=pages,completed=true}))
 end
 if lang=='pt-BR' then
  local Font=require('src.ui.game3.frlg_font')
  local own=dofile(os.getenv('GERMAN_MOD_ROOT')..'/mod/profiles/emerald_ptbr_authored.lua')
  local n=0
  for key,row in pairs(own) do
   for _,s in ipairs(row.target) do if s.t=='text' then
    assert(Font.measure(s.s)<=208,'Authored line exceeds field width: '..key..' / '..s.s)
   end end
   n=n+1
  end
  print('LANGUAGE_AUTHORED_WIDTH_OK',n)
 end
end
