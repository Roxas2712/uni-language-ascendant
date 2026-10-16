local function wait(n) for _=1,n do coroutine.yield() end end
return function(game)
 local ok,err=xpcall(function()
  if love.setDeprecationOutput then love.setDeprecationOutput(false) end
  local V=require('src.core.GameVersion');local v=V.get();local gen=V.generation()
  local e=game.mods and game.mods.exports.german_rom_source
  local mode=os.getenv('QA_LANGUAGE')
  if mode=='de' or mode=='fr' or mode=='it' or mode=='es' then assert(e and e.status=='active' and e.language==mode,'language not active')
  elseif mode=='en' then assert(e and e.status=='english','English selection not active')
  else assert(not e,'Baseline has active language mod') end
  if e and e.startup.open then assert(e.startup.choose(e.language)) end
  local boot=love.timer.getTime()
  local world,map
  if gen==3 then
   map=(v=='firered' or v=='leafgreen') and 'FR_VIRIDIAN_CITY' or (v=='emerald' and 'EM_' or v=='ruby' and 'RU_' or 'SA_')..'OLDALE_TOWN'
   game:_handleBootAction({action='new_game',name='TEST',gender=0,start={map=map,x=gen==3 and (v=='firered' or v=='leafgreen') and 26 or 6,y=(v=='firered' or v=='leafgreen') and 27 or 17,facing='up'}})
  elseif gen==1 then
   game.stack:clear();game:startNewGame({intro=false});world=game.overworld;map='VIRIDIAN_CITY';world:setMap(map,18,20,'down',{via='boot'})
  else
   game.stack:clear();game:continueGame(require('src.core.gen2.Save').newGame({playerName='TEST',trainerId=12345}));world=game.world;map='CHERRYGROVE_CITY';world:setMap(map,18,12,'down',{continue=true})
  end
  wait(180)
  if gen==3 then require('src.ui.game3.map_name_popup').dismiss() end
  if gen==2 then world:cancelMapNameSign() end
  local u,d=game.update,game.draw
  local updates,draws={},{}
  game.update=function(self,...)
   local t=love.timer.getTime();u(self,...);updates[#updates+1]=(love.timer.getTime()-t)*1000
  end
  game.draw=function(self,...)
   local t=love.timer.getTime();d(self,...);draws[#draws+1]=(love.timer.getTime()-t)*1000
  end
  local before=collectgarbage('count')
  local started=love.timer.getTime()
  wait(tonumber(os.getenv("QA_FRAMES")) or 360)
  local elapsed=love.timer.getTime()-started
  game.update=u;game.draw=d
  local function stats(a)
   table.sort(a);local sum=0;for _,x in ipairs(a) do sum=sum+x end
   return {n=#a,meanMs=sum/#a,p50Ms=a[math.ceil(#a*.5)],p95Ms=a[math.ceil(#a*.95)],maxMs=a[#a]}
  end
  local result={game=v,language=mode,cacheHit=e and e.coverage and e.coverage.cacheHit or false,
   modLoadSeconds=e and e.loadSeconds or 0,bootToDriverSeconds=boot,
   update=stats(updates),draw=stats(draws),elapsedSeconds=elapsed,luaMemoryKiB=collectgarbage('count'),memoryBeforeKiB=before,
   graphics=love.graphics.getStats(),scene=map}
  print('PERFORMANCE_JSON '..require('src.link.Json').encode(result))
 end,debug.traceback)
 if not ok then print('PERFORMANCE_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
