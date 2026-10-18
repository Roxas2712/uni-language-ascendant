-- Runtime decoder checks. These binary fixtures are not dialogue evidence.
local root=assert(arg[1]);local compile=dofile(root..'/mod/gb/compile.lua')
local S=require('src.core.SaveSerializer')
local p={language='ko',encoding='korean-gen2',charmap={['1:80']='가',['1:94']='나',['89']='\n'},fontmap={},catalogs={'sample.lua'}}
local source=string.char(1,80,89,1,94)
local function own(path)
 if path=='assets.lua'then return {}end
 return {table={{'value',{parts={{off=0,size=5},{token='{DONE}'}}}},{'formatted',{format={parts={{token='\n'},{off=0,size=5},{token='{PROMPT}'}}}}}}}
end
local result=compile(source,p,'',own)
local cat=assert(S.decode(result.files['lang/sample.lua']))
assert(cat.value=='가\n나{DONE}' and cat.formatted=='가\n나')
assert(not pcall(compile,source:sub(1,4),p,'',own),'Truncation must fail')
p.charmap['1:94']=nil
assert(not pcall(compile,source,p,'',own),'Missing Korean glyph must fail')
p.encoding=nil;p.charmap={['1']='A',['80']='B',['89']='C',['94']='D'}
cat=assert(S.decode(compile(source,p,'',own).files['lang/sample.lua']))
assert(cat.value=='ABCAD{DONE}','Single-byte profile behavior changed')
local function templateOwn(path)
 if path=='assets.lua'then return {}end
 return {table={{'line',{format={parts={{token='{TARGET}'},{token=' / '},{token='{USER}'},{token='{PROMPT}'}}},parameters={TARGET='%2$s',USER='%1$s'}}}}}
end
cat=assert(S.decode(compile('',p,'',templateOwn).files['lang/sample.lua']))
assert(cat.line=='%2$s / %1$s','Native role reordering lost argument identity')
print('ASIAN_COMPILE_UNIT_OK multibyte boundaries, format controls, truncation, glyph failure, single-byte regression')

local function mapOwn(recipe)
 return function(path)if path=='assets.lua'then return {}end;return {table={{'map',{tilemap=recipe}}}}end
end
local function mapDecode(bytes,recipe)return assert(S.decode(compile(bytes,p,'',mapOwn(recipe)).files['lang/sample.lua'])).map end
local recipe={off=0,size=5,cells=6,rle=true,fill=79}
local cells=mapDecode(string.char(2,3,7,1,255),recipe)
assert(#cells==6 and cells[1]==2 and cells[3]==2 and cells[4]==7 and cells[5]==79)
assert(not pcall(mapDecode,string.char(2,7,7,1,255),recipe),'Overflowing RLE accepted')
assert(not pcall(mapDecode,string.char(2,0,7,1,255),recipe),'Zero RLE accepted')
assert(not pcall(mapDecode,string.char(2,3,7,1,0),recipe),'Unterminated RLE accepted')
assert(not pcall(mapDecode,string.char(255,3,7,1,255),recipe),'Trailing bytes accepted')
assert(not pcall(mapDecode,string.char(2,255),{off=0,size=2,cells=360,rle=true,fill=79}),'Run length 255 confused with terminator')
recipe.rle=false;cells=mapDecode(string.char(2,3,7,1,255),recipe)
assert(#cells==6 and cells[1]==2 and cells[2]==3 and cells[4]==1 and cells[5]==79)
print('ASIAN_TILEMAP_UNIT_OK native RLE/flat, fill, bounds and termination')
