-- Apply authored supplements only to the exact base text reviewed by the author.
-- Validation finishes before any registry mutation is queued.
return function(mod,entries)
 local W=require('src.import.LuaWriter')
 local function controls(ir)
  local out={}
  for _,seg in ipairs(ir) do
   if seg.t~='text' and seg.t~='nl' and seg.t~='para' and seg.t~='scroll' and seg.t~='eos' then out[#out+1]=seg end
  end
  return W.encode(out)
 end
 local originals,pending={},{}
 for key,value in mod.content.text:each() do if entries[key] then originals[key]=value end end
 for key,row in pairs(entries) do
  local source=assert(originals[key],'Authored text missing from base: '..key)
  local digest=love.data.encode('string','hex',love.data.hash('string','sha256',W.encode(source)))
  assert(digest==row.sourceSha256,'Authored text base changed: '..key)
  assert(type(row.target)=='table' and row.target[#row.target].t=='eos','Authored text lacks EOS: '..key)
  assert(controls(source)==controls(row.target),'Authored text control mismatch: '..key)
  pending[#pending+1]={key,row.target}
 end
 for _,row in ipairs(pending) do
  mod.content.text:override(row[1],row[2])
  mod.content.rom_text:override(row[1],row[2])
 end
 return #pending
end
