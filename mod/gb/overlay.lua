return function(mod,version,prefix,files)
 local A=require('src.render.Assets')
 local Runtime=require('src.mods.Runtime')
 local V=require('src.core.GameVersion')
 local marker='mod.german_rom_source.gb'
 mod.events:on(marker,function() end)
 local bus=Runtime.events
 local function active() return Runtime.events==bus and Runtime.wants(marker) and V.get()==version end
 local imageData=love.image.newImageData
 local image=love.graphics.newImage
 local function bytes(path)
  if active() and type(path)=='string' and path:sub(1,#prefix+1)==prefix..'/' then return files[path:sub(#prefix+2)] end
 end
 for path,data in pairs(files) do
  if path:match('%.png$') then
   local value=data
   A.compose(prefix..'/'..path,function() return imageData(love.data.newByteData(value)) end)
  end
 end
 local exists=A.exists
 A.exists=function(path) return bytes(path)~=nil or exists(path) end
 love.image.newImageData=function(path,...) local b=bytes(path);return imageData(b and love.data.newByteData(b) or path,...) end
 love.graphics.newImage=function(path,...) local b=bytes(path);return image(b and imageData(love.data.newByteData(b)) or path,...) end
 -- Keep the normal resolver ahead of the localized vanilla overworld sheet.
 local resolve=A.resolve
 A.resolve=function(path)
  local resolved=resolve(path)
  if active() and path==resolved and path=='assets/generated/tilesets/overworld.png' and files['assets/tilesets/overworld.png'] then
   return prefix..'/assets/tilesets/overworld.png'
  end
  return resolved
 end
end
