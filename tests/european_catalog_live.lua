-- Exercise the actual imported raster font and TextBox paginator for every
-- supplemental string, plus native descriptions and all Pokédex pages.
return function(game)
 local ok,err=xpcall(function()
  local root=assert(os.getenv('GERMAN_MOD_ROOT'))
  local lang=assert(os.getenv('LANGUAGE_SHOT'))
  local version=require('src.core.GameVersion').get()
  local gen=require('src.core.GameVersion').generation()
  local exports=assert(game.mods.exports.german_rom_source)
  assert(exports.status=='active' and exports.language==lang)
  local f=assert(io.open(root..'/translations/european/gb-ui.json'));local ui=require('src.link.Json').decode(f:read('*a'));f:close()
  local Font=require('src.render.Font');local TextBox=require('src.render.TextBox')
  local ix=({es=1,fr=2,it=3})[lang]
  local gaps,lines,keys={},0,0
  local function fontCheck(text,where)
   for _,span in ipairs(Font.split(text))do
    if not span.code and text:byte(span.from)>=32 then gaps[text:sub(span.from,span.to)..' in '..where]=true end
   end
  end
  local function sample(text)
   return (text:gsub('%%[-+ #0-9%.]*[a-zA-Z]',function(t)return t:sub(-1)=='s' and 'TEST' or '7' end)
    :gsub('{[^}]+}','TEST'):gsub('<NEXT>','\n'):gsub('%%',''))
  end
  for key,values in pairs(ui)do
   local text=assert(game.data.strings[key],key)
   assert(text==values[ix],'Compiled string differs from reviewed source: '..key)
   text=sample(text)
   if key=='⁂' then
    -- The shiny mark is drawn by SummaryMenu from the 17-tile stats atlas.
    if gen==2 then assert(game.data.gen2MenuGfx.stats.tiles==17)end
    text=''
   elseif gen==1 and key=='<PO><KE>GEAR' then
    -- Generation 1 has neither this device nor its dedicated font page.
    text=''
   end
   for line in text:gmatch('[^\n\v\f\1]+')do fontCheck(line,key);lines=lines+1 end
   for _,page in ipairs(TextBox.paginate(text:gsub('\1',''),18))do
    for _,line in ipairs(page)do assert(Font.width(line)<=144,'Paginator overflow '..key)end
   end
   keys=keys+1
  end
  for gap in pairs(gaps)do print('EU_FONT_GAP',gap)end
  assert(not next(gaps),'Missing raster glyphs')
  if gen==2 then
   local Gear=require('src.ui.gen2.Pokegear')
   for _,group in ipairs({'OPT_ADVERBS','OPT_ADJECTIVES','PNP_ADJECTIVES','ROCKET_LINES'})do
    for _,key in ipairs(Gear[group])do
     local text=require('src.core.Strings')(key)
     assert(Font.width(text)<=144,'Radio fixed line clips '..key..': '..text)
    end
   end
   if not game.save then game:continueGame(require('src.core.gen2.Save').newGame({playerName='TEST'}))end
   local radio=Gear.new(game,{radioRng=function()return 2 end})
   -- Test each station with its real imported species/landmark/dex records.
   local stationIds={'OAKS_POKEMON_TALK','POKEDEX_SHOW','POKEMON_MUSIC','LUCKY_CHANNEL','PLACES_AND_PEOPLE','LETS_ALL_SING','ROCKET_RADIO','POKE_FLUTE_RADIO','UNOWN_RADIO','EVOLUTION_RADIO'}
   if version=='crystal'then stationIds[#stationIds+1]='BUENAS_PASSWORD'end
   local rd=radio:radioData();rd.caught=function()return true end
   for _,id in ipairs(stationIds)do
    local seed=0
    local show=Gear.Radio.new({data=rd,rng=function()seed=(seed+1)%251;return seed end})
    show:tune(id)
    for _=1,120 do show.delay=0;show:step()end
    for _,text in ipairs(show.log)do
     for line in text:gmatch('[^\n]+')do assert(Font.width(line)<=144,'Radio composed line clips '..id..': '..line)end
    end
   end
   for _,category in ipairs({'moves','items'})do
    for id,row in pairs(game.data[category])do
     if type(row)=='table' and row.description then
      local n=0
      for line in row.description:gsub('<NEXT>','\n'):gmatch('[^\n]+')do
       fontCheck(line,category..'/'..id)
       assert(Font.width(line)<=144,'Native description clips '..category..'/'..id..': '..line);n=n+1
      end
      assert(n<=2,'Native description pages '..category..'/'..id)
     end
    end
   end
   for id,row in pairs(game.data.gen2Pokedex.entries)do
    fontCheck(row.kind,'dex category '..id)
    assert(Font.width(row.kind)<=88,'Native category clips '..id..': '..row.kind)
    for _,field in ipairs({'text','text2'})do
     local n=0;local text=row[field]
     while text:sub(-6)=='<NEXT>'do text=text:sub(1,-7)end
     for line in (text..'<NEXT>'):gmatch('(.-)<NEXT>')do
      fontCheck(line,'dex '..id..'/'..field)
      assert(Font.width(line)<=144,'Native dex clips '..id..'/'..field..': '..line);n=n+1
     end
     assert(n<=3,'Native dex page count '..id..'/'..field)
    end
   end
  end
  for gap in pairs(gaps)do print('EU_FONT_GAP',gap)end
  assert(not next(gaps),'Missing native raster glyphs')
  print('EUROPEAN_CATALOG_LIVE_OK',version,lang,keys,lines)
 end,debug.traceback)
 if not ok then print('EUROPEAN_CATALOG_LIVE_FAILED',err)end
 love.event.quit(ok and 0 or 1)
end
