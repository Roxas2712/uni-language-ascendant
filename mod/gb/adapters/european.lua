local Adapter={}
function Adapter.apply(mod,edition)
 local game=mod.game
 local data=game.data
 local function route(record,key,path)
  if type(record)=='table' and mod:info('assets/'..path) then record[key]=mod.path..'/assets/'..path end
 end
 for _,font in ipairs({data.font,game.fontData}) do
  route(font,'image','fonts/font.png')
  route(font,'imageBattleExtra','fonts/font_battle_extra.png')
 end
 local gfx=data.gen2MenuGfx or {}
 route(gfx.battleHud,'battleExtra','fonts/font_battle_extra.png')
 route(gfx.pack,'menu','pack/menu.png')
 route(gfx.pokedex,'tiles','pokedex/dex.png')
 route(gfx.pokegear,'tiles','pokegear/gear.png')
 route(gfx.trainerCard,'card','trainer_card/card.png')
 route(gfx.trainerCard,'cardFemale','trainer_card/card_f.png')
 route(gfx.trainerCard,'leaders','trainer_card/leaders.png')
 local title=game.titleData
 route(title,'screen',edition=='crystal' and 'title/crystal_screen.png' or 'title/title_screen.png')
 route(title,'screenGray',edition=='crystal' and 'title/crystal_screen_gray.png' or 'title/title_screen_gray.png')
 route(title,'image',edition=='crystal' and 'title/crystal_logo.png' or 'title/pokemon_logo.png')
 route(title,'wordmark','title/crystal_wordmark.png')
 return true
end
return Adapter
