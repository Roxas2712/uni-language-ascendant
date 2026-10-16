local function wait(n) for _=1,n do coroutine.yield() end end
return function(game)
 local ok,err=xpcall(function()
  if love.setDeprecationOutput then love.setDeprecationOutput(false) end
  local version=require('src.core.GameVersion').get()
  local lang=os.getenv('LANGUAGE_SHOT')
  if lang=='de' then assert(game.mods.exports.german_rom_source.status=='active') end
  local map=(version=='leafgreen' or version=='firered') and 'FR_VIRIDIAN_CITY' or (version=='ruby' and 'RU_OLDALE_TOWN' or version=='sapphire' and 'SA_OLDALE_TOWN' or 'EM_OLDALE_TOWN')
  local shots=(version=='leafgreen' or version=='firered') and {{'center',26,27},{'mart',36,20},{'gym',36,11}} or {{'center',6,17},{'mart',14,7}}
  game:_handleBootAction({action='new_game',name='TEST',gender=0,start={map=map,x=shots[1][2],y=shots[1][3],facing='up'}})
  local Map=require('src.core.game3.map')
  local function capture(name)
   wait(180)
   require('src.ui.game3.map_name_popup').dismiss()
   game.capturePath=os.getenv('SHOT_DIR')..'/'..version..'-'..name..'-'..lang..'.png'
   for _=1,600 do if not game.capturePath then break end;wait(1) end
   wait(8);print('CAPTURE_OK',version,name,lang)
  end
  for _,shot in ipairs(shots) do
   assert(Map.load(nil,game,map,{x=shot[2],y=shot[3],facing='up'}))
   capture(shot[1])
  end
  require('src.core.game3.rng').SeedRng(12345)
  assert(require('src.core.game3.party').giveMon(game.session,1,15,nil,{fixedPersonality=0}))
  require('src.ui.game3.summary_menu').openMenu(game.session.party,1,{session=game.session,page=1})
  capture('summary')
  print('COMPARISON_OK',version,lang)
 end,debug.traceback)
 if not ok then print('COMPARISON_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
