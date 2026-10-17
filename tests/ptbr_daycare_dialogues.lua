-- Real Day-Care Man script: accept and reject an egg via the native YES/NO UI.
-- Fixture only supplies compatible parents, a pending egg and map position.
return function(game,capture,lang)
 local Map=require('src.core.game3.map')
 local Field=require('src.core.game3.field')
 local Message=require('src.ui.game3.message')
 local Choice=require('src.ui.game3.choice')
 local Party=require('src.core.game3.party')
 local Daycare=require('src.core.game3.daycare')
 local Breeding=require('src.core.game3.breeding')
 local Objects=require('src.core.game3.objects')
 local Player=require('src.core.game3.player')
 local Json=require('src.link.Json')
 local function wait(n) for _=1,n do coroutine.yield() end end
 local function press(key) game:keypressed(key);wait(1);game:keyreleased(key);wait(8) end
 game.session.party={}
 assert(Party.giveMon(game.session,1,20,nil,{fixedPersonality=0}))
 assert(Daycare.deposit(game.session,1))
 assert(Party.giveMon(game.session,132,20,nil,{fixedPersonality=0}))
 assert(Daycare.deposit(game.session,1))
 assert(Party.giveMon(game.session,19,10,nil,{fixedPersonality=0}))
 local dc=Daycare.stateOf(game.session)
 for _,accept in ipairs({false,true}) do
  Breeding.triggerPendingEgg(game.session,dc)
  assert(dc.eggPending)
  assert(Map.load(nil,game,'EM_ROUTE117',{x=47,y=6,facing='up'}))
  wait(90)
  local npc=assert(Objects.find(3),'Day-Care Man missing')
  Player.reset(npc.cellX,npc.cellY+1,'up');Player.syncSavePosition(game)
  local countBefore=#game.session.party
  assert(not Field.isLocked(),'Day-care fixture is locked')
  Field.interact(game)
  local pages,seen,choices={}, {},0
  local shot=false
  for i=1,1400 do
   local page=Message.currentPage()
   if page and page~='' and not seen[page] then pages[#pages+1]=page;seen[page]=true end
   if Choice.isOpen() then
    assert(Choice.kind=='yesno','Unexpected Day-Care choice')
    if not shot then Message.skipReveal();capture(accept and 'daycare-accept' or 'daycare-reject');shot=true end
    if not accept and Choice.cursor==1 then press('down') end
    press('z');choices=choices+1
   elseif Message.isOpen() then press('z')
   else wait(10) end
   if not Field.isLocked() and not Message.isOpen() and not Choice.isOpen() then break end
  end
  assert(shot and choices==(accept and 1 or 2),'Wrong Day-Care decision path')
  assert(not dc.eggPending,'Egg offer was not resolved')
  assert(#game.session.party==countBefore+(accept and 1 or 0),'Wrong party size after egg decision')
  if accept then assert(game.session.party[#game.session.party].isEgg,'Received mon is not an egg') end
  local joined=table.concat(pages,' ')
  if lang=='pt-BR' then
   assert(not joined:find('EGG',1,true) and not joined:find('want',1,true),'English Day-Care remnant')
   assert(joined:find('OVO',1,true),'Expected Portuguese egg dialogue not observed')
   assert(joined:find(accept and 'Cuide bem dele.' or 'Obrigado!',1,true),'Translated final Day-Care line was not reached')
   assert(not joined:find('Take good care',1,true),'English egg farewell')
  else assert(joined:find('EGG',1,true),'English control missing') end
  print('LANGUAGE_DAYCARE_EVIDENCE '..Json.encode({game='emerald',language=lang,
   case=accept and 'daycare-accept' or 'daycare-reject',map='EM_ROUTE117',
   fixture='Bulbasaur + Ditto deposited through Daycare.deposit; pending egg; one party member',
   trigger='Field.interact / keyboard YES-NO',pages=pages,choices=choices,completed=true}))
 end
end
