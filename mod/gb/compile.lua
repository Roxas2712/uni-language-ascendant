return function(rom,p,root,own)
 local S=require('src.core.SaveSerializer')
 local I=require('src.import.ImageWriter')
 local R=require('src.import.Rom')
 local files,report={}, {dialogue=0,assets=0,catalogs={},language='de'}
 local function decode(r)
  if r.parts then
   local out={}
   for _,part in ipairs(r.parts) do
    if part.token then out[#out+1]=part.token elseif part.number then out[#out+1]=('%0'..part.width..'d'):format(part.number) else
     assert(part.off>=0 and part.off+part.size<=#rom,'Text span outside ROM')
     local chars={}
     for j=part.off+1,part.off+part.size do chars[#chars+1]=assert(p.charmap[tostring(rom:byte(j))]) end
     out[#out+1]=table.concat(chars)
    end
   end
   return table.concat(out)
  elseif r.empty then return ''
  elseif r.array then local out={};for i,v in ipairs(r.array) do out[i]=decode(v) end;return out
  elseif r.table then local out={};for _,v in ipairs(r.table) do out[v[1]]=decode(v[2]) end;return out
  else return r.value end
 end
 for _,cat in ipairs(p.catalogs) do
  local data=decode(own(root..cat))
  local n=0;for _ in pairs(data) do n=n+1 end
  report.catalogs[cat]=n
  if cat=='dialogue.lua' then report.dialogue=n end
  files['lang/'..cat]=S.encode(data)
 end
 files['lang/charmap.lua']=S.encode(p.fontmap)
 for _,name in ipairs({'runtime_patterns','runtime_system_patterns'}) do files['lang/'..name..'.lua']=S.encode({}) end
 local streams={}
 for path,r in pairs(own(root..'assets.lua')) do
  local raw={}
  for _,t in ipairs(r.tiles) do
   assert(t.off>=0 and t.off+t.size<=#rom,'Graphics span outside ROM')
   local data
   if t.lz then
    if not streams[t.off] then streams[t.off]=R.decompressLz3(rom:sub(t.off+1,t.off+t.size)) end
    local source=streams[t.off];data={}
    for j=t.start+1,t.start+t.length do data[#data+1]=assert(source[j]) end
   else
    local start=t.off+(t.start or 0)
    data={rom:byte(start+1,start+(t.length or t.size))}
   end
   for _,b in ipairs(data) do raw[#raw+1]=b end
  end
  local image=(r.bits==1 and I.decode1bpp or I.decode2bpp)(raw,r.width,r.height,r.transparent)
  if r.palettes then
   for index,t in ipairs(r.tiles) do
    local tx=((index-1)%(r.width/8))*8;local ty=math.floor((index-1)/(r.width/8))*8
    for y=0,7 do for x=0,7 do
     local red=image:getPixel(tx+x,ty+y);local c=t.palette[4-math.floor(red*3+0.5)]
     image:setPixel(tx+x,ty+y,c[1]/255,c[2]/255,c[3]/255,c[4]/255)
    end end
   end
  end
  if r.matte then image=I.matteColor0(image) end
  if r.ink then image:mapPixel(function(_,_,red) return 0,0,0,red<0.5 and 1 or 0 end) end
  files[path]=image:encode('png'):getString();report.assets=report.assets+1
 end
 return {files=files,report=report,operations={{registry='strings',method='override',key='__rom_language_source_gb__',value='active'}}}
end
