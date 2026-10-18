-- Enumerate real SummaryData lookups with the active edition's native font.
return function()
 local Font=require('src.ui.game3.frlg_font')
 local Data=require('src.core.game3.summary_data')
 local own=assert(love.filesystem.load('mods/german_rom_source/ptbr_ability_descriptions.lua'))()
 local version=require('src.core.GameVersion').get()
 local rs=version=='ruby' or version=='sapphire'
 local opts=rs and {font='native_'..require('src.ui.game3.rs.summary_menu').manifest().nativeWindow.fontNum} or {}
 local budget=(version=='firered' or version=='leafgreen') and 222 or 152
 local bad={}
 local names=assert(love.filesystem.load('mods/german_rom_source/ptbr_abilities.lua'))()
 local Pokemon=require('src.core.game3.pokemon')
 for id=0,77 do
  local name=Pokemon.abilityName(id)
  assert(name==names[id],'Ability name mismatch '..id)
  local nameBudget=(version=='firered' or version=='leafgreen') and 152 or 152
  if Font.measure(name,opts)>nameBudget then bad[#bad+1]={id=id,width=Font.measure(name,opts),name=name} end
  local desc=Data.abilityDescription(id)
  assert(desc==own[id],'Ability description mismatch '..id..': '..tostring(desc)..' / expected '..own[id])
  if desc:find('\n',1,true) or Font.measure(desc,opts)>budget then bad[#bad+1]={id=id,width=Font.measure(desc,opts),text=desc} end
  for ch in Font.utf8Chars(desc) do assert(ch==' ' or Font.glyphId(ch)~=0,'Missing ability glyph '..ch) end
 end
 print('LANGUAGE_ABILITY_LAYOUT '..require('src.link.Json').encode(bad))
 assert(#bad==0,'Ability description exceeds native panel')
 print('LANGUAGE_ABILITY_DESCRIPTIONS_OK',78)
end
