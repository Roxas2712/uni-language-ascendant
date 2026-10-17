-- Layout mechanics only; no synthetic text is used as gameplay evidence.
local root=assert(arg[1]);local reflow=dofile(root..'/mod/ptbr_text_layout.lua')
local function chars(s)local t={};for c in s:gmatch('.')do t[#t+1]={t='c',s=c}end;return t end
local src=chars('one two three four five')
src[#src+1]={t='para'}
for _,t in ipairs(chars('six '))do src[#src+1]=t end
local pause={t='pause',n=12};src[#src+1]=pause
for _,t in ipairs(chars('seven'))do src[#src+1]=t end
local out=reflow(src,9,string.len)
local text,line,lines={},'',1;local found=false
for _,t in ipairs(out)do
 if t.t=='c' then line=line..t.s;text[#text+1]=t.s;assert(#line<=9)
 elseif t.t=='nl' then assert(lines==1);lines=2;line='';text[#text+1]=' '
 elseif t.t=='scroll' then lines=2;line='';text[#text+1]=' '
 elseif t.t=='para' then lines=1;line='';text[#text+1]=' '
 elseif t.t=='pause' then assert(t==pause and t.n==12);found=true end
end
assert(found and table.concat(text)=='one two three four five six seven')
assert(src[4].s==' ','Input tokens mutated')
local wide=reflow(chars('abcdefghijkl'),4,string.len);local breaks=0
for _,t in ipairs(wide)do if t.t~='c' then breaks=breaks+1 end end
assert(breaks==2,'Long word was clipped instead of wrapped')
print('TEXT_LAYOUT_UNIT_OK width, scrolling, source text, timing controls, immutable input')
