-- Actual diploma/credits UI with a new-game fixture. This is UI coverage,
-- not a claim that the story or Pokédex was completed in these runs.
local function wait(n) for _=1,n do coroutine.yield() end end
return function(game)
 io.stdout:setvbuf('no')
 local ok,err=xpcall(function()
  if love.setDeprecationOutput then love.setDeprecationOutput(false) end
  local version=require('src.core.GameVersion').get()
  local lang=assert(os.getenv('QA_LANGUAGE'))
  local mod=assert(game.mods.exports.german_rom_source,'Language mod did not load')
  assert(mod.status==(lang=='en' and 'english' or 'active') and mod.language==lang,'Wrong active language')
  local Json=require('src.link.Json')
  local frlg=version=='firered' or version=='leafgreen'
  local prefix=frlg and 'FR_' or version=='emerald' and 'EM_' or version=='ruby' and 'RU_' or 'SA_'
  local map=prefix..(frlg and 'VIRIDIAN_CITY' or 'OLDALE_TOWN')
  game:_handleBootAction({action='new_game',name='TEST',gender=0,start={map=map,x=6,y=17,facing='up'}})
  wait(60)
  local function capture(name)
   game.capturePath=os.getenv('SHOT_DIR')..'/'..version..'-'..lang..'-'..name..'.png'
   for _=1,600 do if not game.capturePath then break end;wait(1) end
   assert(not game.capturePath,'Screenshot timeout')
   print('LANGUAGE_CAPTURE',version,lang,name)
  end
  local rs=version=='ruby' or version=='sapphire'
  local Diploma=require('src.ui.game3.'..(rs and 'rs.diploma' or 'diploma'))
  assert(Diploma.show(),'Diploma assets unavailable')
  for _=1,600 do if Diploma.phase()=='wait' then break end;wait(1) end
  assert(Diploma.phase()=='wait','Diploma did not finish its fanfare')
  local body=Diploma._body
  if rs then local parts={};for _,row in ipairs(Diploma._content) do parts[#parts+1]=row.text end;body=table.concat(parts,' | ') end
  assert(body)
  assert(#body>20 and (lang~='pt-BR' or not body:find('This document',1,true)),'Diploma untranslated/empty: '..body)
  print('LANGUAGE_DIPLOMA_EVIDENCE '..Json.encode({game=version,language=lang,body=body,
   fixture='New game; native certificate UI opened directly; no full-Pokedex claim'}))
  capture('diploma')
  game:keypressed('z');wait(1);game:keyreleased('z')
  for _=1,300 do if not Diploma.isOpen() then break end;wait(1) end
  assert(not Diploma.isOpen(),'Diploma did not close')
  wait(30)
  local Credits=require('src.ui.game3.'..(frlg and 'credits' or version=='emerald' and 'rse.credits' or 'rs.credits'))
  assert(Credits.start({session=game.session,hasRecords=false}),'Credits assets unavailable')
  local seen,count,finished={},0,false
  for frame=1,30000 do
   Credits.update(1/60)
   local state=frlg and Credits.state() or Credits.state
   local text=state and state.text
   if text then
    local key=Json.encode(text)
    if not seen[key] then
     seen[key]=true;count=count+1
     local evidence=text
     if not frlg then
      evidence={};local Font=require('src.ui.game3.frlg_font')
      for _,row in ipairs(text) do
       evidence[#evidence+1]=row.text
       if row.text:find('%S') then assert(Font.measure(row.text,rs and {font='native_3',textMode=2,letterSpacing=0} or {letterSpacing=1})<=240,'Credits text clipped: '..row.text) end
      end
     end
     print('LANGUAGE_CREDITS_PAGE',version,lang,count,Json.encode(evidence))
     if count==2 or count==8 or count==20 then
      -- Let the native fade finish before saving the actual rendered page.
      for _=1,45 do Credits.update(1/60) end
      capture('credits-'..count)
     end
    end
   end
   local ending=state and (frlg and state.mainseq==Credits.SCENE.WAITBUTTON or not frlg and state.mainFunc=='end6')
   if ending then
    for _=1,90 do Credits.update(1/60) end
    capture('the-end');finished=true;print('LANGUAGE_CREDITS_END',version,lang,frame,count);break
   end
   if frame%120==0 then wait(1) end
  end
  assert(finished and count>=10,'Credit roll did not reach its actual ending')
  if lang=='pt-BR' and not frlg then
   for key in pairs(seen) do assert(not key:find('Director',1,true) and not key:find('RUBY VERSION',1,true),'English/incorrect edition in credits') end
  end
  Credits.reset()
  print('LANGUAGE_ENDINGS_OK',version,lang,count)
 end,debug.traceback)
 if not ok then print('LANGUAGE_ENDINGS_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
