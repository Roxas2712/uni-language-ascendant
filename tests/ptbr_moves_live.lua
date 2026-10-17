-- Structural/layout checks accompany the real battle test; they are not
-- presented as gameplay dialogue evidence.
return function()
 local P=require('src.core.game3.pokemon')
 local Font=require('src.ui.game3.frlg_font')
 local Summary=require('src.core.game3.summary_data')
 local names=assert(love.filesystem.load('mods/german_rom_source/ptbr_moves.lua'))()
 local base=assert(loadstring(assert(require('src.core.game3.dataset').cache():read('data/generated/gba/pokemon/descriptions.lua'))))()
 local corrections=assert(love.filesystem.load('mods/german_rom_source/ptbr_move_descriptions.lua'))()
 local wide,descriptions,unchanged,descWide={},{},{},{}
 local version=require('src.core.GameVersion').get()
 local isRS=version=='ruby' or version=='sapphire'
 local budget=(version=='firered' or version=='leafgreen') and 112 or 152
 local opts=isRS and {font='native_'..require('src.ui.game3.rs.summary_menu').manifest().nativeWindow.fontNum} or {}
 local maxLines=isRS and 2 or (budget==112 and 4 or 3)
 for id=1,354 do
  local name=P.moveName(id)
  assert(name==names[id],'Move display mismatch: '..id..' / '..tostring(name))
  local width=Font.measure(name)
  if width>77 then wide[#wide+1]={id=id,name=name,width=width} end
  assert(P.romMoveName(id)~=nil,'Lost original move lookup: '..id)
  local description=Summary.moveDescription(id,name)
  assert(description~='---','Lost move description: '..id)
  descriptions[#descriptions+1]={id=id,name=name,description=description}
  local count,maxWidth=0,0
  for line in (description..'\n'):gmatch('(.-)\n') do count=count+1;maxWidth=math.max(maxWidth,Font.measure(line,opts)) end
  if count>maxLines or maxWidth>budget then descWide[#descWide+1]={id=id,width=maxWidth,lines=count} end
  local key='MOVE_'..P.romMoveName(id):upper():gsub('%s+','_'):gsub('[^%w_]','')
  if description==base.MOVES[key] then unchanged[#unchanged+1]=id end
  if corrections[id] then assert(description:gsub('%s+',' ')==corrections[id]:gsub('%s+',' '),'Reviewed move description not applied: '..id) end
 end
 print('LANGUAGE_MOVE_LAYOUT '..require('src.link.Json').encode(wide))
 assert(#wide==0,'Move names exceed the 77px display budget')
 local out=assert(io.open(os.getenv('SHOT_DIR')..'/'..require('src.core.GameVersion').get()..'-actual-move-descriptions.json','wb'))
 out:write(require('src.link.Json').encode(descriptions));out:close()
 print('LANGUAGE_MOVE_DESCRIPTION_LAYOUT '..require('src.link.Json').encode(descWide))
 print('LANGUAGE_MOVE_DESCRIPTION_UNCHANGED '..require('src.link.Json').encode(unchanged))
 if os.getenv('QA_MODE')=='vocabulary' then assert(#descWide==0,'Move descriptions exceed native panel');assert(#unchanged==0,'English move descriptions remain') end
 print('LANGUAGE_MOVES_OK 354 names; description lookup preserved; native font widths')
end
