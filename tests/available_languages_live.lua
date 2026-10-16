-- Runs in an isolated engine identity with the requested imports staged by QA.
return function(game)
 local ok,err=xpcall(function()
  local exports=assert(game.mods.exports.german_rom_source)
  local ui=assert(exports.startup)
  assert(ui.open,'picker must be open')
  local expected={};local count=0
  for id in assert(os.getenv('QA_AVAILABLE_LANGUAGES')):gmatch('[^,]+') do expected[id]=true;count=count+1 end
  assert(#ui.choices==count,'unexpected number of game languages')
  for _,choice in ipairs(ui.choices) do assert(expected[choice.id] and choice.available,'unavailable choice shown: '..choice.id) end
  local schema=assert(game.mods.optionSchemas.german_rom_source)
  assert(#schema[1].choices==count+1,'launcher choices differ from picker')
  for _,choice in ipairs(schema[1].choices) do assert(choice[2]=='auto' or expected[choice[2]],'unavailable launcher choice') end
  assert(exports.language==assert(os.getenv('QA_EXPECTED_LANGUAGE')),'incorrect selected/fallback language')
  for _,id in ipairs({'en','de','fr','it','es','ja','ko','zh-Hans','zh-Hant'}) do assert(ui.chooseMenu(id),'missing menu locale') end
  assert(ui.choose(exports.language) and not ui.open,'cannot start available language')
  print('AVAILABLE_LANGUAGES_OK',os.getenv('QA_AVAILABLE_LANGUAGES'),exports.language,'picker + launcher + menu locales')
 end,debug.traceback)
 if not ok then print('AVAILABLE_LANGUAGES_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
