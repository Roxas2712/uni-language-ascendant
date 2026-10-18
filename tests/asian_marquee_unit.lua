local root=assert(arg[1]);local active=true
package.loaded['src.render.Font']={split=function(text)
 local out={};local i=1
 while i<=#text do
  local from=i
  if text:sub(i,i+3)=='<PK>'then i=i+4
  else i=i+1;while i<=#text and text:byte(i)>=128 and text:byte(i)<192 do i=i+1 end end
  out[#out+1]={from=from,to=i-1}
 end
 return out
end}
local M=require('src.ui.Marquee');local original=M.clip
dofile(root..'/mod/gb/runtime/asian_marquee.lua')(function()return active end)
for _,s in ipairs({'あいうえお','가나다라마','<PK>ABCD'})do
 local spans=package.loaded['src.render.Font'].split(s)
 assert(M.clip(s,2)==s:sub(1,spans[2].to))
 assert(M.at(s,2,0)==M.clip(s,2))
 assert(M.at(s,2,1.25)==s:sub(spans[2].from,spans[3].to))
 assert(M.at(s,2,2)==s:sub(spans[4].from))
 assert(M.clip(s,0)=='')
end
assert(M.at('あ',2,5)=='あ'and M.clip(nil,2)=='')
active=false;assert(M.clip('あいう',2)==original('あいう',2))
print('ASIAN_MARQUEE_UNIT_OK kana, Hangul, macros, scrolling, inactive isolation')
