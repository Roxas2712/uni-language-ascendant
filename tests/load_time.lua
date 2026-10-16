return function(game)
 local e=assert(game.mods and game.mods.exports.german_rom_source)
 assert(e.status=='active',e.status)
 print('LOAD_TIME_JSON '..require('src.link.Json').encode({game=require('src.core.GameVersion').get(),seconds=e.loadSeconds,cacheHit=e.coverage.cacheHit,cacheKey=e.cacheKey}))
 love.event.quit()
end
