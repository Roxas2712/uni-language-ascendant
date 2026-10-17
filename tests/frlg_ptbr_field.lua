-- Real scripts for newly filled FRLG gaps, including genuine YES/NO branches.
return function(game,capture,lang)
 local Map=require('src.core.game3.map')
 local Field=require('src.core.game3.field')
 local Message=require('src.ui.game3.message')
 local Choice=require('src.ui.game3.choice')
 local Text=require('src.core.game3.rom_text')
 local Json=require('src.link.Json')
 local function wait(n) for _=1,n do coroutine.yield() end end
 local function press(key) game:keypressed(key);wait(1);game:keyreleased(key);wait(8) end
 local function normal(s)return s:gsub('%s+',' '):match('^%s*(.-)%s*$') end
 local leaf=require('src.core.GameVersion').get()=='leafgreen'
 local cases={
  {id='celadon-reception',map='FR_CELADON_CITY_DEPARTMENT_STORE_1F',x=6,y=12,
   key=leaf and 'g3:081954b9' or 'g3:081954dd',pt='LOJA DE DEPARTAMENTOS',en='CELADON DEPT. STORE'},
  {id='celadon-floor-directory',map='FR_CELADON_CITY_DEPARTMENT_STORE_1F',x=9,y=12,
   key=leaf and 'g3:08195513' or 'g3:08195537',pt='ANDAR 1',en='1F: SERVICE COUNTER'},
  {id='trade-decline',map='FR_UNDERGROUND_PATH_NORTH_ENTRANCE',x=5,y=7,
   pt='Quer trocar pelo meu',en='Want to trade it for my',choice=2,tail='Trade_Text_ThatsTooBad'},
  {id='daycare-one-mon',map='FR_FOUR_ISLAND_POKEMON_DAY_CARE',x=2,y=3,
   pt='Mas você só tem um',en='But you have just one',choice=1,tail='DayCare_Text_YouHaveJustOneMon'},
 }
 for _,case in ipairs(cases) do
  assert(Map.load(nil,game,case.map,{x=case.x,y=case.y,facing='up'}));wait(45)
  assert(not Field.isLocked() and not Message.isOpen(),'Fixture not ready '..case.id)
  local before=#game.session.party
  Field.interact(game)
  local seen,pages,shot,choices={}, {},false,0
  for _=1,750 do
   local page=Message.currentPage()
   if page and page~='' and not seen[page] then pages[#pages+1]=page;seen[page]=true end
   if page and normal(page):find(lang=='pt-BR' and case.pt or case.en,1,true) and not shot then
    Message.skipReveal();capture(case.id);shot=true
   end
   if Choice.isOpen() then
    assert(case.choice and Choice.kind=='yesno','Unexpected choice '..case.id)
    if Choice.cursor~=case.choice then press('down') end
    press('z');choices=choices+1
   elseif Message.isOpen() then press('z')
   else wait(10) end
   if not Field.isLocked() and not Message.isOpen() and not Choice.isOpen() then break end
  end
  assert(shot,'Actual expected dialogue not seen '..case.id..': '..table.concat(pages,' | '))
  assert(not Field.isLocked(),'Field remained locked '..case.id)
  assert(#game.session.party==before,'Unexpected party mutation '..case.id)
  assert(choices==(case.choice and 1 or 0),'Wrong choice count '..case.id)
  if case.key then
   local full=normal(Text.plain(case.key))
   for _,page in ipairs(pages) do assert(full:find(normal(page),1,true),'Different script text '..case.id) end
  end
  local key=case.tail or case.key
  local last=assert(Text.plain(key):match('([^\n]+)$'))
  assert(normal(table.concat(pages,' ')):find(normal(last),1,true),'Missing dialogue ending '..case.id)
  print('LANGUAGE_DIALOGUE_EVIDENCE '..Json.encode({game=require('src.core.GameVersion').get(),language=lang,
   case=case.id,map=case.map,fixture='New game; one healthy party member; no prior trades or daycare deposits',
   trigger='Field.interact / keyboard YES-NO',pages=pages,choices=choices,completed=true}))
 end
end
