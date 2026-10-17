-- Native word picker and saved profile rendering. Fixtures contain word IDs
-- only; the normal game data and translation module provide every label.
return function(game)
 io.stdout:setvbuf('line')
 local function wait(n)for _=1,n do coroutine.yield()end end
 local ok,err=xpcall(function()
  if love.setDeprecationOutput then love.setDeprecationOutput(false)end
  local version=require('src.core.GameVersion').get()
  local rs=version=='ruby' or version=='sapphire'
  local prefix=({ruby='RU_',sapphire='SA_',emerald='EM_',firered='FR_',leafgreen='FR_'})[version]
  game:_handleBootAction({action='new_game',name='TEST',gender=0,start={map=prefix..((version=='firered' or version=='leafgreen') and 'VIRIDIAN_CITY' or 'OLDALE_TOWN'),x=6,y=17,facing='up'}})
  wait(60)
  local Easy=require('src.core.game3.easy_chat_text')
  local Font=require('src.ui.game3.frlg_font');local drawn={};local draw=Font.draw
  Font.draw=function(text,x,y,opts)drawn[text]=true;return draw(text,x,y,opts)end
  local function press(k)game:keypressed(k);wait(1);game:keyreleased(k);wait(45)end
  local function capture(name)
   wait(10);game.capturePath=os.getenv('SHOT_DIR')..'/'..version..'-pt-BR-easy-chat-'..name..'.png'
   for _=1,600 do if not game.capturePath then break end;wait(1)end;assert(not game.capturePath)
  end
  local Editor=require(rs and 'src.ui.game3.rs.easy_chat_editor' or 'src.ui.game3.easy_chat')
  if rs then Editor.show({type=0,token={},session=game.session,words=game.session.easyChatProfile})
  else Editor.open({type=0,session=game.session,words=game.session.easyChatProfile})end
  wait(100);capture('profile');press('z');capture('groups');
  if rs then
   local f=assert(io.open(os.getenv('SHOT_DIR')..'/'..version..'-easy-chat-map.lua','w'));f:write(require('src.import.LuaWriter').encode({map=Editor._map,man=Editor._man}));f:close()
  end
  if rs then
   press('rshift');capture('alphabet');assert(Editor._group.alpha)
   press('z');capture('letter-a');
   if Editor._view=='words'then
    for _,w in ipairs(Editor._list)do assert(Easy.word(w.id):match('^A') or Easy.word(w.id):match('^À') or Easy.word(w.id):match('^Á') or Easy.word(w.id):match('^Ã') or Easy.word(w.id):match('^Â'),'Wrong translated initial: '..Easy.word(w.id))end
   end
  else press('z');capture('words')end
  local base=require('src.core.game3.dataset').cache()
  local pack=assert(loadstring(assert(base:read(Easy.FILE))))()
  local words=assert(loadfile(os.getenv('GERMAN_MOD_ROOT')..'/mod/ptbr_easy_chat_words.lua'))()
  local bad={};local count=0
  local opts=rs and Editor.textOptions('picker') or {font='narrow'}
  for gid,g in pairs(pack.groups)do for _,w in ipairs(g.words)do
   local target=Easy.word(w.id);assert(type(target)=='string' and target~='')
   if gid~=0 and gid~=21 and gid~=18 and gid~=19 then
    local sha=love.data.encode('string','hex',love.data.hash('string','sha256',gid..'\0'..w.text))
    assert(target==assert(words[sha]).target,'Wrong word ID mapping')
   end
   for ch in Font.utf8Chars(target)do assert(Font.glyphId(ch),'Missing glyph '..ch)end
   local width=Font.measure(target,opts)
   if width>80 then bad[#bad+1]={group=gid,id=w.id,text=target,width=width}end
   count=count+1
  end end
  local Json=require('src.link.Json');local f=assert(io.open(os.getenv('SHOT_DIR')..'/'..version..'-easy-chat-overflow.json','w'));f:write(Json.encode(bad));f:close()
  print('LANGUAGE_EASY_CHAT_LAYOUT',#bad)
  if rs then
   Editor.reset()
   local Message=require('src.core.game3.rs.easy_chat_message')
   local Host=require('src.ui.game3.rs.field_auto_scroll_message')
   local result=assert(Message.build(game.session,0));assert(result.text==Font.wrap(Easy.phrase(game.session.easyChatProfile,2,2),208,{font='native_3'}))
   assert(Host.open(Host.prepare(result)));wait(240);capture('saved-profile');assert(Host.text()==result.text);Host.close()
  else Editor.close()end
  Font.draw=draw
  assert(#bad==0,'Word picker clips translated words; see overflow report')
  print('LANGUAGE_EASY_CHAT_OK',version,count)
 end,debug.traceback)
 if not ok then print('LANGUAGE_EASY_CHAT_FAILED',err)end;love.event.quit(ok and 0 or 1)
end
