-- Edition-native field VM interactions. Setup changes only map/player position.
return function(game,capture,lang)
 local Map=require('src.core.game3.map')
 local Field=require('src.core.game3.field')
 local Message=require('src.ui.game3.message')
 local Choice=require('src.ui.game3.choice')
 local Text=require('src.core.game3.rom_text')
 local Objects=require('src.core.game3.objects')
 local Player=require('src.core.game3.player')
 local version=require('src.core.GameVersion').get()
 local prefix=version=='ruby' and 'RU_' or 'SA_'
 local function wait(n) for _=1,n do coroutine.yield() end end
 local function press(k) game:keypressed(k);wait(1);game:keyreleased(k);wait(8) end
 local function normal(s)return s:gsub('%s+',' '):match('^%s*(.-)%s*$') end
 local stem='LilycoveCity_DepartmentStore_1F_Text_'
 local cases={
  {id='saving-progress',map='OLDALE_TOWN',object=1,key='OldaleTown_Text_SavingMyProgress',pt='Quero descansar',en='I want to take a rest'},
  {id='lilycove-greeter',map='LILYCOVE_CITY_DEPARTMENT_STORE_1F',object=1,distance=2,key=stem..'WelcomeToDeptStore',pt='DEPARTAMENTOS',en='DEPARTMENT STORE'},
  {id='lilycove-directory',map='LILYCOVE_CITY_DEPARTMENT_STORE_1F',x=0,y=9,key=stem..'FloorNamesSign',pt='ATENDIMENTO',en='SERVICE COUNTER'},
  {id='lottery-decline',map='LILYCOVE_CITY_DEPARTMENT_STORE_1F',object=2,distance=2,key=stem..'LotteryCornerDrawTicket',tail=stem..'PleaseVisitAgain',choice=2,pt='BALCÃO DE LOTERIA',en='LOTTERY CORNER'},
 }
 for _,case in ipairs(cases) do
  assert(Map.load(nil,game,prefix..case.map,{x=case.x or 8,y=case.y or 7,facing='up'}));wait(45)
  if case.object then
   local object=assert(Objects.find(case.object),'NPC absent: '..case.id)
   Player.reset(object.cellX,object.cellY+(case.distance or 1),'up');Player.syncSavePosition(game)
  end
  assert(not Field.isLocked() and not Message.isOpen(),'Fixture not ready')
  Field.interact(game)
  local pages,seen,shot,choices={}, {},false,0
  for _=1,750 do
   local page=Message.currentPage()
   if page and page~='' and not seen[page] then pages[#pages+1]=page;seen[page]=true end
   if page and normal(page):find(lang=='pt-BR' and case.pt or case.en,1,true) and not shot then
    Message.skipReveal();capture(case.id);shot=true
   end
   if Choice.isOpen() then
    assert(case.choice and Choice.kind=='yesno','Unexpected menu')
    if Choice.cursor~=case.choice then press('down') end
    press('z');choices=choices+1
   elseif Message.isOpen() then press('z') else wait(10) end
   if not Field.isLocked() and not Message.isOpen() and not Choice.isOpen() then break end
  end
  assert(shot,'Expected actual NPC dialogue absent: '..case.id..' / '..table.concat(pages,' | '))
  assert(not Field.isLocked() and choices==(case.choice and 1 or 0),'NPC did not complete')
  local source=normal(Text.plain(case.key)..' '..(case.tail and Text.plain(case.tail) or ''))
  for _,page in ipairs(pages) do assert(source:find(normal(page),1,true),'Unexpected source: '..case.id) end
  local last=Text.plain(case.tail or case.key):match('([^\n]+)$')
  assert(normal(table.concat(pages,' ')):find(normal(last),1,true),'Dialogue truncated')
  print('LANGUAGE_DIALOGUE_EVIDENCE '..require('src.link.Json').encode({game=version,language=lang,case=case.id,
   map=prefix..case.map,fixture='New game; original field scripts; player positioned next to NPC/sign',
   trigger='Field.interact / keyboard',pages=pages,choices=choices,completed=true}))
 end
end
