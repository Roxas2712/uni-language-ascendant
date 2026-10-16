local function wait(n)for _=1,n do coroutine.yield()end end
return function(game)
 local ok,err=xpcall(function()
  if love.setDeprecationOutput then love.setDeprecationOutput(false)end
  local root=os.getenv('GERMAN_MOD_ROOT');local lang=os.getenv('QA_LANGUAGE')
  local e=assert(game.mods.exports.german_rom_source);assert(e.status=='active' and e.language==lang)
  assert(e.coverage.translated==15653 and e.coverage.total==15655)
  local expectedMissing={sCreditsText_NicolaPrattBarlow=true,sCreditsText_RoyalNewZealandFederationBlind=true}
  assert(#e.coverage.missing==2);for _,key in ipairs(e.coverage.missing)do assert(expectedMissing[key],key)end
  local Json=require('src.link.Json');local function read(path)local f=assert(io.open(path,'rb'));local s=f:read('*a');f:close();return s end
  local diffs=Json.decode(read(root..'/build/emerald-1.4.1-diff.json'))[lang]
  local Text=require('src.core.game3.rom_text');local IR=require('src.core.game3.scripting.text_ir')
  local p=dofile(root..'/mod/profiles/emerald_'..lang..'.lua')
  local rom
  for _,v in ipairs(Json.decode(read(root..'/build/emerald-new-language-inputs.json')).roms)do if v.language==lang then rom=read(v.staged_file)end end
  local glyphs=assert(loadfile(root..'/mod/latin_glyphs.lua'))(lang);local previous={}
  for k,v in pairs(glyphs)do previous[k]=IR.CHARMAP[k];IR.CHARMAP[k]=v end
  local function same(a,b)
   if type(a)~=type(b)then return false end
   if type(a)~='table'then return a==b end
   for k,v in pairs(a)do if not same(v,b[k])then return false end end
   for k in pairs(b)do if a[k]==nil then return false end end
   return true
  end
  local checked=0
  local function verify(key)
   local row=assert(p.texts[key]);local expected=IR.decode(rom:sub(row[1]+1,row[1]+16384),{dialect='rse',battle=row[2] or nil})
   assert(same(Text.ir(key),expected),'Runtime text does not match source ROM: '..key);checked=checked+1
  end
  for _,key in ipairs(diffs.added)do verify(key)end
  for key in pairs(diffs.changed)do verify(key)end
  for k in pairs(glyphs)do IR.CHARMAP[k]=previous[k]end
  local examples={fr={'g3:081fe142','g3:0822c73f'},it={'g3:08210cee','g3:08210d48'},es={'g3:0821eafd','g3:0820f3c3'}}
  -- Capture repaired dialogue in the game renderer, with the original IR and
  -- placeholders; this is a focused rendering check, not a full event replay.
  game:_handleBootAction({action='new_game',name='TEST',gender=0,start={map='EM_OLDALE_TOWN',x=6,y=17,facing='up'}});wait(60)
  require('src.ui.game3.map_name_popup').dismiss()
  local key=examples[lang][1];print('FIX_TEXT_SAMPLE',lang,key,Text.plain(key))
  require('src.ui.game3.hud').openMessage(game,Text.ir(key),{speed=0})
  wait(5)
  game.capturePath=os.getenv('SHOT_DIR')..'/'..lang..'-fixed-dialogue.png'
  for _=1,300 do if not game.capturePath then break end;wait(1)end
  assert(not game.capturePath)
  assert(game:saveGame())
  print('TEXT_FIX_OK '..Json.encode({language=lang,checked=checked,translated=e.coverage.translated,missing=e.coverage.missing,cacheHit=e.coverage.cacheHit,seconds=e.loadSeconds}))
 end,debug.traceback)
 if not ok then print('TEXT_FIX_FAILED',err)end
 love.event.quit(ok and 0 or 1)
end
