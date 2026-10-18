local root=assert(arg[1])
local factory=dofile(root..'/mod/startup.lua')
local function check(opts)
 local store={['preferences/ascendant-intro-v1.txt']='seen',['preferences/notice.txt']='accepted'}
 store['preferences/'..(opts.game or 'red')..'.txt']=opts.saved
 local schema
 local selected,events={},{}
 local saves=0
 local game={draw=function() end,update=function() end,mods={modOptions={}},options={}}
 local originalUpdate=game.update
 local Save={loadOptions=function() return {unrelated='keep',modOptions={other={x=7}}} end,defaultOptions=function()return {}end,
  saveOptions=function(value) assert(value.unrelated=='keep' and value.modOptions.other.x==7);saves=saves+1;return true end}
 local restarts=0
 local Runtime={events={}}
 Runtime.wants=function()return true end
 package.loaded['src.core.SaveData']=Save
 package.loaded['src.core.HostShell']={restart=function()restarts=restarts+1 end}
 package.loaded['src.mods.Runtime']=Runtime
 local mod={id='test',game=game,exports={},options={define=function(_,value)schema=value end,get=function(_,k)return opts[k]end},
  imports={info=function(_,id)return opts[id] or nil end},
  cache={read=function(_,k)return store[k]end,write=function(_,k,v) if opts.fail then return nil,'disk full' end;store[k]=v;return true end},
  events={on=function(_,k,fn)events[k]=fn end}}
 local cat={{game='red',language='de',name='Deutsch',id='de'},{game='red',language='fr',name='Français',id='fr'},
  {game='emerald',language='es',name='Español',id='es'},
  {game='red',language='de',name='Deutsch (alternate revision)',id='de_alt'}}
 if opts.realCatalog then cat=dofile(root..'/mod/catalog.lua') end
 local language=factory(mod,opts.game or 'red',function(file)
  if file=='preferences.lua' then return function(mod)mod.cache.reset=function()for k in pairs(store)do store[k]=nil end;return not opts.fail end;return mod.cache end end
  if file=='intro.lua' then return dofile(root..'/mod/intro.lua') end
  if file=='locales.lua' then return dofile(root..'/mod/locales.lua') end
  if file=='options_schema.lua' then return dofile(root..'/mod/options_schema.lua') end
  if file=='startup_view.lua' then return function()return function()end end end
  if file=='catalog.lua' then return cat end
  if file=='rom_requirements.lua' then return {{game='red'}} end
  return {}
 end)
 mod.exports.language=language;mod.exports.status=language=='en' and 'english' or 'active'
 events['game.ready']()
 local ui=mod.exports.startup
 return {ui=ui,language=language,game=game,original=originalUpdate,store=store,schema=schema,restarts=function()return restarts end,saves=function()return saves end,events=events}
