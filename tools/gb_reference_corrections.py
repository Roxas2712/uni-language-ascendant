"""Development-only corrections verified against the supplied retail ROMs.
Never packaged: the compiler emits ROM span addresses for these strings.
"""
def correct(game,cats):
 d=cats['dialogue.lua']
 if game in ['gold','silver','crystal']:
  for k,v in cats['item_names.lua'].items():
   if v.startswith('HM'):cats['item_names.lua'][k]='VM'+v[2:]
 if game=='crystal':
  cats['rom_text.lua']['_SeerMoreCareText']=cats['rom_text.lua']['_SeerMoreCareText'].replace('orumsichtiger','umsichtiger')
  for k,v in cats['landmark_names.lua'].items():
   if k in ['LANDMARK_DIGLETTS_CAVE','LANDMARK_NATIONAL_PARK','LANDMARK_SEAFOAM_ISLANDS','LANDMARK_UNION_CAVE','LANDMARK_VICTORY_ROAD']:
    cats['landmark_names.lua'][k]=v.replace('DIGDAS','DIGDA').replace('-\n','\n')
 if game in ['red','blue','yellow']:
  d['_ChooseABoxText']=d['_ChooseABoxText'].replace('POKéMON-BOX!','PKMN-BOX!')
  if game!='yellow':d['_PewterCityTrainerTipsText']=d['_PewterCityTrainerTipsText'].replace('Erfahrungspunkte, ','Erfahrungspunkte,')
 if game=='yellow':
  cats['dialogue_aliases.lua']['_PalletTownOakItsUnsafeText']=d['_PalletTownOakThatWasCloseText']
 if game in ['gold','silver']:
  # 0x1049a1 Gold; same telephone text in Silver.
  d['41:4aba']='Oh, du bist in\n{STRBUF}…\fIst dort nicht\n{STRBUF}?\fHast du schon\nnachgesehen?'
 if game=='crystal':
  d['70:4e6f']='{STRBUF}\nist nicht\vinteressiert.'
  d['70:4f2c']=d['70:4f2c'].replace('BRIEFES','BRIEFes')
  d['70:4f8d']='Der BRIEF wurde\naus dem BRIEF-\vKASTEN gelöscht.'
  d['70:5c22']=d['70:5c22'].replace('BRIEFES','BRIEFes')
  d['71:4c28']=d['71:4c28'].replace('Hallo, Kleiner.\fIch','Hallo,\fich')
  d['71:4e5f']=d['71:4e5f'].replace('Medizin ?','Medizin?')
  d['71:4fd7']='Ich kann dir das\nnicht abkaufen.'
