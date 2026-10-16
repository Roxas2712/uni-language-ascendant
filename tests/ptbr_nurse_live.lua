-- Exercise the actual field interaction and healing script, not a shown string.
return function(game,capture,lang)
 local Message=require('src.ui.game3.message')
 local Field=require('src.core.game3.field')
 local Party=require('src.core.game3.party')
 local function wait(n) for _=1,n do coroutine.yield() end end
 Message.close()
 if #game.session.party==0 then assert(Party.giveMon(game.session,1,15,nil,{fixedPersonality=0})) end
 local mon=game.session.party[1];mon.hp=1
 local seen,shot={},false
 wait(60)
 Field.interact(game)
 for i=1,1200 do
  local page=Message.currentPage()
  if type(page)=='string' and page~='' and not seen[page] then
   seen[page]=true;print('LANGUAGE_NURSE_PAGE',lang,page:gsub('\n',' | '))
  end
  if lang=='pt-BR' and page:find('saúde recuperada',1,true) and not shot then
   Message.skipReveal();capture('healing');shot=true
  elseif lang=='en' and page:find('full health',1,true) and mon.hp>1 and not shot then
   Message.skipReveal();capture('healing');shot=true
  end
  game:keypressed('z');wait(1);game:keyreleased('z');wait(10)
  if mon.hp>1 and not Field.isLocked() and not Message.isOpen() then break end
 end
 assert(mon.hp>1,'Nurse script did not heal the injured Pokémon')
 assert(shot,'Correct healing message was not reached in the actual nurse script')
 assert(not Field.isLocked(),'Nurse script did not release field control')
 print('LANGUAGE_HEALING_OK',lang,mon.hp)
end
