-- Original port-credit state machine, accelerated only between rendered frames.
return function(game,qa)
 local Credits=require('src.ui.gen2.Credits');local Font=require('src.render.Font');local Json=require('src.link.Json')
 local state=Credits.new(game,{allowSkip=true});game.stack:clear();game.stack:push(state)
 local seen,shots={},{}
 for _=1,1200 do
  for _,entry in ipairs(state.shown or {})do
   if entry.text then
    local localized=Font.__ulaEuropeanStrings.localize(entry.text)
    seen[entry.text]=localized
    if not shots.staff and localized:find(qa.lang=='ja'and 'スタッフ'or '스태프',1,true)then qa.capture('credits-staff');shots.staff=true end
    if not shots.role and localized:find(qa.lang=='ja'and 'ディレクター'or '감독',1,true)then qa.capture('credits-role');shots.role=true end
   elseif entry.theEnd and not shots.ending then qa.capture('credits-ending');shots.ending=true end
  end
  if shots.ending then break end
  -- Run genuine credits ticks, without replacing the script or shown text.
  for _=1,12 do state:update(1/60)end
  qa.wait(1)
 end
 for _,kind in ipairs({'staff','role','ending'})do assert(shots[kind],'Credit scene not reached: '..kind)end
 for source,value in pairs(seen)do print('ASIAN_REAL_CREDITS_LINE',Json.encode({source=source,text=value}))end
 print('ASIAN_REAL_CREDITS_OK',qa.version)
end
