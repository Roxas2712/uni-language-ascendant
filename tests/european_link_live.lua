-- Two genuine ENet endpoints on localhost. No external relay or account.
local function wait(n)for _=1,n do coroutine.yield()end end
return function(game)
 local host,guest
 local ok,err=xpcall(function()
  local V=require('src.core.GameVersion');local v,gen=V.get(),V.generation()
  local lang=assert(os.getenv('LANGUAGE_SHOT'))
  local Save=require(gen==1 and 'src.core.SaveData' or 'src.core.gen2.Save')
  if gen==1 then game:startNewGame({intro=false})else game:continueGame(Save.newGame({playerName='TEST',trainerId=12345}))end
  local Mon=require(gen==1 and 'src.pokemon.Pokemon' or 'src.battle.gen2.Mon')
  local mon=Mon.new(game.data,'BULBASAUR',15)
  mon.nickname=({es='NIÑO',fr='ÉTÉ',it='CITTÀ'})[lang];mon.ot=mon.nickname;mon.otId=4321
  game.save.party={mon}
  local Net=require('src.link.Net');local Session=require('src.link.Session')
  assert(Net.available(),'LÖVE ENet transport unavailable')
  local a,b=Net.new(),Net.new();local port=38000+math.floor(love.timer.getTime()*1000)%10000
  assert(a:host(port),a.error);assert(b:join('127.0.0.1:'..port),b.error)
  host=Session.new(a,{role='host',kind='link'});guest=Session.new(b,{role='guest',kind='link'})
  for _=1,180 do host:update();guest:update();if host.paired and guest.paired then break end;wait(1)end
  assert(host.paired and guest.paired,'Local ENet pairing timed out')
  local H=require('src.link.Handshake');local P=require('src.link.Protocol')
  local hello=H.hello(game,'trade');assert(H.checkCompat(hello,hello)=='full','Same-profile compatibility rejected')
  host:send(hello)
  guest:send({type='party',mons={gen==1 and P.packMon(mon) or P.packMon2(mon)}})
  local gotHello,received
  for _=1,180 do
   host:update();guest:update()
   for _,msg in ipairs(guest:poll())do if msg.type=='hello'then gotHello=msg end end
   for _,msg in ipairs(host:poll())do if msg.type=='party'then received=msg.mons[1]end end
   if gotHello and received then break end;wait(1)
  end
  assert(gotHello and received,'Local ENet messages missing')
  assert(H.checkCompat(hello,gotHello)=='full','Wire handshake changed compatibility')
  local rebuilt,why=(gen==1 and P.unpackMon or P.unpackMon2)(game.data,received,{strict=true})
  assert(rebuilt,why);assert(rebuilt.nickname==mon.nickname and rebuilt.ot==mon.ot and rebuilt.otId==4321,'Accented identities changed on the wire')
  assert(rebuilt.species==mon.species and rebuilt.level==15 and rebuilt.hp==mon.hp,'Trade rebuild changed mechanics')
  if gen==2 then
   assert(game.mods.exports.german_rom_source.identityCoverage.scriptFields>=2,'Scripted SPEAROW identity fields missing')
   local exports=game.mods.exports.german_rom_source
   local native=assert(require('src.core.SaveSerializer').decode(exports.assets['lang/script_strings.lua']))
   local giftCommand
   for _,commands in pairs(game.data.gen2Scripts)do
    if type(commands)=='table'then for _,cmd in ipairs(commands)do
     if type(cmd)=='table' and cmd.op=='givepoke' and tonumber(cmd.trainer or 0)~=0 then giftCommand=cmd;break end
    end end
   end
   assert(giftCommand and giftCommand.name==native.KENYA and giftCommand.otName==native.RANDY,'SPEAROW script identities')
   assert(game.world.vm:start({giftCommand,{op='end'}}),'Cannot run gift script')
   local spearow=game.save.party[2]
   assert(spearow and spearow.species=='SPEAROW' and spearow.nickname==native.KENYA and spearow.ot==native.RANDY,'Scripted gift did not persist native names')
   if v=='crystal'then
    local vm={specials={party=function()return game.save.party end,save=function()return game.save end,data=function()return game.data end}}
    require('src.script.gen2.Specials').ALL.GiveOddEgg(vm)
    local egg=game.save.party[3];assert(egg and egg.isEgg)
    local hatched=require('src.core.gen2.Breeding').hatch(game.data,game.save,3,nil)
    assert(hatched and not hatched.isEgg and not hatched.nickname and hatched.ot=='TEST' and hatched.otId==12345,'Translated Odd Egg failed to hatch normally')
    assert(hatched.hp==hatched.maxHp and hatched.species==egg.species,'Hatch mechanics changed')
   end
   local Trade=require('src.core.gen2.NpcTrade')
   for _,row in ipairs(game.data.gen2EventTables.trades)do
    local give=Mon.new(game.data,row.give,15)
    local save=Save.newGame({playerName='TEST'});save.party={give}
    local sent,got=Trade.perform(game.data,save,row,1)
    assert(sent==give and got.species==row.get and got.nickname==row.nickname and got.ot==row.otName and got.otId==row.otId,'Native NPC trade identity')
    assert(got.level==give.level and got.item==Trade.item(game.data,row),'Native NPC trade mechanics')
   end
  else
   local Commands=require('src.script.Commands');local Screens=require('src.ui.Screens')
   local original={ask=Commands.ask,show=Commands.show_text,sound=Commands.text_sound,push=Screens.push}
   local fixturesOk,fixturesErr=xpcall(function()
    Commands.ask=function(ctx)ctx.lastCheck=true end
    Commands.show_text=function()end;Commands.text_sound=function()end
    for i,row in ipairs(game.data.field.trades)do
     local given=Mon.new(game.data,row.give,15);game.save.party={given}
     Screens.push=function(g,id,opts)
      if id=='PartyMenu'then opts.onSwitch(given)
      elseif id=='TradeAnim'then require('src.ui.TradeAnim').new(g,opts);opts.onDone()
      else error('Unexpected NPC screen '..id)end
     end
     local ctx={game=game,save=game.save,runner={resume=function()end,yield=function()end}}
     Commands.trade(ctx,i)
     local got=game.save.party[1]
     assert(got.nickname==row.nickname and got.ot=='ENTREN.' and got.species==row.get and got.level==15,'Spanish NPC identity not persisted')
    end
   end,debug.traceback)
   Commands.ask=original.ask;Commands.show_text=original.show;Commands.text_sound=original.sound;Screens.push=original.push
   assert(fixturesOk,fixturesErr)
  end
  -- Strict decoding must refuse unsupported species rather than rename one.
  received.species='MISSING_QA_SPECIES'
  assert(not (gen==1 and P.unpackMon or P.unpackMon2)(game.data,received,{strict=true}),'Unknown trade species accepted')
  print('EUROPEAN_LINK_LIVE_OK',v,lang,'localhost ENet, handshake, accented OT/nickname, strict trade reconstruction, native NPC trade records')
 end,debug.traceback)
 if host then host:close()end;if guest then guest:close()end
 if not ok then print('EUROPEAN_LINK_LIVE_FAILED',err)end
 love.event.quit(ok and 0 or 1)
end
