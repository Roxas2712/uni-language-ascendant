return function(game)
 local ok,err=xpcall(function()
  local mode=assert(os.getenv('QA_MODE'));local V=require('src.core.GameVersion');local v,gen=V.get(),V.generation()
  local exp=game.mods.exports.german_rom_source
  local Font=require('src.render.Font')
  if mode=='disabled'then
   assert(not exp,'Disabled mod loaded')
  else assert(exp and exp.status=='english','English restart did not restore original language')end
  assert(game.data.pokemon.BULBASAUR.name=='BULBASAUR','Species overlay leaked')
  assert(not game.data.strings or game.data.strings.RUN~='HUIR','String overlay leaked')
  assert(not Font.__ulaEuropeanStrings or not Font.__ulaEuropeanStrings.active(),'Renderer hook remained active')
  local Assets=require('src.render.Assets')
  assert(not Assets.resolve('assets/generated/tilesets/overworld.png'):find('rom%-language'),'World overlay leaked')
  local Save=require(gen==1 and 'src.core.SaveData' or 'src.core.gen2.Save')
  local save=assert(Save.load(v),'Foreign-language save missing')
  assert(save.party[1].nickname=='TESTMON','Saved nickname lost across process restart')
  if gen==2 and mode=='english'then
   local S=require('src.script.gen2.Specials');local gift=assert(save.party[2]);local expected=gift.ot
   assert(expected=='MANIA' or expected=='MANÍA' or expected=='MATTIA','Unexpected saved native OT')
   local vm={specials={party=function()return save.party end,selectPartyMon=function(_,done)done(2,gift)end}}
   gift.happiness=0;S.ALL.ReturnShuckie(vm)
   assert(vm.scriptVar==S.SHUCKIE_RETURNED,'Saved gift cannot be returned after English restart')
  end
  print('EUROPEAN_LIFECYCLE_OK',v,mode)
 end,debug.traceback)
 if not ok then print('EUROPEAN_LIFECYCLE_FAILED',err)end
 love.event.quit(ok and 0 or 1)
end
