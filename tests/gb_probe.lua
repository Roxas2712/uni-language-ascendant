return function(g)
 local A=require('src.render.Assets');local e=g.mods.exports.german_rom_source
 for k,t in pairs(g.data.tilesets or {}) do if type(t)=='table' and t.id=='OVERWORLD' then print('SHEET',k,t.image,A.resolve(t.image),A.isComposed(A.resolve(t.image))) end end
 local b=e.assets['assets/tilesets/overworld.png'];if b then local f=io.open(os.getenv('GERMAN_MOD_ROOT')..'/build/red-world-de.png','wb');f:write(b);f:close() end
 love.event.quit()
end
