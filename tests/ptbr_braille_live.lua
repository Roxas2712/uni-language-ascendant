-- Read actual field signs through the edition's VM. No replacement UI text.
return function(game)
 local function wait(n) for _=1,n do coroutine.yield() end end
 local ok,err=xpcall(function()
  local version=require('src.core.GameVersion').get()
  local em=version=='emerald'
  local prefix=assert(({ruby='RU_',sapphire='SA_',emerald='EM_'})[version])
  assert(game.mods.exports.german_rom_source.language=='pt-BR')
  local Map=require('src.core.game3.map')
  local Field=require('src.core.game3.field')
  local Braille=require('src.ui.game3.braille')
  local Message=require('src.ui.game3.message')
  game:_handleBootAction({action='new_game',name='TEST',gender=0,start={map=prefix..'OLDALE_TOWN',x=6,y=17,facing='up'}})
  wait(90)
  local cases={
   {'rise','UNDERWATER_SEALED_CHAMBER',12,44,'SUBA AQUI.'},
   {'dig','SEALED_CHAMBER_OUTER_ROOM',10,3,em and 'ESCAVE AQUI.' or 'CAVE AQUI'},
   {'order','SEALED_CHAMBER_INNER_ROOM',10,5,em and 'PRIMEIRO VEM\nWAILORD.\nPOR ULTIMO,\nRELICANTH.' or 'PRIMEIRO,\nRELICANTH.\nPOR ULTIMO,\nWAILORD.'},
   {'story-1','SEALED_CHAMBER_INNER_ROOM',6,9,em and 'VIVEMOS\nNESTA\nCAVERNA.' or 'NESTA\nCAVERNA\nVIVEMOS'},
   {'story-2','SEALED_CHAMBER_INNER_ROOM',14,9,em and 'DEVEMOS TUDO\nAOS POKEMON.' or 'DEVEMOS\nTUDO AOS\nPOKEMON.'},
   {'story-3','SEALED_CHAMBER_INNER_ROOM',4,14,em and 'MAS NOS\nSELAMOS O\nPOKEMON.' or 'MAS\nSELAMOS O\nPOKEMON\nAQUI.'},
   {'story-4','SEALED_CHAMBER_INNER_ROOM',16,14,em and 'O TEMIAMOS.' or 'TINHAMOS MEDO'},
   {'story-5','SEALED_CHAMBER_INNER_ROOM',6,19,em and 'AQUELES COM\nCORAGEM,\nAQUELES COM\nESPERANCA.' or 'OS QUE TEM\nCORAGEM,\nOS QUE TEM\nESPERANCA.'},
   {'story-6','SEALED_CHAMBER_INNER_ROOM',14,19,em and 'ABRA A PORTA.\nUM POKEMON\nETERNO\nESPERA.' or 'ABRA A PORTA\nUM POKEMON\nETERNO\nESPERA.'},
   {'desert','DESERT_RUINS',7,21,em and 'ESQ., ESQ.,\nBAIXO, BAIXO.\nDEPOIS, USE\nQUEBRAROCHA.' or 'DIREITA DUAS,\nBAIXO DUAS.\nDEPOIS,\nUSE FORCA.'},
   {'island','ISLAND_CAVE',7,21,em and 'FIQUE JUNTO\nDA PAREDE.\nCORRA UMA\nVOLTA.' or 'PARE. DEIXE\nO TEMPO\nPASSAR DUAS\nVEZES.'},
   {'tomb','ANCIENT_TOMB',7,21,em and 'QUEM HERDAR\nNOSSA VONTADE\nBRILHE NO\nCENTRO.' or 'COM NOVO TEMPO\nAMOR,ESPERANCA\nMIRE O CEU\nNO CENTRO.'},
  }
  for _,c in ipairs(cases) do
   assert(Map.load(nil,game,prefix..c[2],{x=c[3],y=c[4],facing='up'}));wait(45)
   assert(not Field.isLocked() and not Message.isOpen())
   Field.interact(game)
   for _=1,120 do if Braille.isOpen() then break end;wait(1) end
   assert(Braille.isOpen(),'Native braille did not open: '..c[1])
   assert(Braille._text==c[5],'Wrong braille: '..c[1]..' / '..tostring(Braille._text))
   local rows=Braille.encode(Braille._text)
   local window=Braille.window()
   local width=window and (window.right-window.textX)*8 or 208
   for _,row in ipairs(rows) do assert(#row*16<=width,'Braille outside window: '..c[1]) end
   assert((#rows-1)*Braille.linePitch()+16<=(window and (window.bottom-window.textY)*8 or 128),'Braille too tall')
   Message.skipReveal();wait(20)
   assert(Braille._fg,'Native braille glyph image did not load')
   game.capturePath=os.getenv('SHOT_DIR')..'/'..version..'-pt-BR-braille-'..c[1]..'.png'
   for _=1,600 do if not game.capturePath then break end;wait(1) end
   assert(not game.capturePath)
   local text=Braille._text
   for _=1,50 do
    game:keypressed('z');wait(1);game:keyreleased('z');wait(10)
    if not Field.isLocked() and not Message.isOpen() then break end
   end
   assert(not Field.isLocked() and not Message.isOpen(),'Braille did not close: '..c[1])
   print('LANGUAGE_BRAILLE_EVIDENCE '..require('src.link.Json').encode({game=version,case=c[1],map=prefix..c[2],text=text,
    fixture='New save, player positioned at original sign; Field.interact; original VM and braille renderer',completed=true}))
  end
  print('LANGUAGE_BRAILLE_OK',version,#cases)
 end,debug.traceback)
 if not ok then print('LANGUAGE_BRAILLE_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
