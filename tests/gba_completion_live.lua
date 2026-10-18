local function wait(n) for _=1,n do coroutine.yield() end end
local function read(path) local f=assert(io.open(path,'rb'));local s=f:read('*a');f:close();return s end
local function same(a,b)
 if type(a)~=type(b)then return false end
 if type(a)~='table'then return a==b end
 for k,v in pairs(a)do if not same(v,b[k])then return false end end
 for k in pairs(b)do if a[k]==nil then return false end end
 return true
end
return function(game)
 local ok,err=xpcall(function()
  if love.setDeprecationOutput then love.setDeprecationOutput(false)end
  local root=assert(os.getenv('GERMAN_MOD_ROOT'))
  local version=require('src.core.GameVersion').get()
  local lang=assert(os.getenv('QA_LANGUAGE'));local mode=assert(os.getenv('QA_MODE'))
  local frlg=version=='firered' or version=='leafgreen'
  local S=require('src.core.Strings');local IR=require('src.core.game3.scripting.text_ir')
  local e=game.mods.exports.german_rom_source
  local Jump=frlg and require('src.core.game3.minigames.pokemon_jump.game')
  if mode=='english' or mode=='disabled' then
   assert(mode=='disabled' and not e or mode=='english' and e.status=='english','Lifecycle activation')
   assert(S('The connection failed.')=='The connection failed.','English UI not restored')
   if Jump then assert(Jump.prizeItemName(133,2,'CHERI BERRY')=='CHERI BERRIES','English prize plural')end
   print('GBA_COMPLETION_OK',version,lang,mode);return
  end
  assert(e and e.status=='active' and e.language==lang,'Wrong active profile')
  assert(e.coverage.cacheHit==(mode=='warm'),'Unexpected compiler cache state')
  assert(#e.coverage.missing==0,'Unaccounted English native text keys')
  assert(e.coverage.covered==e.coverage.total,'Coverage categories do not sum')
  local ui=dofile(root..'/mod/gba/ui.lua')[lang]
  local entry
  for _,row in ipairs(dofile(root..'/mod/catalog.lua'))do if row.game==version and row.language==lang then entry=row end end
  local profile=dofile(root..'/mod/'..entry.profile)
  if lang=='fr' and version=='emerald' then
   local native=require('src.core.game3.rom_text').plain('gText_WonderNews')
   assert(S("You already have this WONDER NEWS."):find(native,1,true),'Wonder News terminology differs from regional ROM')
  end
  local base=dofile(love.filesystem.getSaveDirectory()..'/'..version..'/data/generated/gba/scripts/text.lua')
  for _,key in ipairs(e.coverage.retainedProperNames)do
   assert(same(require('src.core.game3.rom_text').ir(key),base[key]),'Altered credit identity '..key)
  end
  for _,key in ipairs(e.coverage.inapplicable)do
   assert(require('src.core.game3.rom_text').plain(key)=='','Unused English suffix still present')
  end
  for _,key in ipairs(e.coverage.authored)do
   assert(require('src.core.game3.rom_text').plain(key)~=(IR.toPlain(base[key],{})),'Untranslated credit role '..key)
  end
  local F=require('src.ui.game3.frlg_font');local Message=require('src.ui.game3.message')
  local rendered,nativeOverrides=0,0
  local canvas=love.graphics.newCanvas(240,160)
  local function fontCheck(text,where)
   for kind,value in F.scanTokens(text)do
    if kind=='char' and value~=' ' then assert(F.glyphId(value)~=0,'Missing glyph '..value..' in '..where)end
   end
  end
  for source,target in pairs(ui)do
   local actual=S.lookup(source)
   assert(game.data.strings[source]~=nil,'Authored GBA key was not registered '..source)
   if actual~=target then nativeOverrides=nativeOverrides+1 end
   -- Real formatting with accented, maximum cartridge-length player names.
   local args={}
   for spec in source:gmatch('%%([-+ #0-9%.]*[a-zA-Z])')do args[#args+1]=spec:sub(-1)=='s' and 'ÁLVARO7' or 7 end
   local text=S(source,unpack(args));fontCheck(text,source)
   assert(not text:find('%s',1,true),'Unexpanded format '..source)
   love.graphics.push('all');love.graphics.setCanvas(canvas);love.graphics.clear(1,1,1,1)
   F.draw(F.wrap(text:gsub('\f','\n'),216),4,0);love.graphics.pop()
   -- Test the actual textbox conversion/paginator, not an independent wrapper.
   Message.show(text,{speed=0})
   if Message._pages then
    for _,page in ipairs(Message._pages)do
     for line in tostring(page):gmatch('[^\n]+')do assert(F.measure(line)<=224,'Message clips '..source..': '..line)end
    end
   end
   Message.close();rendered=rendered+1
  end
  assert(require('src.render.Zoom').offsetLabel(3)=='+3' and require('src.render.Zoom').offsetLabel(-2)=='-2','Zoom labels')
  for _,source in ipairs({'{DPAD_UPDOWN}PICK {A_BUTTON}OK {B_BUTTON}BACK','{A_BUTTON}SET {SELECT_BUTTON}CLEAR {START_BUTTON}RESET {B_BUTTON}BACK'})do
   assert(require('src.ui.game3.pokedex_chrome').measureControlInfo(S(source))<=228,'Controls help clips '..source..': '..require('src.ui.game3.pokedex_chrome').measureControlInfo(S(source)))
  end
  local Rows=require('src.ui.game3.option_rows')
  local options={};for k,v in pairs(game.options or {})do options[k]=v end
  local seen={};local lookup=S.lookup
  S.lookup=function(source,context)if not context then seen[source]=true end;return lookup(source,context)end
  local context={options=options,game=game,session=game.session}
  local skip
  if not frlg then skip={} for _,key in ipairs({'textSpeed','battleScene','battleStyle','sound','buttonMode','frameType'})do skip[key]={id=key}end end
  local rows=Rows.build(context,skip)
  local grouped=Rows.group(rows,function()end)
  assert(grouped[1].label==ui.SPEED,'Stat abbreviation leaked into speed settings')
  require('src.ui.BindingsMenu').new({save={options={}}},{buttons=require('src.ui.BindingsMenu').GEN3_BUTTONS})
  for _,row in ipairs(rows)do if row.value then row.value(context)end end
  local gifts=require('src.core.game3.mystery_gift').builtins(frlg and 'frlg' or 'rse')
  S.lookup=lookup
  local nativeValues={}
  for _,ir in pairs(game.data.text or {})do if type(ir)=='table' then nativeValues[IR.toPlain(ir,{})]=true end end
  local gaps={}
  for source in pairs(seen)do
   if not (ui[source] or nativeValues[source] or source:match('^%d') or source:match('^[+-]?%d+%%$'))then gaps[#gaps+1]=source;print('GBA_DYNAMIC_GAP',source)end
  end
  assert(#gaps==0,'Uncataloged dynamic GBA UI')
  for _,gift in ipairs(gifts)do
   local card=gift.card
   if card then
    assert(F.measure(card.titleText)<=200,'Card title clips '..card.titleText)
    for _,line in ipairs(card.bodyText or {})do assert(F.measure(line)<=224,'Card body clips '..line..' ('..F.measure(line)..')')end
    for _,key in ipairs({'footerLine1Text','footerLine2Text'})do assert(F.measure(card[key] or '')<=224,'Card footer clips')end
   end
  end
  print('GBA_UI_RENDER_OK',rendered,nativeOverrides,'native pairs take precedence',#gifts,'cards')
  local rom=read(assert(os.getenv('QA_ROM')))
  local assetProfile=dofile(root..'/mod/'..entry.assets)
  local metadata=assetProfile.fields
  local function u32(off)local a,b,c,d=rom:byte(off+1,off+4);return a+b*256+c*65536+d*16777216 end
  local function ptr(off)return u32(off)-0x08000000 end
  local old={};local glyphs=entry.glyphsPath and assert(loadfile(root..'/mod/'..entry.glyphsPath))(lang) or entry.glyphs or {[0x15]='ß',[0xF1]='Ä',[0xF2]='Ö',[0xF3]='Ü',[0xF4]='ä',[0xF5]='ö',[0xF6]='ü'}
  for k,v in pairs(glyphs)do old[k]=IR.CHARMAP[k];IR.CHARMAP[k]=v end
  local function plain(off)return IR.toPlain(IR.decode(rom:sub(off+1,off+256),{dialect=IR.dialectOf(version)}),{})end
  local creditRows=0
  if frlg then
   local C=metadata.CREDITS
   local pack=require('src.ui.game3.rse.scene_kit').loadLua('data/generated/gba/credits/pack.lua')
   for id=0,C.text_count-1 do
    local row=assert(pack.texts[id]);local off=C.texts+id*12
    assert(row.title==plain(ptr(off)) and row.names==plain(ptr(off+4)),'Native FRLG credit row '..id)
    creditRows=creditRows+1
   end
  else
   local rs=version=='ruby' or version=='sapphire'
   local C=metadata.CREDITS_RSE
   if rs then
    local syms=assetProfile.symbols
    local name=syms.has['credits.o:gCreditsEntryPointerTable'][1] and 'credits.o:gCreditsEntryPointerTable' or 'gCreditsEntryPointerTable'
    C={pages=syms.off[name][1],pageCount=syms.count[name..'\t20'][1],entriesPerPage=5}
   end
   local M=require('src.ui.game3.rse.gba_machine').new()
   local pages=M:manifest('data/generated/gba/credits_rse/manifest.lua').pages
   for p=0,C.pageCount-1 do for i=0,C.entriesPerPage-1 do
    local entryPtr=ptr(C.pages+(p*C.entriesPerPage+i)*4)
    local text=plain(ptr(entryPtr+4))
    local row=assert(pages[p+1][i+1])
    local off=ptr(entryPtr+4)
    local isTitle=rs and (rom:byte(off+1)==0xFC and rom:byte(off+2)==3 and rom:byte(off+3)==9) or not rs and rom:byte(entryPtr+2)~=0
    assert(row.text==text and row.isTitle==isTitle,'Native RSE credit row '..p..'/'..i)
    creditRows=creditRows+1
   end end
  end
  for k in pairs(glyphs)do IR.CHARMAP[k]=old[k]end
  print('GBA_NATIVE_CREDITS_OK',creditRows)
  local Pokemon=require('src.core.game3.pokemon')
  local stats=dofile(love.filesystem.getSaveDirectory()..'/'..version..'/data/generated/gba/pokemon/stats.lua')
  assert(same(Pokemon._stats,stats),'Battle species stats changed')
  local map=frlg and 'FR_VIRIDIAN_CITY' or ({ruby='RU_',sapphire='SA_',emerald='EM_'})[version]..'OLDALE_TOWN'
  game:_handleBootAction({action='new_game',name='ÁLVARO7',gender=0,start={map=map,x=frlg and 26 or 6,y=frlg and 27 or 17,facing='up'}})
  wait(45)
  if Jump then
   local VM=require('src.core.game3.scripting.vm');local Ops=require('src.core.game3.scripting.ops_a');local Flags=require('src.core.game3.scripting.flags')
   local Items=require('src.core.game3.items_data')
   local vm=VM.new()
   for _,item in ipairs({4,13,133,175})do for _,qty in ipairs({1,2,99})do
    for _,dest in ipairs({0,1,2})do
     Flags.setVar(vm.store,vm.ctx,0x8000,item);Flags.setVar(vm.store,vm.ctx,0x8001,qty)
     assert(Ops.dispatch(vm,{op='bufferitemnameplural',dest=dest,[2]=0x8000,[3]=0x8001})==false)
     assert(vm.ctx.stringVars[dest+1]==Items.displayName(item),'Localized item corrupted by plural suffix')
     assert(Jump.prizeItemName(item,qty,Items.displayName(item))==Items.displayName(item),'Localized minigame prize plural')
    end
   end end
   local Runtime=require('src.mods.Runtime');local bus=Runtime.events
   Runtime.events={}
   assert(Jump.prizeItemName(133,2,'CHERI BERRY')=='CHERI BERRIES','Wrapper leaked across event bus')
   Runtime.events=bus
   print('GBA_REGIONAL_PLURAL_OK',36,'VM cases and prizes; bus guard')
  end
  assert(require('src.core.game3.party').giveMon(game.session,1,15,nil,{fixedPersonality=0}))
  game.session.party[1].nickname='CUSTOM'
  local SMenu=require('src.ui.game3.summary_menu');SMenu.openMenu(game.session.party,1,{session=game.session,page=1});wait(12);SMenu.close()
  local opts=require('src.ui.game3.screens').get('option',game.session);opts.show({game=game,session=game.session});wait(12)
  game.capturePath=os.getenv('SHOT_DIR')..'/'..version..'-'..lang..'-gba-options.png'
  for _=1,600 do if not game.capturePath then break end;wait(1)end
  assert(not game.capturePath,'Capture timed out');opts.close()
  assert(game:saveGame(),'GBA save failed')
  local saved=assert(require('src.core.SaveData').load());assert(saved.engine=='game3')
  assert(game.session.party[1].nickname=='CUSTOM','Player nickname changed')
  print('GBA_COMPLETION_REPORT '..require('src.link.Json').encode({game=version,language=lang,mode=mode,total=e.coverage.total,translated=e.coverage.translated,covered=e.coverage.covered,authored=e.coverage.authored,retainedProperNames=e.coverage.retainedProperNames,inapplicable=e.coverage.inapplicable,missing=e.coverage.missing,uiKeys=rendered,nativeStringOverrides=nativeOverrides,creditRows=creditRows,cacheKey=e.cacheKey}))
  print('GBA_COMPLETION_OK',version,lang,mode)
 end,debug.traceback)
 if not ok then print('GBA_COMPLETION_FAILED',err)end
 love.event.quit(ok and 0 or 1)
end
