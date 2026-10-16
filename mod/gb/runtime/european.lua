-- Language-neutral registry adapter for compiled retail EU catalogs.
return function(mod)
 local function catalog(name)
  local body=mod:read('lang/'..name..'.lua')
  return body and assert(loadstring(body,'@european/'..name))() or {}
 end
 local generation=require('src.core.GameVersion').generation()
 local data=assert(mod.game.data)
 for seq,code in pairs(catalog('charmap')) do mod.content.font:register('charmap:ula-european:'..seq,{seq=seq,code=code}) end
 mod.content.font:override('main',{image=mod.path..'/assets/fonts/font.png',base=0x80,glyphsPerRow=16})
 if generation==1 then
  mod.content.font:register('font_battle_extra',{image=mod.path..'/assets/battle/font_battle_extra.png',base=0x62,glyphsPerRow=15})
 end
 for key,value in pairs(catalog('dialogue')) do mod.content.text:override(key,value) end
 if generation==2 then for key,value in pairs(catalog('rom_text')) do mod.content.rom_text:override(key,value) end end
 local strings=catalog('strings')
 local patterns={}
 local function escaped(value)return (value:gsub('([%^%$%(%)%%%.%[%]%*%+%-%?])','%%%1'))end
 local token='%%[-+ #0-9%.]*[a-zA-Z]'
 for source,target in pairs(strings) do
  if source:find('%%') and not source:find('%%%%') then
   local pieces,at,fields={},1,0
   while true do
    local first,last=source:find(token,at)
    if not first then pieces[#pieces+1]=escaped(source:sub(at));break end
    pieces[#pieces+1]=escaped(source:sub(at,first-1))
    pieces[#pieces+1]=source:sub(last,last)=='s' and '(.-)' or '([%s%+%-]*%d+%.?%d*)'
    fields=fields+1;at=last+1
   end
   local letters=source:gsub(token,''):gsub('[^A-Za-z]','')
   if fields>0 and #letters>=3 then patterns[#patterns+1]={source=source,pattern='^'..table.concat(pieces)..'$',target=target,fields=fields} end
  end
 end
 table.sort(patterns,function(a,b)if #a.source==#b.source then return a.source<b.source end;return #a.source>#b.source end)
 local function localize(text)
  if type(text)~='string' then return text end
  if strings[text] then return strings[text] end
  for _,row in ipairs(patterns) do
   local captures={text:match(row.pattern)}
   if #captures==row.fields then
    local index=0
    return (row.target:gsub(token,function()index=index+1;return captures[index] end))
   end
  end
  return text
 end
 mod.exports.localizeUi=localize
 for key,value in pairs(strings) do mod.content.strings:override(key,value) end
 local function names(cat,registry,records)
  for key,value in pairs(catalog(cat)) do
   if not records or records[key] then registry:patch(key,{name=value}) end
  end
 end
 names('species_names',mod.content.pokemon,data.pokemon)
 names('move_names',mod.content.moves,data.moves)
 names('item_names',mod.content.items,data.items)
 names(generation==1 and 'trainer_names' or 'trainer_class_names',mod.content.trainers)
 names('type_names',mod.content.type_chart,data.type_chart and data.type_chart.types)
 if generation==2 then names('landmark_names',mod.content.landmarks) end
 for key,value in pairs(catalog('status_labels')) do mod.content.statuses:patch(key,{label=value,hudLabel=value}) end
 for key,value in pairs(catalog('dex_kinds')) do if data.pokemon[key] then mod.content.pokemon:patch(key,{dexEntry={kind=value}}) end end
 if generation==1 then
  for key,value in pairs(catalog('dex_metrics')) do if data.pokemon[key] then mod.content.pokemon:patch(key,{dexEntry=value}) end end
 else
  for _,cat in ipairs({'move_descriptions','item_descriptions'}) do
   local records=cat=='move_descriptions' and data.moves or data.items
   for key,value in pairs(catalog(cat)) do if records[key] then records[key].description=value end end
  end
  for key,value in pairs(catalog('dex_entries')) do
   local entry=data.gen2Pokedex and data.gen2Pokedex.entries[key]
   if entry then for _,field in ipairs({'kind','text','text2'}) do entry[field]=value[field] end end
  end
  for key,value in pairs(catalog('dex_metrics')) do
   local entry=data.gen2Pokedex and data.gen2Pokedex.entries[key]
   if entry then entry.heightM=value.heightM;entry.weightKg=value.weightKg end
  end
  if mod.game.oakSpeechData and mod.game.oakSpeechData.text then
   local named=catalog('rom_text')
   for i=1,7 do local label='_OakText'..i;if named[label] then mod.game.oakSpeechData.text[label]=named[label] end end
  end
  for key,value in pairs(catalog('trainer_names')) do
   local cls,index=key:match('^(.-):(%d+)$')
   local group=data.gen2Trainers and data.gen2Trainers.classes[cls]
   local trainer=group and group.trainers[tonumber(index)]
   if trainer then trainer.name=value end
  end
  for _,commands in pairs(data.gen2Scripts or {}) do
   if type(commands)=='table' then for _,cmd in ipairs(commands) do
    if type(cmd)=='table' and cmd.op=='getstring' and strings[cmd.string] then cmd.string=strings[cmd.string] end
   end end
  end
 end
 -- Immediate-mode GB menus pass their authored English strings straight to
 -- Font.encode. Resolve catalog keys and authored printf templates only while
 -- this mod bus is active; captured names and numeric values remain intact.
 do
  local accent={es={'Á','É','Í','Ó','Ú','Ñ','Ü','¿','¡'},fr={'à','è','é','ù','ç','ë','ï','ê','î'},it={'À','È','É','Ì','Ò','Ù','à','è','ì'}}
  local fontmap=catalog('charmap')
  mod.hooks:wrap('ui.naming.grid',function(next,base,ctx)
   local grid=next(base,ctx)
   local out={};for i,row in ipairs(grid) do out[i]={};for j,c in ipairs(row) do out[i][j]=c end end
   local chars=accent[mod.language]
   -- Keep a font-based fallback for development callers without a language.
   if not chars then
    if fontmap['ç'] then chars=accent.fr elseif fontmap['ñ'] then chars=accent.es else chars=accent.it end
   end
   out[4]={};for i,c in ipairs(chars) do out[4][i]=ctx.lower and (({['Á']='á',['É']='é',['Í']='í',['Ó']='ó',['Ú']='ú',['Ñ']='ñ',['Ü']='ü',['À']='à',['È']='è',['Ì']='ì',['Ò']='ò',['Ù']='ù'})[c] or c:lower()) or c end
   return out
  end)
 end
 local Font=require('src.render.Font')
 local Runtime=require('src.mods.Runtime')
 local version=require('src.core.GameVersion')
 local bus=Runtime.events
 local marker='__ula_european_active__'
 mod.content.strings:override(marker,'active')
 local patch=Font.__ulaEuropeanStrings
 if not patch then
  patch={original=Font.encode,split=Font.split};Font.__ulaEuropeanStrings=patch
  Font.split=function(text)
   local spans=patch.split(text)
   if patch.active and patch.active() and type(text)=='string' then
    for _,span in ipairs(spans) do
     local code=patch.fontmap[text:sub(span.from,span.to)]
     if code then span.code=code end
    end
   end
   return spans
  end
  Font.encode=function(text)
   if patch.active and patch.active() and type(text)=='string' then text=patch.localize(text) end
   return patch.original(text)
  end
 end
 patch.active=function() return Runtime.events==bus and version.get()==mod.edition and data.strings and data.strings[marker]=='active' end
 patch.strings=strings;patch.localize=localize;patch.fontmap=catalog('charmap')
end
