-- Control/argument fixtures only; these are not localization evidence.
local root=assert(arg[1]);local C=require('src.core.gen2.CommonText');local active=true
local text={labels={sale='one'},one='{STRBUF}\n{NUM}\v{NUM}{DONE}'}
dofile(root..'/mod/gb/runtime/asian_arguments.lua')({}, {sale={2,1,3}},function()return active end)
local pages=C.of(text,'sale');local rendered=C.fill(pages,{3,'ITEM',900})
assert(rendered[1][1]=='ITEM'and rendered[1][2]=='3')
assert(rendered[2][1]=='3'and rendered[2][2]=='900','Scroll consumed an argument twice')
local direct=C.of(text,'sale',{3,'ITEM',900});assert(direct[2][2]=='900')
active=false;assert(C.fill(pages,{3,'ITEM',900})[1][1]=='3','Inactive mod still reorders')
print('ASIAN_ARGUMENTS_UNIT_OK reordered fields, scrolling, direct lookup, inactive isolation')
