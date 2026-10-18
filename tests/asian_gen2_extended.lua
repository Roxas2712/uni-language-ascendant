-- Real clerk interaction, purchase, and original menu/intro states.
return function(game,qa)
 local wait,press,capture=qa.wait,qa.press,qa.capture
 local Json=require('src.link.Json');local Bag=require('src.inventory.Bag')
 local function count(id)
  local total=0;for _,row in ipairs(Bag.rows(game.save,game.data))do if row.id==id then total=total+row.count end end;return total
 end
 local Logger=require('src.core.Logger');local originalWarn=Logger.warn
 Logger.warn=function(message,...)
  if message:find('no glyph',1,true)then print(debug.traceback('ASIAN_FONT_CALLSITE'))end
  return originalWarn(message,...)
 end
 local Font=require('src.render.Font');local encode=Font.encode;local stage='purchase';local residual={}
 Font.encode=function(text,...)
  if type(text)=='string'then
   local translated=Font.__ulaEuropeanStrings.localize(text)
   if translated:find('[A-Za-z][A-Za-z]')then residual[stage..' :: '..translated]=true end
  end
  return encode(text,...)
 end
 local world=game.world
 world:setMap('CHERRYGROVE_MART',2,3,'left',{via='boot',continue=true});wait(60);world:interact();wait(90)
 local mart=game.stack:top();assert(mart.phase=='top'and mart.martType=='STANDARD','Actual clerk did not open mart')
 capture('mart-welcome');press('z',10);assert(mart.phase=='buy')
 while mart:selected().id~='POTION'do press('down',4)end
 local entry=mart:selected();local oldCount=count('POTION');local oldMoney=mart:money()
 press('z',10);assert(mart.phase=='buyQuantity');press('up',4);press('up',4);assert(mart.qty==3)
 press('z',90);assert(mart.confirm,'Purchase confirmation absent');capture('mart-price')
 local rendered={};for _,page in ipairs(mart.confirm.pages)do rendered[#rendered+1]=table.concat(page,'\n')end
 local body=table.concat(rendered,'\f');local total=3*entry.price
 print('ASIAN_REAL_MART_PRICE',Json.encode({text=body,quantity=3,item=entry.name,total=total}))
 -- Independent native decode with semantic roles, not a synthetic textbox.
 local expected=qa.expected._MartFinalPriceText;local fields={entry.name,3,total};local index=0
 expected=expected:gsub('{(%u+)}',function(token)
  if token=='DONE'or token=='PROMPT'then return ''end
  if token=='NUM'or token=='STRBUF'then index=index+1;return tostring(fields[index])end
  return '{'..token..'}'
 end)
 local pages=require('src.core.gen2.CommonText').pages(expected);local compare={}
 for _,page in ipairs(pages)do compare[#compare+1]=table.concat(page,'\n')end
 assert(body==table.concat(compare,'\f'),'Native price fields changed: '..body)
 while mart.confirm.page<#mart.confirm.pages do press('z',20)end
 wait(90);capture('mart-price-final')
 for _=1,40 do if mart:money()~=oldMoney then break end;press('z',8)end
 assert(mart:money()==oldMoney-total and count('POTION')==oldCount+3,'Purchase state differs')
 wait(90);capture('mart-thanks');print('ASIAN_REAL_PURCHASE_OK',qa.version,total)
 game.save.flags=game.save.flags or {};game.save.flags.EVENT_GOT_POKEDEX=true
 game.save.engineFlags=game.save.engineFlags or {};game.save.engineFlags.ENGINE_POKEDEX=true
 game.save.pokegearFlags={map=true,phone=true,radio=true}
 local function show(name,tag,opts)
  stage=tag;print('ASIAN_MENU_STAGE',tag);game.stack:clear();local state=require(name).new(game,opts);game.stack:push(state);wait(50);capture(tag);return state
 end
 show('src.ui.gen2.StartMenu','start',{unlocked={pokedex=true,pokemon=true,pack=true,pokegear=true,player=true,save=true,option=true}})
 local options=show('src.ui.OptionsMenu','options')
 for i,row in ipairs(options:visible())do
  if row.group then
   options.index=i;options:ensureVisible();press('z',4)
   local page=game.stack:top();assert(page~=options and page.sub,'Option group did not open')
   for n in ipairs(page:visible())do
    page.index=n;page:ensureVisible();stage='options-'..row.id;wait(2)
    if n==1 or n==#page:visible()then capture(stage..'-'..n)end
   end
   press('x',4);assert(game.stack:top()==options,'Option group did not close')
  end
 end
 show('src.ui.gen2.PartyMenu','party',{party=game.save.party})
 local originalParty=game.save.party;local six={};local Mon=require('src.battle.gen2.Mon')
 for i=1,6 do
  six[i]=Mon.new(game.data,'BULBASAUR',100);six[i].nickname=qa.lang=='ja'and 'テストテス'or '테스트테스';six[i].status='PSN'
 end
 game.save.party=six
 local party=show('src.ui.gen2.PartyMenu','party-six',{party=six,submenu=true})
 for _=1,5 do press('down',3)end
 assert(party.index==6,'Sixth party member inaccessible');capture('party-six-last')
 press('z',10);assert(party.submenu,'Field party submenu absent');capture('party-submenu');press('x',5)
 press('down',3);assert(party.index==7,'Party cancel inaccessible');capture('party-six-cancel')
 show('src.ui.gen2.PartyMenu','party-tm',{party=six,tmhm={move='CUT'}})
 local battleParty=show('src.ui.gen2.PartyMenu','party-battle',{party=six,battle=true,battleSubmenu=true})
 press('z',10);assert(battleParty.submenu and battleParty.submenu.battle,'Battle party submenu absent');capture('party-battle-submenu')
 game.save.party=originalParty
 for _,pocket in ipairs({'ITEM','BALL','KEY_ITEM','TM_HM'})do show('src.ui.gen2.PackMenu','pack-'..pocket:lower(),{pocket=pocket})end
 local pack=show('src.ui.gen2.PackMenu','pack-actions',{pocket='ITEM'})
 for _=1,#pack.rows do if pack.rows[pack.index]and pack.rows[pack.index].id=='POTION'then break end;press('down',3)end
 assert(pack.rows[pack.index].id=='POTION');press('z',10);assert(pack.submenu);capture('pack-submenu')
 for _=1,#pack.submenu.rows do if pack.submenu.rows[pack.submenu.index]=='toss'then break end;press('down',3)end
 assert(pack.submenu.rows[pack.submenu.index]=='toss');local beforeToss=count('POTION')
 press('z',10);assert(pack.qtyState);press('z',90);assert(pack.confirm);capture('pack-toss-confirm')
 press('x',10);assert(not pack.confirm and count('POTION')==beforeToss,'Cancelled toss changed inventory')
 local card=show('src.ui.gen2.TrainerCard','trainer');card.page=2;capture('badges')
 local gear=show('src.ui.gen2.Pokegear','gear')
 for i,entry2 in ipairs(gear.cards)do gear.cardIndex=i;capture('gear-'..entry2.id)end
 game.save.pokedex.seen.BULBASAUR=true;game.save.pokedex.caught.BULBASAUR=true
 local dex=show('src.ui.gen2.PokedexMenu','dex-main')
 press('rshift',8);assert(dex.view=='option','Dex option input failed');capture('dex-option');press('x',8)
 press('escape',8);assert(dex.view=='search','Dex search input failed');capture('dex-search');press('x',8)
 show('src.ui.gen2.PokedexMenu','dex-entry',{entrySpecies='BULBASAUR'})
 show('src.ui.gen2.Diploma','diploma')
 show('src.ui.gen2.BoxMenu','pc',{mode='withdraw'})
 local pc=show('src.ui.gen2.BoxMenu','pc-deposit',{mode='deposit'})
 press('z',90);assert(pc.phase=='submenu','Actual PC selection did not open its submenu');capture('pc-submenu')
 for page=1,3 do show('src.ui.gen2.SummaryMenu','summary-'..page,{mon=game.save.party[1],page=page})end
 -- Exercise the actual status branch, without injecting a label or dialogue.
 local mon=game.save.party[1];local oldPokerus=mon.pokerus;mon.pokerus=0x11
 local infected=show('src.ui.gen2.SummaryMenu','summary-pokerus',{mon=mon,page=1})
 local statusRows=0
 for _,placement in ipairs(infected:pinkPlacements())do
  if placement.y==12 and placement.x<10 and placement.text~=''then
   statusRows=statusRows+1;assert(placement.x==0,'Native Pokerus label misplaced')
  end
 end
 assert(statusRows==1,'Native Pokerus status overlaps another label')
 mon.pokerus=oldPokerus
 if os.getenv('QA_MODE')=='menus'then
  Font.encode=encode;Logger.warn=originalWarn
  for key in pairs(residual)do print('ASIAN_VISIBLE_LATIN',Json.encode({text=key}))end
  print('ASIAN_REAL_MENUS_OK',qa.version);return
 end
 -- Traverse the normal clock/gender/Oak flow with actual input.
 local Box=require('src.render.TextBox');local original=Box.new;local heard={};local shots={}
 Box.new=function(g,text,...)
  heard[text]=true;print('ASIAN_REAL_INTRO_DIALOGUE',Json.encode({text=text}));return original(g,text,...)
 end
 stage='intro';game:showOakSpeech()
 for _=1,1400 do
  for _,label in ipairs({'_OakText1','_OakText2','_OakText4','_OakText5','_OakText6'})do
   if heard[qa.expected[label]]and not shots[label]then wait(60);capture(label:sub(2):lower());shots[label]=true end
  end
  if shots._OakText6 then break end
  press('z',4)
 end
 Box.new=original
 for _,label in ipairs({'_OakText1','_OakText2','_OakText4','_OakText5','_OakText6'})do assert(shots[label],'Real intro did not show '..label)end
 Font.encode=encode
 for key in pairs(residual)do print('ASIAN_VISIBLE_LATIN',Json.encode({text=key}))end
 Logger.warn=originalWarn
 print('ASIAN_REAL_INTRO_OK',qa.version)
end
