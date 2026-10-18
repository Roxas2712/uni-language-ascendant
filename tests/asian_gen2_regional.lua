-- Real US-only map branches with explicitly authored Japanese compatibility.
-- No dialogue is injected: original map scripts select every displayed line.
return function(game,qa)
 assert(qa.lang=='ja'and qa.version=='crystal')
 local wait,press,capture=qa.wait,qa.press,qa.capture
 local Box=require('src.render.TextBox');local Json=require('src.link.Json');local Bag=require('src.inventory.Bag')
 local original=Box.new;local heard={};local world=game.world
 Box.new=function(g,text,...)
  heard[text]=true;print('ASIAN_REGIONAL_DIALOGUE',Json.encode({text=text,origin='authored compatibility; real US map script'}))
  return original(g,text,...)
 end
 local function expect(keys)
  for _,key in ipairs(keys)do assert(heard[qa.expected[key]],'Regional branch absent: '..key)end
 end
 local function count(id)local n=0;for _,r in ipairs(Bag.rows(game.save,game.data))do if r.id==id then n=n+r.count end end;return n end
 local before=#game.save.party
 world:setMap('DAY_CARE',2,4,'up',{via='boot',continue=true});wait(60);world:interact();wait(90);capture('odd-egg-offer')
 local shot=false
 for _=1,350 do
  if heard[qa.expected['18:71c3']]and not shot then wait(90);capture('odd-egg-description');shot=true end
  if shot and not world.script then break end
  press('z',4)
 end
 expect({'18:70ce','18:71ae','18:71c3'})
 assert(#game.save.party==before+1,'Odd Egg party insertion failed')
 assert(game.save.party[#game.save.party].isEgg or game.save.party[#game.save.party].egg,'Gift is not an egg')
 print('ASIAN_REAL_ODD_EGG_OK')
 for _=1,30 do press('z',3)end
 assert(Bag.add(game.save,'EON_MAIL',1,game.data));local mail=count('EON_MAIL');local revive=count('REVIVE')
 world:setMap('GOLDENROD_POKECENTER_1F',7,6,'up',{via='boot',continue=true});wait(60);world:interact();wait(90);capture('eon-mail-request')
 shot=false
 for _=1,350 do
  if heard[qa.expected['18:64e9']]and not shot then wait(90);capture('eon-mail-thanks');shot=true end
  if shot then break end
  press('z',4)
 end
 expect({'18:63fb','18:648c','18:6549','18:64a4','18:64e9'})
 assert(count('EON_MAIL')==mail-1 and count('REVIVE')==revive+1,'Eon Mail exchange state changed')
 Box.new=original
 print('ASIAN_REAL_EON_MAIL_OK')
end