end
local a=check({language='auto'})
assert(a.ui.stage=='menu' and a.ui.chooseMenu('ja') and a.ui.stage=='game' and a.store['preferences/ui-language.txt']=='ja')
assert(not a.ui.chooseMenu('bad'))
assert(a.language=='en' and a.ui.open,'fresh install must show language screen without German')
assert(#a.ui.choices==10 and #a.schema[1].choices==2,'unavailable languages must be visible only in the picker')
assert(not a.ui.choose('de') and a.restarts()==0,'missing source accepted')
assert(not a.ui.choose('unknown'),'unknown language accepted')
assert(a.ui.choose('en') and not a.ui.open and a.game.update==a.original,'callbacks not restored')
local b=check({language='en',de=true,fr=true})
assert(#b.ui.choices==10,'additional profile language omitted')
assert(b.ui.choose('fr') and b.restarts()==1 and b.store['preferences/red.txt']=='fr','language switch not persisted')
local c=check({language='de',de=true,fail=true})
assert(not c.ui.choose('en') and c.restarts()==0 and c.ui.open,'restarted after failed persistence')
local d=check({language='en',showPicker=false})
assert(not d.ui.open and d.game.update==d.original,'disabled picker wraps gameplay')
local e=check({language='en',de=true});e.ui.chooseMenu('de');e.ui.stage='menu';e.ui.previewLocale('ja');assert(e.ui.back() and e.ui.uiLanguage=='de' and e.ui.stage=='game')
assert(#e.ui.choices==10 and #e.schema[1].choices==3,'launcher must contain only imported languages')
assert(e.ui.choices[2].id=='de' and e.schema[1].choices[3][2]=='de')
assert(e.ui.back() and e.ui.stage=='menu');assert(e.ui.requestReset() and e.ui.stage=='reset');assert(e.ui.back() and e.ui.stage=='menu');assert(e.restarts()==0)
assert(e.ui.requestReset());e.ui.resetIndex=2;assert(e.ui.confirm() and e.restarts()==1 and next(e.store)==nil)
local f=check({language='auto',saved='fr',de=true,es=true})
assert(f.language=='en' and #f.ui.choices==10 and #f.schema[1].choices==3,'missing saved ROM or other-game import leaked into choice')
assert(f.store['preferences/red.txt']=='fr','fallback must not erase the stored preference')
local g=check({language='fr',de_alt=true})
assert(g.language=='en' and #g.ui.choices==10 and g.ui.choices[2].id=='de','override fallback or alternate imported revision failed')
local h=check({de=true,de_alt=true})
assert(#h.ui.choices==10,'duplicate language revisions shown')
for _,id in ipairs({'en','de','fr','it','es','ja','ko','zh-Hans','zh-Hant','pt-BR'}) do
 assert(f.ui.chooseMenu(id),'menu locale hidden with missing game ROM: '..id)
end
f.ui.stage='menu';f.ui.uiIndex=1
assert(f.ui.pageMenu(1) and f.ui.uiLanguage=='pt-BR' and f.ui.uiIndex==10)
assert(f.ui.confirm() and f.store['preferences/ui-language.txt']=='pt-BR')
assert(f.ui.back() and f.ui.stage=='menu')
assert(f.ui.pageMenu(1) and f.ui.uiIndex==1 and f.ui.uiLanguage=='en')
assert(f.ui.pageMenu(-1) and f.ui.uiIndex==10)
local locales=dofile(root..'/mod/locales.lua')
for key in pairs(locales.en) do assert(type(locales['pt-BR'][key])=='string',key) end
print('STARTUP_UNIT_OK per-game/import filtering, saved/override fallback, alternate revisions, ten menu locales, persistence, restart, callback restoration, disk failure')

local function choice(ui,id) for i,c in ipairs(ui.choices) do if c.id==id then return c,i end end end
assert(choice(a.ui,'de').supported and not choice(a.ui,'de').available)
assert(not choice(a.ui,'es').supported and not choice(a.ui,'es').available)
for _,game in ipairs({'red','blue','yellow','gold','silver','crystal','ruby','sapphire','emerald','firered','leafgreen'}) do
 local imports={game=game,realCatalog=true,language='en'}
 for _,row in ipairs(dofile(root..'/mod/catalog.lua')) do imports[row.sourceId or row.id]=true end
 local test=check(imports);test.ui.chooseMenu('de')
 local available=0
 for i,c in ipairs(test.ui.choices) do
  local extra={red={es=true},yellow={es=true},gold={es=true,fr=true,it=true},silver={es=true,fr=true},crystal={es=true,it=true},firered={es=true,it=true},leafgreen={es=true,fr=true},emerald={es=true,fr=true,it=true}}
  local expected=c.id=='en' or c.id=='de' or c.id=='pt-BR' or (extra[game] or {})[c.id]==true
  assert(c.available==expected,game..'/'..c.id)
  if expected then available=available+1 else
   test.ui.index=i
   test.game:keypressed('return');test.game:gamepadpressed(nil,'a')
   assert(test.ui.noticeKey=='unavailable' and test.saves()==0 and test.restarts()==0 and test.ui.open)
  end
 end
 assert(#test.schema[1].choices==available+1)
end
local missing=check({language='en'});missing.ui.chooseMenu('en');missing.ui.index=2
missing.game:keypressed('return')
assert(missing.ui.noticeKey=='missing' and missing.saves()==0 and missing.restarts()==0)
assert(choice(g.ui,'de').available,'alternate revision must enable the language')
local shared=check({game='sapphire',realCatalog=true,ruby_ptbr=true})
assert(choice(shared.ui,'pt-BR').available,'Sapphire shared source must enable PT-BR')
for id,strings in pairs(locales) do for key in pairs(locales.en) do assert(type(strings[key])=='string',id..'/'..key) end end
print('DISABLED_LANGUAGES_UNIT_OK all 11 editions, missing imports, unsupported profiles, keyboard/controller rejection, shared source, ten locale keys')
