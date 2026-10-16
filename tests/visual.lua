local function wait(n) for _=1,n do coroutine.yield() end end
return function(game)
  local ok,err=pcall(function()
    local version=require('src.core.GameVersion').get()
    assert(game.mods.exports.german_rom_source.status=='active')
    game:returnToTitle({skipIntro=true})
    wait(1000)
    game.capturePath=os.getenv('GERMAN_SHOT')
    for _=1,600 do if not game.capturePath then break end;wait(1) end
    wait(10)
    print('GERMAN_TITLE_VISUAL_OK',version)
    game:_handleBootAction({action='new_game',name='TEST',gender=0})
    wait(120)
    assert(require('src.core.game3.party').giveMon(game.session,1,15,nil,{fixedPersonality=0}))
    require('src.ui.game3.summary_menu').openMenu(game.session.party,1,{session=game.session,page=1})
    wait(160)
    game.capturePath=os.getenv('GERMAN_SHOT'):gsub('%-title.png$','-summary.png')
    for _=1,600 do if not game.capturePath then break end;wait(1) end
    wait(10)
    print('GERMAN_SUMMARY_VISUAL_OK',version)
  end)
  if not ok then print('GERMAN_TITLE_VISUAL_FAILED',err) end
  love.event.quit(ok and 0 or 1)
end
