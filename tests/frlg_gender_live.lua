-- Real post-battle NPC script, with the battle-completed flag as a fixture.
return function(game)
 local function wait(n)for _=1,n do coroutine.yield() end end
 local ok,err=xpcall(function()
  local version=require('src.core.GameVersion').get()
  assert(version=='firered' or version=='leafgreen')
  assert(game.mods.exports.german_rom_source.language=='pt-BR')
  if love.setDeprecationOutput then love.setDeprecationOutput(false) end
  local Map=require('src.core.game3.map');local Field=require('src.core.game3.field')
  local Message=require('src.ui.game3.message');local Space=require('src.core.game3.scripting.space')
  local Flags=require('src.core.game3.scripting.flags')
  for gender=0,1 do
   game:_handleBootAction({action='new_game',name='TEST',gender=gender,start={map='FR_VIRIDIAN_CITY',x=26,y=28,facing='up'}})
   wait(90)
   assert(require('src.core.game3.party').giveMon(game.session,1,15,nil,{fixedPersonality=0}))
   local trainer=require('src.core.game3.constants').active(game.session):require('trainers','TRAINER_PKMN_BREEDER_ALIZE')
   Flags.setTrainerDefeated(Space.vm.store,game.session,trainer,true)
   assert(Map.load(nil,game,'FR_FIVE_ISLAND_WATER_LABYRINTH',{x=9,y=8,facing='up'}));wait(60)
   local npc=assert(require('src.core.game3.objects').find(2))
   require('src.core.game3.player').reset(npc.cellX,npc.cellY+1,'up')
   require('src.core.game3.player').syncSavePosition(game)
   Field.interact(game)
   local expected=gender==0 and 'um bom CRIADOR.' or 'uma boa CRIADORA.'
   local pages,seen,shot={},{},false
   for _=1,450 do
    local page=Message.currentPage()
    if page and page~='' and not seen[page] then pages[#pages+1]=page;seen[page]=true end
    if page and page:gsub('%s+',' '):find(gender==0 and 'CRIADOR' or 'CRIADORA',1,true) and not shot then
     Message.skipReveal();wait(20)
     game.capturePath=os.getenv('SHOT_DIR')..'/'..version..'-pt-BR-gender-'..gender..'.png'
     for _=1,600 do if not game.capturePath then break end;wait(1) end
     assert(not game.capturePath);shot=true
    end
    game:keypressed('z');wait(1);game:keyreleased('z');wait(10)
    if not Field.isLocked() and not Message.isOpen() then break end
   end
   assert(shot and not Field.isLocked(),'NPC did not complete: '..table.concat(pages,' | '))
   local joined=table.concat(pages,' '):gsub('%s+',' ')
   assert(joined:find(expected,1,true),'Wrong gender agreement: '..joined)
   print('LANGUAGE_GENDER_EVIDENCE '..require('src.link.Json').encode({game=version,gender=gender,pages=pages,
    fixture='Fresh save with selected gender; Alize defeated flag; actual post-battle Field.interact; no battle-completion claim',completed=true}))
  end
  print('LANGUAGE_GENDER_OK',version)
 end,debug.traceback)
 if not ok then print('LANGUAGE_GENDER_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
