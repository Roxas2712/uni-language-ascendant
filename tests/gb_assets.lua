return function(game)
 local ok,err=xpcall(function()
  local v=require('src.core.GameVersion').get()
  local e=assert(game.mods.exports.german_rom_source)
  local matched=0
  for name,bytes in pairs(e.assets) do
   if name:match('%.png$') then
    local path=assert(os.getenv('ULA_GB_REFERENCE'),'Set ULA_GB_REFERENCE to the private reference directory')..'/editions/'..v..'/'..name
    local f=io.open(path,'rb')
    if not f and v=='crystal' then f=io.open(path:gsub('/crystal/','/silver/'),'rb') end
    if v=='yellow' and (name=='assets/title/pokemon_logo.png' or name=='assets/title/pika_bubble.png') then
     if f then f:close() end
     f=assert(io.open(os.getenv('GERMAN_MOD_ROOT')..(name:find('pika_bubble') and '/build/yellow-raw-bubble.png' or '/build/yellow-raw-logo.png'),'rb'))
    end
    if f then
     local ref=f:read('*a');f:close()
     local a=love.image.newImageData(love.data.newByteData(bytes))
     local b=love.image.newImageData(love.data.newByteData(ref))
     assert(a:getWidth()==b:getWidth() and a:getHeight()==b:getHeight(),name..' dimensions')
     for y=0,a:getHeight()-1 do for x=0,a:getWidth()-1 do
      local ar,ag,ab,aa=a:getPixel(x,y);local br,bg,bb,ba=b:getPixel(x,y)
      assert(math.abs(aa-ba)<0.01 and (aa==0 or (math.abs(ar-br)<0.01 and math.abs(ag-bg)<0.01 and math.abs(ab-bb)<0.01)),name..' pixels '..x..','..y)
     end end
     matched=matched+1
    end
   end
  end
  print('GB_ASSETS_OK',v,matched,e.coverage.cacheHit and 'warm' or 'cold')
 end,debug.traceback)
 if not ok then print('GB_ASSETS_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
