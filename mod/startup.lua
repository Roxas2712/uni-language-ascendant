-- The picker owns only the pre-title interval. All frame/input wrappers are
-- restored on confirmation; the running game pays no picker cost.
return function(mod,version,own)
 local preferences=own('preferences.lua')(mod)
 local catalog=own('catalog.lua')
 local requirements=own('rom_requirements.lua')
 local locales=own('locales.lua')
 local order={'en','de','fr','it','es','ja','ko','zh-Hans','zh-Hant'}
 local savedUI=preferences:read('preferences/ui-language.txt')
 local uiLanguage=locales[savedUI] and savedUI or 'en'
 local choices={{id='en',name='English',available=true}}
 local known={en=true}
 for _,entry in ipairs(catalog) do
  if entry.game==version and not known[entry.language] and mod.imports:info(entry.id)~=nil then
   known[entry.language]=true
   choices[#choices+1]={id=entry.language,name=entry.name,available=true}
  end
 end
 -- Use the same installed, per-game languages in both entry points. Menu
 -- localization and the ROM requirements list remain independent of imports.
 mod.options:define(own('options_schema.lua')(choices))
 local saved=preferences:read('preferences/'..version..'.txt')
 local language=preferences.fresh and 'auto' or mod.options:get('language')
 if language=='auto' or not language then language=saved or 'en' end
 if not known[language] then language='en' end
 local selected=1
 for i,c in ipairs(choices) do if c.id==language then selected=i end end
 local state={open=false,language=language,choices=choices,index=selected,notice='',page=1,uiLanguage=uiLanguage,uiIndex=1,stage=locales[savedUI] and 'game' or 'menu'}
 if preferences:read('preferences/notice.txt')~='accepted' then state.stage='notice' end
 for i,id in ipairs(order) do if id==uiLanguage then state.uiIndex=i end end
 function state.previewLocale(id) if not locales[id] then return false end;state.uiLanguage=id;return true end
 function state.chooseMenu(id)
  if state.stage=='intro' or state.stage=='notice' or state.stage=='reset' then return false,'Complete the current step first' end
  if not locales[id] then return false,'Unknown menu language' end
  local ok,err=preferences:write('preferences/ui-language.txt',id)
  if not ok then state.noticeKey='saveFailed';return false,err end
  state.uiLanguage=id;state.stage='game';state.noticeKey=nil
  for i,l in ipairs(order) do if l==id then state.uiIndex=i end end
  return true
 end
 for i,row in ipairs(requirements) do if row.game==version then state.page=i end end
 mod.exports.startup=state
 local game=mod.game
 local originals,wrappers={},{}
 local oldVolume
 local intro
 local showPicker=preferences.fresh or state.stage=='notice' or mod.options:get('showPicker')~=false
 local function restore()
  state.open=false
  if intro then intro:close();intro=nil;state.intro=nil end
  for name,fn in pairs(wrappers) do if game[name]==fn then game[name]=originals[name] end end
  if oldVolume and love.audio then love.audio.setVolume(oldVolume);oldVolume=nil end
 end
 local function persist(id)
  local ok,err=preferences:write('preferences/'..version..'.txt',id)
  if not ok then return nil,err or 'Could not save language' end
  -- A choice made here takes precedence over a launcher-wide override.
  local Save=require('src.core.SaveData')
  local opts=Save.loadOptions() or Save.defaultOptions()
  opts.modOptions=opts.modOptions or {};opts.modOptions[mod.id]=opts.modOptions[mod.id] or {}
  opts.modOptions[mod.id].language='auto'
  local written,why=Save.saveOptions(opts)
  if not written then return nil,why or 'Could not save options' end
  if game.mods then game.mods.modOptions[mod.id]=opts.modOptions[mod.id] end
  for _,o in ipairs({game.options,game.save and game.save.options}) do
   if o then o.modOptions=opts.modOptions end
  end
  return true
 end
 function state.choose(id)
  if state.stage=='intro' or state.stage=='notice' or state.stage=='reset' then return false,'Complete the current step first' end
  local choice
  for _,c in ipairs(choices) do if c.id==id then choice=c end end
  if not choice then return false,'Unknown language' end
  if not choice.available then
   state.noticeKey='missing'
   return false,'Missing ROM'
  end
  if id~='en' and mod.exports.status~='active' and id==language then
   state.noticeKey='inactive'
   return false,'Language not active'
  end
  local ok,err=persist(id)
  if not ok then state.noticeKey='saveFailed';return false,err end
  if id==language then restore();return true end
  state.noticeKey='restarting'
  state.restarting=true
  require('src.core.HostShell').restart()
  return true,'restart'
 end
 function state.back()
  if state.stage=='intro' or state.stage=='notice' then return false end
  if state.stage=='reset' then state.stage=state.previousStage or 'game'
  elseif state.stage=='menu' then
   local saved=preferences:read('preferences/ui-language.txt')
   if not saved or not locales[saved] then return false end
   state.uiLanguage=saved
   for i,id in ipairs(order) do if id==saved then state.uiIndex=i end end
   state.stage='game'
  else state.stage='menu' end
  state.noticeKey=nil;return true
 end
 function state.requestReset()
  if state.stage=='intro' or state.stage=='notice' then return false end
  state.previousStage=state.stage;state.stage='reset';state.resetIndex=1;state.noticeKey=nil;return true
 end
 function state.resetProfile()
  if state.stage~='reset' then return false end
  local ok,err=preferences:reset()
  if not ok then state.noticeKey='saveFailed';return false,err end
  state.noticeKey='restarting';state.restarting=true
  require('src.core.HostShell').restart();return true
 end
 function state.skipIntro() return intro and intro:skip() or false end
 function state.confirm()
  if state.stage=='notice' then
   local ok,err=preferences:write('preferences/notice.txt','accepted')
   if not ok then state.noticeKey='saveFailed';return false,err end
   state.stage='menu';return true
  end
  if state.stage=='reset' then if state.resetIndex==2 then return state.resetProfile() else return state.back() end end
  if state.stage=='intro' then return state.skipIntro() end
  if state.stage=='menu' then return state.chooseMenu(order[state.uiIndex]) end
  return state.choose(choices[state.index].id)
 end
 local draw
 local function key(key)
  if state.stage=='intro' then
   if key=='return' or key=='space' or key=='escape' or key=='z' or key=='x' then state.skipIntro() end
   return
  end
  if key=='escape' or key=='backspace' then state.back();return end
  if key=='r' then state.requestReset();return end
  if state.stage=='notice' then if key=='return' or key=='space' then state.confirm() end;return end
  if state.stage=='reset' then
   if key=='left' or key=='right' then state.resetIndex=3-state.resetIndex
   elseif key=='return' or key=='space' then state.confirm() end
   return
  end
  if key=='l' then state.stage='menu';state.noticeKey=nil;return end
  if state.stage=='menu' then
   local steps={left=-1,a=-1,right=1,d=1,up=-3,down=3}
   if steps[key] then state.uiIndex=(state.uiIndex-1+steps[key])%#order+1;state.previewLocale(order[state.uiIndex])
   elseif key=='return' or key=='space' or key=='z' then state.confirm() end
   return
  end
  if key=='left' or key=='a' then state.index=(state.index-2)%#choices+1
  elseif key=='right' or key=='d' then state.index=state.index%#choices+1
  elseif key=='return' or key=='space' or key=='z' then state.confirm()
  elseif key=='tab' then
   local reverse=love.keyboard and love.keyboard.isDown('lshift','rshift')
   state.page=(state.page-1+(reverse and -1 or 1))%#requirements+1
  end
 end
 local function install()
  if not game then return end
  local Intro=own('intro.lua')
  local pending=Intro.pending(mod,preferences)
  if not showPicker and not pending then return end
  state.open=true
  if showPicker then draw=own('startup_view.lua')(mod,state,requirements,locales,order) end
  if pending then
   local nextStage=state.stage
   local ok,result=pcall(Intro.new,mod,own,function()
    intro=nil;state.intro=nil;state.stage=nextStage
    if not showPicker then restore()
    elseif love.audio then oldVolume=love.audio.getVolume();love.audio.setVolume(0) end
   end,preferences)
   if ok then intro=result;state.intro=intro;state.stage='intro'
   else
    mod.log:warn('Ascendant intro could not load: %s',tostring(result))
    if not showPicker then restore();return end
   end
  end
  local Runtime=require('src.mods.Runtime');local bus=Runtime.events
  local marker='mod.german_rom_source.picker'
  mod.events:on(marker,function() end)
  local function wrap(name,fn)
   originals[name]=game[name];wrappers[name]=fn;game[name]=fn
  end
  wrap('draw',function() if intro then intro:draw() else draw() end end)
  wrap('update',function(self,dt)
   if Runtime.events~=bus or not Runtime.wants(marker) then restore();return self:update(dt) end
   if intro then intro:update(dt);return end
   if love.audio then
    if not oldVolume then oldVolume=love.audio.getVolume() end
    love.audio.setVolume(0)
   end
  end)
  wrap('keypressed',function(_,k) key(k) end)
  wrap('keyreleased',function() end)
  wrap('gamepadpressed',function(_,_,button)
   if state.stage=='intro' then if button=='a' or button=='b' or button=='start' then state.skipIntro() end;return end
   if button=='dpleft' then key('left') elseif button=='dpright' then key('right') elseif button=='dpup' then key('up') elseif button=='dpdown' then key('down')
   elseif button=='a' or button=='start' then state.confirm() elseif button=='rightshoulder' then key('tab') elseif button=='y' then key('l') elseif button=='b' then state.back() elseif button=='x' then state.requestReset() end
  end)
  wrap('gamepadreleased',function() end)
  wrap('mousepressed',function(_,x,y,button)
   if button~=1 then return end
   if state.stage=='intro' then state.skipIntro();return end
   local w,h=love.graphics.getDimensions();local scale=math.min(w/960,h/650)
   x=(x-(w-960*scale)/2)/scale;y=(y-(h-650*scale)/2)/scale
   for _,box in ipairs(state.hitboxes or {}) do
    if x>=box.x and x<box.x+box.w and y>=box.y and y<box.y+box.h then box.action();return end
   end
  end)
  wrap('mousereleased',function() end)
  wrap('touchpressed',function(self,_,x,y) self:mousepressed(x,y,1) end)
 end
 mod.events:on('game.ready',install)
 -- One global override is exposed in the stock mod manager for changing the
 -- language later. The picker remains available at each normal game launch.
 return language
end
