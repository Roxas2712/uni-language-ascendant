local function wait(n) for _=1,n do coroutine.yield() end end
return function(game)
 local ok,err=xpcall(function()
  if love.setDeprecationOutput then love.setDeprecationOutput(false) end
  local V=require('src.core.GameVersion');local v=V.get();local gen=V.generation()
  local lang=os.getenv('LANGUAGE_SHOT')
  if lang=='de' then assert(game.mods.exports.german_rom_source.status=='active') end
  local function capture(name)
   wait(120)
   if gen==2 and game.world then game.world:cancelMapNameSign() end
   game.capturePath=os.getenv('SHOT_DIR')..'/'..v..'-'..name..'-'..lang..'.png'
   for _=1,600 do if not game.capturePath then break end;wait(1) end
   wait(5);print('GB_CAPTURE_OK',v,name,lang)
  end
  -- Invoke the normal title renderer directly to compare the same phase.
  game.stack:clear()
  if gen==1 then
   local title=require('src.ui.TitleState').new(game,{})
   game.stack:push(title)
   for _=1,500 do title:update(1/60) end
  else game:showTitle() end
  capture('title')
  local world,map
  if gen==1 then game:startNewGame({intro=false});world=game.overworld;map='VIRIDIAN_CITY'
  else
   game:continueGame(require('src.core.gen2.Save').newGame({playerName='TEST',trainerId=12345}))
   world=game.world;map='CHERRYGROVE_CITY'
  end
  local def=(gen==1 and game.data.maps or game.data.gen2Maps)[map]
  for _,kind in ipairs({'center','mart'}) do
   local warp
   for _,w in ipairs(def.warps) do
    if (kind=='center' and w.destMap:find('POKECENTER')) or (kind=='mart' and w.destMap:find('MART')) then warp=w;break end
   end
   assert(warp,'Missing '..kind..' warp')
   world:setMap(map,warp.x,warp.y+1,'up',{via='boot',continue=true})
   capture(kind)
  end
  -- Exercise a real map sign through the normal interaction path.
  if gen==1 then
   local sign=def.signs and def.signs[1]
   if sign then world:setMap(map,sign.x,sign.y+1,'up',{via='boot'});wait(30);world:showMapText(sign.text);capture('dialogue') end
  else
   local sign=def.bgEvents[1]
   world:setMap(map,sign.x,sign.y+1,'up',{continue=true});wait(30);world:interact();capture('dialogue')
  end
  print('GB_COMPARISON_OK',v,lang)
 end,debug.traceback)
 if not ok then print('GB_COMPARISON_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
