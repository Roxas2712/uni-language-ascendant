-- Actual map scripts and battle input; no invented dialogue fixtures.
local function wait(n)for _=1,n do coroutine.yield()end end
return function(game)
 io.stdout:setvbuf('no')
 if love.setDeprecationOutput then love.setDeprecationOutput(false)end
 local ok,err=xpcall(function()
  local v=require('src.core.GameVersion').get();local lang=os.getenv('QA_LANGUAGE') or 'ko';local playerName=lang=='ja' and 'テスト' or '테스트'
  local e=assert(game.mods.exports.german_rom_source);assert(e.status=='active' and e.language==lang,tostring(e.status))
  assert(game.data.pokemon.BULBASAUR.name==(lang=='ja' and 'フシギダネ' or '이상해씨'),game.data.pokemon.BULBASAUR.name)
  local Font=require('src.render.Font');local Save=require('src.core.gen2.Save');local Mon=require('src.battle.gen2.Mon')
  local S=require('src.core.SaveSerializer');local Json=require('src.link.Json')
  local f=assert(io.open(os.getenv('SHOT_DIR')..'/'..v..'-expected.json'));local expected=Json.decode(f:read('*a'));f:close()
  local glyphCount=0
  for path,raw in pairs(e.assets) do if path:match('^lang/') then
   local body=assert(S.decode(raw,{maxBytes=16*1024*1024,maxNodes=500000,maxDepth=40}))
   local function visit(value)
    if type(value)=='table' then for _,x in pairs(value)do visit(x)end
    elseif type(value)=='string' then
     for _,span in ipairs(Font.split(value))do
      local char=value:sub(span.from,span.to)
      if char:byte()>127 then assert(span.code~=0x7f,'Missing glyph '..char..' in '..path);glyphCount=glyphCount+1 end
     end
    end
   end
   if not path:find('font_pages') and not path:find('charmap')then visit(body)end
  end end
  print('ASIAN_GLYPHS_OK',v,glyphCount,e.coverage.cacheHit and 'warm' or 'cold')
  collectgarbage('collect')
  local names,hashes={},{}
  for path in pairs(e.assets)do names[#names+1]=path end;table.sort(names)
  for _,path in ipairs(names)do hashes[#hashes+1]=path..':'..love.data.encode('string','hex',love.data.hash('string','sha256',e.assets[path]))end
  print('ASIAN_LOAD_JSON '..Json.encode({game=v,language=lang,cacheHit=e.coverage.cacheHit,seconds=e.loadSeconds,luaMemoryKiB=collectgarbage('count'),payloads=#names,digest=love.data.encode('string','hex',love.data.hash('string','sha256',table.concat(hashes,'\n')))}))
  local baseRoot=love.filesystem.getSaveDirectory()..'/'..v..'/data/generated/'
  local function same(a,b)
   if type(a)~=type(b)then return false end
   if type(a)~='table'then return a==b end
   for k,x in pairs(a)do if not same(x,b[k])then return false end end
   for k in pairs(b)do if a[k]==nil then return false end end
   return true
  end
  for _,spec in ipairs({{'pokemon',{'baseStats','types','catchRate','baseExp','growthRate','learnset','evolutions','tmhm','eggMoves'}},{'moves',{'power','accuracy','pp','effect','type','effectChance'}}})do
   local base=assert(loadfile(baseRoot..spec[1]..'.lua'))()
   for id,row in pairs(base)do if type(row)=='table'and row.id then for _,field in ipairs(spec[2])do assert(same(row[field],game.data[spec[1]][id][field]),'Mechanical data changed: '..id..'.'..field)end end end
  end
  print('ASIAN_MECHANICS_OK',v)
  if lang=='ja'then
   assert(game.data.pokemon.GOLBAT.name=='ゴルバット',game.data.pokemon.GOLBAT.name)
   -- The cartridge reuses hiragana り/へ glyph slots in katakana names.
   assert(game.data.pokemon.DUGTRIO.name=='ダグトりオ',game.data.pokemon.DUGTRIO.name)
   for _,char in ipairs({'ゴ','ザ','ゼ'})do assert(Font.split(char)[1].code~=0x7f,'Missing kana '..char)end
  end
  if os.getenv('QA_MODE')=='art'then
   assert(game.titleData.screen:find('rom%-language'),game.titleData.screen)
   game.stack:clear();game.phase='boot'
   game.stack:push(require('src.ui.gen2.TitleState').new(game,{title=game.titleData,onContinue=function()game:showMainMenu()end}))
   wait(150)
   game.capturePath=os.getenv('SHOT_DIR')..'/'..v..'-'..lang..'-native-title.png'
   while game.capturePath do wait(1)end
   game:keypressed('z');wait(1);game:keyreleased('z');wait(60)
   game.capturePath=os.getenv('SHOT_DIR')..'/'..v..'-'..lang..'-main-menu.png'
   while game.capturePath do wait(1)end
   print('ASIAN_GEN2_LIVE_OK',v,'native title and main menu');return
  end
  if os.getenv('QA_MODE')=='warm'or os.getenv('QA_MODE')=='verify'or os.getenv('QA_MODE')=='cold-verify'then
   if os.getenv('QA_MODE')=='warm'then assert(e.coverage.cacheHit,'Warm run recompiled')end
   local saved=assert(Save.load(v));assert(saved.player.name==playerName and saved.party[1].nickname==playerName)
   print('ASIAN_GEN2_LIVE_OK',v,'cache/save verification');return
  end
  game:continueGame(Save.newGame({playerName=playerName,trainerId=12345}));game.speedOverride=1
  local world=game.world;local mon=Mon.new(game.data,'BULBASAUR',15);game.save.party={mon};mon.nickname=playerName;mon.hp=1;mon.status='PSN'
  local maxHp=mon.maxHp or mon.stats.hp
  local function press(key,n)game:keypressed(key);wait(1);game:keyreleased(key);wait(n or 8)end
  local function capture(name)
   game.capturePath=os.getenv('SHOT_DIR')..'/'..v..'-'..lang..'-'..name..'.png'
   for _=1,300 do if not game.capturePath then return end;wait(1)end
   error('Capture timeout '..name)
  end
  if os.getenv('QA_MODE')=='credits'then
   dofile(os.getenv('GERMAN_MOD_ROOT')..'/tests/asian_gen2_credits.lua')(game,{wait=wait,press=press,capture=capture,lang=lang,version=v,expected=expected})
   print('ASIAN_GEN2_LIVE_OK',v,'original port credits');return
  end
  if os.getenv('QA_MODE')=='regional'then
   dofile(os.getenv('GERMAN_MOD_ROOT')..'/tests/asian_gen2_regional.lua')(game,{wait=wait,press=press,capture=capture,lang=lang,version=v,expected=expected})
   print('ASIAN_GEN2_LIVE_OK',v,'real regional events');return
  end
  if os.getenv('QA_MODE')=='extended'or os.getenv('QA_MODE')=='menus'then
   dofile(os.getenv('GERMAN_MOD_ROOT')..'/tests/asian_gen2_extended.lua')(game,{wait=wait,press=press,capture=capture,lang=lang,version=v,expected=expected})
   print('ASIAN_GEN2_LIVE_OK',v,'actual purchase, menus, intro');return
  end
  local outdoor=game.data.gen2Maps.CHERRYGROVE_CITY
  for _,kind in ipairs({'POKECENTER','MART'})do
   local warp
   for _,w in ipairs(outdoor.warps)do if w.destMap:find(kind)then warp=w;break end end
   assert(warp);world:setMap('CHERRYGROVE_CITY',warp.x,warp.y+1,'up',{via='boot',continue=true});wait(60);world:cancelMapNameSign();capture(kind:lower()..'-front')
  end
  local TextBox=require('src.render.TextBox');local original=TextBox.new;local heard={}
  TextBox.new=function(g,text,...)
   heard[#heard+1]=text;print('ASIAN_REAL_DIALOGUE',Json.encode({text=text}))
   return original(g,text,...)
  end
  world:setMap('CHERRYGROVE_POKECENTER_1F',3,3,'up',{via='boot',continue=true});wait(60);world:interact();wait(90);capture('nurse-greeting')
  local capturedReturn,capturedChoice=false,false;local Choice=require('src.ui.ChoiceBox')
  for _=1,250 do
   local current=game.stack:top()
   if getmetatable(current)==Choice and not capturedChoice then
    assert(current.firstItem>=2,'Native choice text touches top border')
    capture('nurse-choice');capturedChoice=true
   end
   for _,text in ipairs(heard)do if text==expected.NurseReturnPokemonText and not capturedReturn then wait(90);capture('nurse-healed');capturedReturn=true end end
   if capturedReturn and mon.hp==maxHp and not mon.status then break end
   press('z',8)
  end
  assert(mon.hp==maxHp and not mon.status,'Nurse did not heal/cure')
  assert(capturedChoice,'Actual nurse YES/NO prompt was not exercised')
  local function saw(text)for _,x in ipairs(heard)do if x==text then return true end end end
  assert(saw(expected.NurseAskHealText),'Native heal question not shown')
  assert(saw(expected.NurseReturnPokemonText),'Native return dialogue not shown')
  for _=1,35 do press('z',3)end
  assert(saw(expected.NurseGoodbyeText),'Native goodbye not shown')
  TextBox.new=original
  assert(game:writeSave());local loaded=assert(Save.load(v));assert(loaded.party[1].nickname==playerName and loaded.player.name==playerName,'Save Unicode roundtrip')
  print('ASIAN_NURSE_SAVE_OK',v)
  local Naming=require('src.ui.gen2.NamingScreen');local entered
  local naming=Naming.new(game,{type='player',onDone=function(name)entered=name end})
  game.stack:push(naming)
  local keys=lang=='ja'and {'テ','ス','ト'}or {'ㅌ','ㅔ','ㅅ','ㅡ','ㅌ','ㅡ'}
  for _,char in ipairs(keys)do
   local found
   for _=1,12 do
    for y,row in ipairs(naming:rows())do for x,c in ipairs(row)do if c==char then naming.row=y-1;naming.col=x-1;found=true end end end
    if found then break end
    naming:toggleCase()
   end
   assert(found,'Character absent from keyboard: '..char);press('z',3)
  end
  assert(naming.text==playerName,naming.text);capture('naming')
  press('x',3)
  assert(naming.text==(lang=='ja'and 'テス'or '테스ㅌ'),'Unicode deletion failed: '..naming.text)
  naming:addCharacter(lang=='ja'and 'ト'or 'ㅡ');assert(naming.text==playerName)
  naming.row=naming:bottomRow();naming.col=6;press('z',3);assert(entered==playerName,'Naming accept failed')
  game.stack:pop();print('ASIAN_NAMING_INPUT_OK',v)
  mon.moves={{id='TACKLE',pp=35},{id='GROWL',pp=40},{id='VINE_WHIP',pp=10},{id='RAZOR_LEAF',pp=25}};local outcome;world:startBattle({wild=Mon.new(game.data,'RATTATA',2)},function(result)outcome=result end)
  local sawMenu,sawMoves=false,false;local battleMessages={}
  for _=1,750 do
   local top=game.stack:top()
   if top and top.isBattle then
    if top.message and not battleMessages[top.message]then
     battleMessages[top.message]=true;print('ASIAN_REAL_BATTLE_MESSAGE',Json.encode({text=top.message}))
    end
    if top.phase=='menu' and not sawMenu then capture('battle-menu');sawMenu=true end
    if (top.phase=='moves' or top.phase=='moveSelect')and not sawMoves then capture('battle-moves');sawMoves=true end
   end
   if outcome then break end
   press('z',3)
  end
  for text in pairs(battleMessages)do
   assert(not text:find('[A-Za-z]'),'English in exercised battle message: '..text)
  end
  assert(sawMenu and sawMoves and outcome=='win','Wild battle failed '..tostring(outcome));print('ASIAN_BATTLE_INPUT_OK',v)
  game.save.pokedex.seen.BULBASAUR=true;game.save.pokedex.caught.BULBASAUR=true
  game.stack:clear();game.stack:push(require('src.ui.gen2.PokedexMenu').new(game,{entrySpecies='BULBASAUR'}));wait(3);capture('pokedex')
  local dex=game.stack:top();dex.entryAction=2;press('z',3);assert(dex.view=='area','Dex area action failed');press('x',3);assert(dex.view=='entry')
  dex.entryAction=1;press('z',3);assert(dex.page==1,'Native one-page Dex changed page')
  print('ASIAN_GEN2_LIVE_OK',v)
 end,debug.traceback)
 if not ok then print('ASIAN_GEN2_LIVE_FAILED',err)end
 love.event.quit(ok and 0 or 1)
end
