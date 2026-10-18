-- Real NPC interaction after a live handoff. No test-supplied dialogue.
return function(game,capture,lang)
 local function wait(n)for _=1,n do coroutine.yield()end end
 local generation=require('src.core.GameVersion').generation();local version=require('src.core.GameVersion').get()
 if generation==3 then
  local prefix=version=='ruby' and 'RU' or version=='sapphire' and 'SA' or version=='emerald' and 'EM' or 'FR'
  assert(require('src.core.game3.map').load(nil,game,prefix..(prefix=='FR' and '_VIRIDIAN_CITY_POKEMON_CENTER_1F' or '_OLDALE_TOWN_POKEMON_CENTER_1F'),{x=7,y=4,facing='up'}))
  return assert(loadfile(os.getenv('GERMAN_MOD_ROOT')..'/tests/ptbr_nurse_live.lua'))()(game,capture,lang)
 end
 local world=generation==1 and game.overworld or game.world
 local mon=game.save.party[1];assert(mon);mon.hp=1;mon.status='PSN'
 if generation==1 then world:setMap('VIRIDIAN_POKECENTER',3,3,'up',{via='boot'})
 else world:setMap('CHERRYGROVE_POKECENTER_1F',3,3,'up',{via='boot',continue=true})end
 wait(90);if world.cancelMapNameSign then world:cancelMapNameSign()end
 local TextBox=require('src.render.TextBox');local original=TextBox.new;local heard={}
 TextBox.new=function(g,text,...)
  heard[#heard+1]=text
  print('LIVE_NURSE_DIALOGUE',lang,require('src.link.Json').encode({text=text,origin='actual NPC interaction'}))
  return original(g,text,...)
 end
 local ok,err=xpcall(function()
  world:interact();wait(90)
  assert(not game.mods.exports.german_rom_source.session:canSwitch(),'Switch allowed during real nurse dialogue')
  capture('nurse-'..lang)
  for _=1,1800 do
   game:keypressed('z');wait(1);game:keyreleased('z');wait(8)
   local top=game.stack:top()
   local idle=generation==1 and top==world or generation==2 and not top and not world:busy()
   if #heard>=4 and mon.hp>1 and (not mon.status or mon.status=='') and idle then break end
  end
  local top=game.stack:top();local ha=world.healAnim
  print('LIVE_NURSE_DIAGNOSTIC',#heard,mon.hp,tostring(mon.status),'top',tostring(top and top.isTextBox),tostring(top and top.done),'heal',tostring(ha and ha.timer),tostring(ha and ha.phase),'paused',tostring(game.mods.exports.german_rom_source.session.opened))
  assert(#heard>=3,'Nurse dialogue did not execute')
  assert(mon.hp>1 and (not mon.status or mon.status==''),'Nurse did not heal/cure')
 end,debug.traceback)
 TextBox.new=original;assert(ok,err)
 print('LIVE_NURSE_OK',version,lang,#heard)
end
