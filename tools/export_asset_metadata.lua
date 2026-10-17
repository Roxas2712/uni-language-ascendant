-- Developer-only LÖVE entry point: record metadata with the shipped extractors.
-- ULA_PROFILE_SHA must be supported by the reference engine. The output is
-- address metadata only; the runtime mod and vendor files are never modified.
local root=assert(os.getenv('GERMAN_MOD_ROOT'))
local engine=assert(os.getenv('GERMAN_DEV_ENGINE'))
package.path=engine..'/?.lua;'..package.path
function love.load()
  local ok,err=xpcall(function()
    local game=assert(os.getenv('GERMAN_GAME'))
    local profile={sha1=assert(os.getenv('ULA_PROFILE_SHA'))}
    require('src.core.GameVersion').set(game)
    local real=require('src.import.gba.versions');real.select(profile.sha1)
    local f=assert(io.open(assert(os.getenv('GERMAN_ROM')),'rb'));local bytes=f:read('*a');f:close()
    assert(love.data.encode('string','hex',love.data.hash('string','sha1',bytes))==profile.sha1,'Reference ROM SHA-1 mismatch')
    local metadata={fields={},calls={},symbols={}}
    local function tracked(source,target)
      return setmetatable({}, {__index=function(_,key)
        local v=source[key]
        if type(v)~='function' then target[key]=v;return v end
        return function(a,b)
          local result=v(a,b)
          target[key]=target[key] or {}
          local k=tostring(a)..(b~=nil and '\t'..tostring(b) or '')
          target[key][k]={result}
          return result
        end
      end})
    end
    local S=real.SYMS
    if game=='emerald' then S=setmetatable({off=real.sym,size=real.size,count=real.count},{__index=S}) end
    local symbols=S and tracked(S,metadata.symbols)
    local V
    V=setmetatable({}, {__index=function(_,key)
      if key=='SYMS' then return symbols end
      if key=='forGame' then return function() return V end end
      if type(real[key])=='function' then return tracked(real,metadata.calls)[key] end
      metadata.fields[key]=real[key];return real[key]
    end})
    local function source(name)
      if not (name:match('^src.import.gba.') or name=='src.core.game3.scripting.text_ir') then return nil end
      if name:match('^src.import.gba.layouts.') or name=='src.import.gba.map_catalog' then return nil end
      local path=name:gsub('%.','/')..'.lua'
      local f=assert(io.open(root..'/mod/vendor/'..path))
      local src=f:read('*a');f:close()
      return src
    end
    local files=dofile(root..'/mod/extract.lua')(game,bytes,V,source,require,profile.sha1)
    local writer=require('src.import.LuaWriter')
    local out=assert(io.open(assert(os.getenv('ULA_ASSET_OUTPUT')),'w'))
    out:write(writer.encode(metadata));out:close()
    local count,size=0,0
    for path,data in pairs(files) do count=count+1;size=size+#data end
    print('ASSET_PROFILE_OK',game,count,size)
  end,debug.traceback)
  if not ok then print(err) end
  love.event.quit(ok and 0 or 1)
end
