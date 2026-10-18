-- Synthetic ordering fixtures, never translation/gameplay evidence.
local root=assert(arg[1]);local enabled=true
local names={[1]='ÁGUA',[2]='ZEBRA',[3]='!',[4]='ABRIGO'}
local rows={{id=1,words={{id=2},{id=1},{id=4}}}}
local UI={populateGroups=function()return rows end}
local calls=0
local Picker={groupWords=function()return rows[1].words end,alphabetWords=function(letter)
 calls=calls+1
 return letter==2 and {{id=1},{id=2},{id=3},{id=4}} or {}
end}
package.loaded['src.core.game3.easy_chat_text']={word=function(id)return names[id]end}
package.loaded['src.ui.game3.easy_chat']=UI
package.loaded['src.ui.game3.rs.mail_composer_policy']=Picker
for _,name in ipairs({'trendy_phrase_policy','easy_chat_editor_policy'})do package.loaded['src.ui.game3.rs.'..name]={}end
local install=dofile(root..'/mod/ptbr_easy_chat_ui.lua')
install(function()return enabled and {display={language='pt-BR'}}end)
assert(UI.populateGroups()[1].words[1].id==4)
assert(rows[1].words[1].id==2,'Base/save identity data was mutated')
local a=Picker.alphabetWords(1,{},{});assert(#a==2 and a[1].id==4 and a[2].id==1)
assert(Picker.alphabetWords(0,{},{})[1].id==3)
assert(Picker.alphabetWords(26,{},{})[1].id==2)
enabled=false;assert(UI.populateGroups()==rows)
local before=calls;assert(#Picker.alphabetWords(2,{},{})==4 and calls==before+1)
print('EASY_CHAT_UI_UNIT_OK translated alphabet, accents, native alternatives, inactive scope, immutable IDs')
