local function wait(n) for _=1,n do coroutine.yield() end end
return function(game)
  local ok,err=pcall(function()
    local version=require('src.core.GameVersion').get()
    local exports=assert(game.mods and game.mods.exports.german_rom_source,'German mod failed to load')
    assert(exports.status=='active','German ROM source is not active: '..tostring(exports.status))
    assert(exports.coverage.translated>8000,'dialogue coverage regressed')
    local Pokemon=require('src.core.game3.pokemon')
    assert(Pokemon._names[1]=='BISASAM','Bulbasaur name was not imported')
    local base=assert(loadfile(os.getenv('GERMAN_BASE_CACHE')..'/'..version..'/data/generated/gba/pokemon/stats.lua'))()
    local function same(a,b)
      if type(a)~=type(b) then return false end
      if type(a)~='table' then return a==b end
      for k,v in pairs(a) do if not same(v,b[k]) then return false end end
      for k in pairs(b) do if a[k]==nil then return false end end
      return true
    end
    assert(same(Pokemon._stats,base),'Language mod changed base stats')
    -- No artificial engine identity: the stock engine still runs the US game.
    assert(not require('src.core.GameVersion').acceptsSha1(version,
      version=='firered' and '18a3758ceeef2c77b315144be2c3910d6f1f69fe' or
      version=='sapphire' and '7e6e034f9cdca6d2c4a270fdb50a94def5883d17' or
      version=='leafgreen' and '0802d1fb185ee3ed48d9a22afb25e66424076dac' or
      version=='ruby' and '1c2a53332382e14dab8815e3a6dd81ad89534050' or
      '61c2eb2b380b1a75f0c94b767a2d4c26cd7ce4e3'),'test engine contains German import patches')
    print('GERMAN_MOD_COUNTS',version,exports.coverage.translated,exports.coverage.total,exports.coverage.names)
    wait(30)
    game:_handleBootAction({action='new_game',name='TEST',gender=0})
    wait(90)
    assert(game.phase=='field','new game did not reach field')
    assert(Pokemon._names[1]=='BISASAM','German names lost after field reload')
    assert(same(Pokemon._stats,base),'Field reload changed base stats')
    assert(game:saveGame(),'save failed')
    local saved=assert(require('src.core.SaveData').load())
    assert(saved.engine=='game3','save format changed')
    assert(saved.version==nil or saved.version==version,'save edition changed')
    local Text=require('src.core.game3.rom_text')
    local sample=version=='leafgreen' and 'Text_WelcomeWantToHealPkmn' or 'gText_Yes'
    if Text.has(sample) then
      local message=Text.plain(sample)
      print('GERMAN_MOD_TEXT',message)
      require('src.ui.game3.hud').openMessage(game,message)
      wait(360)
    end
    local path=os.getenv('GERMAN_SHOT')
    if path then
      game.capturePath=path
      for _=1,600 do if not game.capturePath then break end;wait(1) end
    end
    print('GERMAN_MOD_SMOKE_OK',version)
  end)
  if not ok then print('GERMAN_MOD_SMOKE_FAILED',tostring(err)) end
  love.event.quit(ok and 0 or 1)
end
