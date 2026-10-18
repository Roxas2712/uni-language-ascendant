-- Real profile codec with a memory filesystem: startup finishes after service creation.
local root=assert(arg[1]);local files={};local options={modOptions={}}
local Cache={prefix='red/'}
function Cache.write(path,bytes)files[path]=bytes;return true end
function Cache.remove(path)files[path]=nil end
local Life={};local Runtime={events={}}
package.loaded['src.import.CacheFs']=Cache
package.loaded['src.core.SessionLifecycle']=Life
package.loaded['src.mods.Runtime']=Runtime
package.loaded['src.core.SaveData']={loadOptions=function()return options end,saveOptions=function(v)options=v;return true end,defaultOptions=function()return {modOptions={}}end}
local mod={id='german_rom_source',path='mods/german_rom_source',exports={language='en'},game={},log={warn=function()end}}
function mod:read(path)return files[self.path..'/'..path]end
function mod:info(path)return self:read(path)and{size=#self:read(path)}end
local function own(path)
 if path=='session_engine.lua'then return {rebuild=function()return {},{session={}}end}end
 if path=='catalog.lua'or path=='rom_requirements.lua'then return {}end
 if path=='cache_codec.lua'then return {encode=function()return'recovery'end}end
 return assert(loadfile(root..'/mod/'..path))()
end
local Preferences=own('preferences.lua')
local initial=Preferences(mod);assert(initial:write('preferences/ui-language.txt','en'));assert(initial:write('preferences/red.txt','en'))
local S=own('session.lua')(mod,'red',own)
-- The real first-launch picker writes these later, through a separate reader.
local startup=Preferences(mod)
assert(startup:write('preferences/notice.txt','accepted'));assert(startup:write('preferences/ascendant-intro-v1.txt','seen'))
assert(startup:write('preferences/ui-language.txt','pt-BR'));assert(startup:write('preferences/gold.txt','fr'))
mod.exports.startup={uiLanguage='pt-BR'}
assert(S:text('title')==own('session_locales.lua')['pt-BR'].title and S.uiLanguage=='pt-BR')
assert(S:menuLanguage('de'));local saved=Preferences(mod)
assert(saved:read('preferences/notice.txt')=='accepted'and saved:read('preferences/ascendant-intro-v1.txt')=='seen')
assert(saved:read('preferences/gold.txt')=='fr'and saved:read('preferences/ui-language.txt')=='de')
assert(mod.exports.startup.uiLanguage=='de')
-- Another startup write must also survive the subsequent game-language handoff.
assert(saved:write('preferences/blue.txt','es'))
S.pending='pt-BR';S.snapshot={save={}};assert(S:perform())
saved=Preferences(mod)
assert(saved:read('preferences/red.txt')=='pt-BR'and saved:read('preferences/blue.txt')=='es')
assert(saved:read('preferences/ascendant-intro-v1.txt')=='seen'and saved:read('preferences/notice.txt')=='accepted')
assert(Cache.prefix=='red/'and not mod:info('baseroms/.uni-language-recovery-red.bin'))
print('SESSION_PROFILE_UNIT_OK startup locale, intro/notice and other editions survive live preference changes')
