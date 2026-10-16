-- Reconstruct each new graphic from address recipes and compare every pixel
-- with the private direct cartridge extraction, including tile flips/alpha.
local root=assert(os.getenv('ULA_ROOT'))
package.path=root..'/build/upstream-engine/?.lua;'..package.path
local J=require('src.link.Json')
local function read(path)local f=assert(io.open(path,'rb'));local b=f:read('*a');f:close();return b end
function love.load()
 local ok,err=xpcall(function()
  local count=0
  for _,pair in ipairs({{'gold','es'},{'gold','fr'},{'gold','it'},{'silver','es'},{'silver','fr'},{'crystal','es'},{'crystal','it'}}) do
   local game,lang=unpack(pair)
   local plan=J.decode(read(root..'/build/'..game..'-'..lang..'-gfx-plan.json'))
   local function own(path)return assert(loadfile(root..'/mod/'..path))()end
   local prefix='gb/profiles/'..game..'_'..lang..'/'
   local profile=own(prefix..'profile.lua')
   local result=own('gb/compile.lua')(read(plan.rom),profile,prefix,own)
   local f=assert(io.popen("find '"..plan.out.."' -maxdepth 1 -type f"))
   for path in f:lines() do
    local rel=path:match('([^/]+)$'):gsub('__','/')
    local expected=love.image.newImageData(love.data.newByteData(read(path)))
    local actual=love.image.newImageData(love.data.newByteData(assert(result.files['assets/'..rel])))
    local w,h=expected:getDimensions();local aw,ah=actual:getDimensions()
    assert(w==aw and h==ah,'dimensions mismatch '..rel)
    for y=0,h-1 do for x=0,w-1 do
     local er,eg,eb,ea=expected:getPixel(x,y);local ar,ag,ab,aa=actual:getPixel(x,y)
     assert(math.abs(ea-aa)<1/255 and (ea==0 or (math.abs(er-ar)<=1/255 and math.abs(eg-ag)<=1/255 and math.abs(eb-ab)<=1/255)),game..' '..lang..' pixel mismatch '..rel..' '..x..','..y)
    end end
    count=count+1
   end
   f:close();print('EU_GFX_ROUNDTRIP_PROFILE',game,lang,result.report.assets)
  end
  print('EU_GFX_ROUNDTRIP_OK',count)
 end,debug.traceback)
 if not ok then print('EU_GFX_ROUNDTRIP_FAILED',err)end
 love.event.quit(ok and 0 or 1)
end
