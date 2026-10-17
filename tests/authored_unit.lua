return function(root)
 local apply=dofile(root..'/mod/authored.lua')
 local W=require('src.import.LuaWriter')
 local original={{t='text',s='Before '},{t='bph',code=16},{t='eos'}}
 local target={{t='text',s='Depois '},{t='bph',code=16},{t='eos'}}
 local digest=love.data.encode('string','hex',love.data.hash('string','sha256',W.encode(original)))
 local writes={}
 local function registry(name)
  return {each=function()return pairs({symbol=original,address=original})end,
   override=function(_,key,value)writes[#writes+1]={name,key,value}end}
 end
 local mod={content={text=registry('text'),rom_text=registry('rom_text')}}
 assert(apply(mod,{symbol={sourceSha256=digest,target=target}})==1)
 assert(#writes==2 and writes[1][1]=='text' and writes[2][1]=='rom_text','Both text consumers must be updated')
 for _,bad in ipairs({
  {sourceSha256='wrong',target=target},
  {sourceSha256=digest,target={{t='text',s='Incomplete'}}},
  {sourceSha256=digest,target={{t='text',s='Lost variable'},{t='eos'}}},
 }) do
  writes={}
  assert(not pcall(apply,mod,{symbol={sourceSha256=digest,target=target},address=bad}))
  assert(#writes==0,'Invalid supplement queued partial writes')
 end
 print('AUTHORED_UNIT_OK base fingerprints, EOS, variables, dual registries, atomic validation')
end
