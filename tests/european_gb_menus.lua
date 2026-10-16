local function wait(n)for _=1,n do coroutine.yield()end end
return function(game)
 local ok,err=xpcall(function()
  if love.setDeprecationOutput then love.setDeprecationOutput(false)end
  local V=require('src.core.GameVersion');local version,gen=V.get(),V.generation()
  local lang=assert(os.getenv('LANGUAGE_SHOT'))
  local exports=assert(game.mods.exports.german_rom_source)
  assert(exports.status=='active' and exports.language==lang,'Wrong active language')
  assert(exports.coverage.catalogs['strings.lua']>=856,'UI catalog incomplete')
  if gen==2 then assert(exports.coverage.assets>=69,'Missing UI/world graphics')end
  local sources=require('src.link.Json').decode(assert(io.open(os.getenv('GERMAN_MOD_ROOT')..'/translations/european/gb-ui.json')):read('*a'))
  for key in pairs(sources)do assert(game.data.strings[key] and game.data.strings[key]~='',key)end
  local grass=({es='PLANTA',fr='PLANTE',it='ERBA'})[lang]
  assert(require('src.battle.TypeChart').displayName('GRASS',game.data)==grass,'Untranslated type name')
  local rendered=exports.localizeUi('BOX 7 is full!')
  assert(rendered~= 'BOX 7 is full!' and rendered:find('7',1,true),'Formatted UI fallback failed')
  local function capture(name)
   wait(40)
   game.capturePath=os.getenv('SHOT_DIR')..'/'..version..'-menus-'..name..'-'..lang..'.png'
   for _=1,300 do if not game.capturePath then break end;wait(1)end
   assert(not game.capturePath,'Screenshot timeout');print('EU_MENU_CAPTURE',version,lang,name)
  end
  game.stack:clear()
  if gen==1 then
   local title=require('src.ui.TitleState').new(game,{})
   game.stack:push(title);for _=1,500 do title:update(1/60)end
  else game:showTitle()end
  capture('title')
  if gen==1 then game:startNewGame({intro=false})
  else game:continueGame(require('src.core.gen2.Save').newGame({playerName='TEST',trainerId=12345}))end
  local world=gen==1 and game.overworld or game.world
  local map=gen==1 and 'VIRIDIAN_CITY' or 'CHERRYGROVE_CITY'
  local defs=gen==1 and game.data.maps or game.data.gen2Maps
  local def=defs[map]
  for _,w in ipairs(def.warps)do if w.destMap:find('MART')then world:setMap(map,w.x,w.y+1,'up',{continue=true,via='boot'});break end end
  capture('world')
  local prefix=gen==1 and 'src.ui.' or 'src.ui.gen2.'
  local function show(module,name,opts)
   game.stack:clear();local state=require(module).new(game,opts);game.stack:push(state);capture(name);return state
  end
  game.save.flags=game.save.flags or {};game.save.flags.EVENT_GOT_POKEDEX=true
  if gen==2 then
   game.save.engineFlags=game.save.engineFlags or {};game.save.engineFlags.ENGINE_POKEDEX=true
   game.save.pokegearFlags={map=true,phone=true,radio=true}
   for id,row in pairs(assert(game.data.gen2Landmarks.landmarks))do
    if type(row)=='table' and row.name then
     assert(not row.name:find('<TTE>',1,true),'Invalid landmark break '..id)
     for line in row.name:gmatch('[^\n]+')do
      local n=0
      for _ in line:gmatch('[%z\1-\127\194-\244][\128-\191]*')do n=n+1 end
      assert(n<=11,'Landmark overflow '..id)
     end
    end
   end
   game.save.party={require('src.battle.gen2.Mon').new(game.data,'BULBASAUR',15)}
  else game.save.party={require('src.pokemon.Pokemon').new(game.data,'BULBASAUR',15)}end
  show(prefix..'StartMenu','start',{unlocked={pokedex=true,pokemon=true,pack=true,pokegear=true,player=true,save=true,option=true}})
  show('src.ui.OptionsMenu','options')
  show(prefix..'PartyMenu','party',{party=game.save.party})
  local naming=show(prefix..'NamingScreen','naming',{type='box',isBox=gen==2,title=game.data.strings['YOUR NAME?']})
  if gen==1 then
   assert(#naming:grid()==6 and naming:grid()[5][9]=='ED','Naming controls lost')
   naming.lower=true;capture('naming-lower')
  end
  if gen==2 then
   assert(#naming:rows()==5,'Wrong keyboard geometry');naming.lower=true;capture('naming-lower')
   local playerNaming=show(prefix..'NamingScreen','naming-player',{type='player'})
   assert(#playerNaming:rows()==4 and #playerNaming:rows()[4]==9,'Player naming geometry')
   local Pack=require(prefix..'PackMenu')
   for _,pocket in ipairs({'ITEM','BALL','KEY_ITEM','TM_HM'})do show(prefix..'PackMenu','pack-'..pocket:lower(),{pocket=pocket})end
   local card=show(prefix..'TrainerCard','trainer')
   card.page=2;capture('badges')
   game.stack:clear();local gear=require(prefix..'Pokegear').new(game);game.stack:push(gear)
   for i,entry in ipairs(gear.cards)do gear.cardIndex=i;capture('gear-'..entry.id)end
   show(prefix..'BoxMenu','pc',{mode='withdraw'})
   for page=1,3 do show(prefix..'SummaryMenu','summary-'..page,{mon=game.save.party[1],page=page})end
   local base=assert(loadfile(love.filesystem.getSaveDirectory()..'/'..version..'/data/generated/tilesets.lua'))()
   for key,value in pairs(base)do if type(value)=='table' and value.collision then
    local active=game.data.gen2Tilesets[key];assert(#value.collision<=#active.collision,key..' collision sizes '..#value.collision..'/'..#active.collision)
    for i,row in ipairs(value.collision)do for j,v in ipairs(row)do assert(v==active.collision[i][j],'Collision changed '..key)end end
   end end
  else
   show('src.ui.BagMenu','bag')
   show('src.ui.PlayerPC','pc')
  end
  print('EUROPEAN_MENU_LIVE_OK',version,lang,'complete UI keys, formatted fields, atlas routing, unchanged collisions')
 end,debug.traceback)
 if not ok then print('EUROPEAN_MENU_LIVE_FAILED',err)end
 love.event.quit(ok and 0 or 1)
end
