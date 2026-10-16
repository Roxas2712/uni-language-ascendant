return function(game)
  assert(not game.mods.exports.german_rom_source,'mod still active after disabling')
  local P=require('src.core.game3.pokemon')
  assert(P.name(1)=='BULBASAUR','English species name was not restored')
  local Text=require('src.core.game3.rom_text')
  assert(Text.plain('Text_WelcomeWantToHealPkmn'):find('Welcome',1,true),'English dialogue was not restored')
  print('GERMAN_MOD_DISABLED_OK')
  love.event.quit(0)
end
