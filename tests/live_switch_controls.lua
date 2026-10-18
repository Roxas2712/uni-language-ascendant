-- Exercise the real menu adapters and importer; never supplies game dialogue.
return function(game,capture)
 local function wait(n)for _=1,n do coroutine.yield()end end
 local e=game.mods.exports.german_rom_source;local S=e.session
 local Runtime=require('src.mods.Runtime');local generation=require('src.core.GameVersion').generation()
 local host=game.mods.exports.ORIGAMI_ASCENDANT
 if host and host.gen3 and host.gen3.menu then
  local m=host.gen3.menu;local screen=assert(m.open(S.game));local row
  for _,r in ipairs(screen.items)do if r.label=='UNI-LANGUAGE'then assert(not row);row=r end end
  assert(row,'missing Origami language entry');row.choose();assert(S.opened and not m.active())
  print('LIVE_MENU_ROUTE_OK','Origami Ascendant')
 else
  local items=Runtime.call('ui.start_menu.items',function(_,x)return x end,S.game,{{label='SAVE',onSelect=function()end}})
  local hub;for _,r in ipairs(items)do if r.label=='ASCENDANT'then assert(not hub,'duplicate hub');hub=r end end;assert(hub)
  local k=game.mods.exports.kanto_ascendant;local a=k and k.ascendantMenu
  if a then
   local original=a.open;local rows;a.open=function(_,r)rows=r end;hub.onSelect();a.open=original
   assert(rows,'KASC did not collect entries');local found
   local root=a.buildRoot and a.buildRoot(rows)or rows
   for _,r in ipairs(root)do if r.ascendantKey=='uni_language_ascendant'then assert(not found);found=r end end
   assert(found,'KASC lost the root language entry');original(S.game,rows);wait(3);capture('ascendant-root');found.onSelect();assert(S.opened)
   print('LIVE_MENU_ROUTE_OK','Kanto Ascendant',#rows)
  else
   hub.onSelect();assert(S.opened and S.page=='hub');local index
   for i,r in ipairs(S.hubRows)do if r.ascendantKey=='uni_language_ascendant'then index=i end end
   assert(index);S.index=index;S:key('return');assert(S.opened and S.page=='home')
   print('LIVE_MENU_ROUTE_OK','fallback hub',#S.hubRows)
  end
 end
 wait(3);capture('language-menu')
 S.page='game';S.index=1;wait(2);capture('language-choices')
 local count=0;for _,row in ipairs(S:choices())do count=count+1;if not row.supported then assert(not row.available)end end;assert(count==10)
 for _,id in ipairs({'en','de','fr','it','es','ja','ko','zh-Hans','zh-Hant','pt-BR'})do
  assert(S:menuLanguage(id));S.page='menu';S.index=10;wait(2);assert(S.uiLanguage==id)
  if id=='ja' or id=='ko' or id=='zh-Hant'then capture('ui-'..id)end
 end
 assert(S:menuLanguage('en'));S.page='home';S.index=1;S:back();assert(not S.opened)
 assert(not S:importBytes('wrong ROM'),'bad ROM accepted')
 local rows=S:choices();local selected
 for _,row in ipairs(rows)do if row.id=='de' and row.available then selected=row end end;assert(selected)
 local imported=assert(game.mods.mods.german_rom_source.manifest.optional_imports);local spec
 for _,r in ipairs(imported)do if r.id==selected.importId then spec=r end end;assert(spec)
 local Cache=require('src.import.CacheFs');local old=Cache.prefix;Cache.prefix=''
 local path='mods/german_rom_source/baseroms/'..spec.file;local bytes=assert(Cache.read(path));Cache.remove(path);assert(not Cache.read(path));Cache.prefix=old
 for _,r in ipairs(S:choices())do if r.id=='de'then assert(not r.available)end end
 assert(not S:request('de'),'missing ROM selectable')
 local ok,id=S:importBytes(bytes);assert(ok and id=='de',tostring(id))
 for _,r in ipairs(S:choices())do if r.id=='de'then assert(r.available)end end
 print('LIVE_IMPORT_OK',selected.importId,#bytes)
 assert(S:canSwitch())
 game.capturePath='qa_busy';assert(not S:request('de'));game.capturePath=nil
 assert(S:canSwitch());print('LIVE_CONTROLS_OK',generation,'10 UI languages; disabled choices; import; unsafe capture refusal')
end
