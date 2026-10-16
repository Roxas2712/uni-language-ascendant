return function(g)
 local ok,err=xpcall(function()
  assert(not g.mods.exports.german_rom_source,'Mod loaded while disabled')
  assert(g.data.pokemon.BULBASAUR.name=='BULBASAUR','Disabled mod changed species')
  local v=require('src.core.GameVersion').get()
  local A=require('src.render.Assets')
  assert(not A.resolve('assets/generated/tilesets/overworld.png'):find('rom%-language'),'Disabled world overlay active')
  print('GB_DISABLED_OK',v)
 end,debug.traceback)
 if not ok then print('GB_DISABLED_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
