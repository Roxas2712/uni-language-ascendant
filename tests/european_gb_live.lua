local function wait(n) for _=1,n do coroutine.yield() end end
return function(game)
 local ok,err=xpcall(function()
  if love.setDeprecationOutput then love.setDeprecationOutput(false) end
  local V=require('src.core.GameVersion');local v=V.get();local gen=V.generation()
  local lang=os.getenv('LANGUAGE_SHOT')
  local e=assert(game.mods.exports.german_rom_source,'Language mod not loaded')
  assert(e.status=='active' and e.language==lang,'Language profile is not active')
  assert(e.coverage.dialogue>2500,'Insufficient dialogue coverage')
  local expected=lang=='fr' and 'BULBIZARRE' or 'BULBASAUR'
  assert(game.data.pokemon.BULBASAUR.name==expected,game.data.pokemon.BULBASAUR.name)
  local baseRoot=love.filesystem.getSaveDirectory()..'/'..v..'/data/generated/'
  local function same(a,b)
   if type(a)~=type(b) then return false end
   if type(a)~='table' then return a==b end
   for k,x in pairs(a) do if not same(x,b[k]) then return false end end
   for k in pairs(b) do if a[k]==nil then return false end end
   return true
  end
  local base=assert(loadfile(baseRoot..'pokemon.lua'))()
  for id,row in pairs(base) do if type(row)=='table' and row.id then
   for _,field in ipairs({'baseStats','types','catchRate','baseExp','growthRate','learnset','evolutions','tmhm','eggMoves'}) do
    assert(same(row[field],game.data.pokemon[id][field]),'Mechanical species field changed: '..id..'.'..field)
   end
  end end
  base=assert(loadfile(baseRoot..'moves.lua'))()
  for id,row in pairs(base) do if type(row)=='table' and row.id then
   for _,field in ipairs({'power','accuracy','pp','effect','type','effectChance'}) do
    assert(same(row[field],game.data.moves[id][field]),'Mechanical move field changed: '..id..'.'..field)
   end
  end end
  print('EUROPEAN_PROFILE' ,v,lang,e.coverage.dialogue,e.coverage.assets)
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
  if gen==2 then
   local baseline=assert(loadfile(baseRoot..'pokedex.lua'))().entries.BULBASAUR
   local dex=game.data.gen2Pokedex.entries.BULBASAUR
   assert(dex.weight==baseline.weight and dex.height==baseline.height,'Mechanical Pokedex words changed')
   assert(dex.heightM==0.7 and dex.weightKg==6.9,'Incorrect metric source measurements')
   assert(dex.text:find('<NEXT>',1,true),'Pokedex line markers missing')
   game.save.pokedex.seen.BULBASAUR=true;game.save.pokedex.caught.BULBASAUR=true
   local screen=require('src.ui.gen2.PokedexMenu').new(game,{entrySpecies='BULBASAUR'})
   game.stack:clear();game.stack:push(screen);capture('pokedex')
  end
  print('EUROPEAN_GB_LIVE_OK' ,v,lang)
 end,debug.traceback)
 if not ok then print('EUROPEAN_GB_LIVE_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
