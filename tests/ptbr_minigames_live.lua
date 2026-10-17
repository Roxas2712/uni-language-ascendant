-- Native minigame UI and input; fixture coins/berries never provide text.
return function(game)
 io.stdout:setvbuf('line')
 local function wait(n)for _=1,n do coroutine.yield()end end
 local ok,err=xpcall(function()
  local version=require('src.core.GameVersion').get();local rs=version~='emerald'
  if love.setDeprecationOutput then love.setDeprecationOutput(false)end
  local prefix=({ruby='RU_',sapphire='SA_',emerald='EM_'})[version]
  game:_handleBootAction({action='new_game',name='TEST',gender=0,start={map=prefix..'OLDALE_TOWN',x=6,y=17,facing='up'}});wait(60)
  local function capture(name)
   game.capturePath=os.getenv('SHOT_DIR')..'/'..version..'-pt-BR-minigame-'..name..'.png'
   for _=1,600 do if not game.capturePath then break end;wait(1)end;assert(not game.capturePath)
   print('LANGUAGE_MINIGAME_CAPTURE',version,name)
  end
  local function press(k)game:keypressed(k);wait(1);game:keyreleased(k);wait(8)end
  if not rs then
   local Pass=require('src.ui.game3.rse.frontier_pass')
   Pass.show({session=game.session});wait(90);capture('frontier-pass');press('z');wait(150);capture('frontier-card');require('src.ui.game3.trainer_card').close();Pass.reset();wait(10)
  end
  do
   local C=require('src.core.game3.rse.contest')
   local c=C.new({category=0,rank=0});c:setContestants({player={species=1,nickname='BULBASAUR',trainerName='TEST',moves={33,45,73,22},cool=80,beauty=60,cute=40,smart=20,tough=10}});c:init()
   local Contest=require(rs and 'src.ui.game3.rs.contest' or 'src.ui.game3.rse.contest')
   local screen=Contest.open({contest=c,session=game.session})
   local messages={};local startText=screen.startText
   screen.startText=function(self,key,vars,speedy)
    local result=startText(self,key,vars,speedy)
    local text={};for _,tok in ipairs(self.printer.toks)do text[#text+1]=tok.t=='c' and tok.s or '\n'end
    local plain=table.concat(text)
    local line='';local budget=136 -- visible left panel, including the RS port
    local font=require('src.ui.game3.frlg_font')
    for _,tok in ipairs(self.printer.toks)do
     if tok.t=='c' then line=line..tok.s
     elseif tok.t=='nl' or tok.t=='scroll' or tok.t=='para' then
      assert(font.measure(line)<=budget,'Contest text clipped: '..line);line=''
     end
    end
    assert(font.measure(line)<=budget,'Contest text clipped: '..line)
    assert(not plain:find('The standout',1,true) and not plain:find('It tried to',1,true) and not plain:find('coolness',1,true),'Native contest retained English: '..plain)
    messages[#messages+1]={key=type(key)=='string' and key or 'dynamic',text=plain}
    if key=='gText_AppealNumWhichMoveWillBePlayed' then assert(table.concat(text):find(tostring(c.contest.appealNumber+1),1,true),'Contest turn-number placeholder lost')end
    return result
   end
   wait(180);capture('contest')
   local selected=false
   for _=1,800 do
    for _,task in pairs(screen.m.tasks.t)do if task.isActive and task.func==screen.fn.taskHandleMoveSelectInput then selected=true end end
    if selected then break end;press('z')
   end
   assert(selected,'Contest did not reach actual move selection');wait(15);capture('contest-moves')
   for i=1,3 do press('down');capture('contest-move-'..i) end
   local F=require('src.ui.game3.frlg_font')
   local descriptions=require('src.link.Json').decode(assert(io.open(os.getenv('GERMAN_MOD_ROOT')..'/translations/pt-BR/contest-descriptions.json')):read('*a'))
   if rs then
    for id,row in pairs(c.data.effects)do
     assert(row.description==descriptions[tostring(id)],'Untranslated contest description '..id)
     for line in row.description:gmatch('[^\n]+')do assert(F.measure(line,{font='native_3'})<=144,'Contest description too wide '..id..': '..line)end
    end
   end
   if os.getenv('QA_CONTEST_FULL')then
    local shot=false;local lastRound=-1
    for _=1,5000 do
     if screen.done then break end
     if c.contest.appealNumber~=lastRound then lastRound=c.contest.appealNumber;print('LANGUAGE_CONTEST_ROUND',version,lastRound+1)end
     local lines=screen.printer and table.concat(screen.printer.lines,' ') or ''
     if not shot and screen.printer and not screen.printer:isActive() and (lines:find('Tentou assustar',1,true) or lines:find('conter um grito',1,true))then capture('contest-comment');shot=true end
     press('z')
    end
    assert(screen.done and c.contest.appealNumber>=5,'Native contest did not finish all five rounds')
    local f=assert(io.open(os.getenv('SHOT_DIR')..'/'..version..'-contest-dialogues.json','w'));f:write(require('src.link.Json').encode(messages));f:close()
    print('LANGUAGE_CONTEST_COMPLETE',version,c.contest.appealNumber,#messages)
   end
   Contest.reset()
   local Results=require(rs and 'src.ui.game3.rs.contest_results' or 'src.ui.game3.rse.contest_results')
   Results.open({contest=c,session=game.session});wait(180);capture('contest-results');Results.reset();wait(10)
  end
  if os.getenv('QA_CONTEST_ONLY')then print('LANGUAGE_MINIGAMES_OK',version);return end
  local Slots=require(rs and 'src.ui.game3.rs.slot_machine' or 'src.ui.game3.rse.slot_machine')
  local slots=Slots.open({coins=100,machineId=0,session=game.session});wait(180);capture('slots-bet')
  press('down');press('z');wait(90);capture('slots-spin')
  press('z');wait(60);press('z');wait(60);press('z');wait(90);capture('slots-result');Slots.reset();wait(10)
  local Roulette=require('src.ui.game3.rse.roulette')
  Roulette.open({coins=100,session=game.session});wait(180);capture('roulette');Roulette.reset();wait(10)
  require('src.core.game3.bag').add(game.session.bag,133,5)
  local Blender=require(rs and 'src.ui.game3.rs.berry_blender' or 'src.ui.game3.rse.berry_blender')
  local blender=Blender.open({session=game.session,opponents=1,playerName='TEST'});wait(60)
  local start,result=false,false
  for i=1,10000 do
   if blender.cb=='play' and not start then capture('blender-play');start=true end
   if blender.cb=='end' and blender.game.gameEndState>=6 and not result then capture('blender-results');result=true end
   if blender.cb=='play' then
    local best=require('src.core.game3.rse.berry_blender').CMD.BEST
    if blender.game:previewInputScore(true)==best then game:keypressed('z');wait(1);game:keyreleased('z')else wait(1)end
   else
    if blender.yesNo then press('down')end
    press('z')
   end
   if blender.done then break end
  end
  assert(start and blender.game.gameFrameTime>0,'Berry blender did not enter actual gameplay')
  print('LANGUAGE_BLENDER_STATE',blender.cb,blender.game.gameEndState,blender.game.progressBarValue,blender.game.gameFrameTime)
  assert(blender.done and result,'Berry blender did not complete with native results')
  print('LANGUAGE_BLENDER_RESULT',blender.game.gameFrameTime,blender.game.maxRPM)
  Blender.reset()
  print('LANGUAGE_MINIGAMES_OK',version)
 end,debug.traceback)
 if not ok then print('LANGUAGE_MINIGAMES_FAILED',err)end;love.event.quit(ok and 0 or 1)
end
