local root=assert(arg[1]);local create=dofile(root..'/mod/preferences.lua')
local fs={};local fail,throw=false,false
local Cache={prefix='red/'}
Cache.write=function(path,bytes)
 assert(Cache.prefix=='','version prefix leaked into profile')
 if throw then error('filesystem error')end
 if fail then return nil,'disk full'end
 fs[path]=bytes;return true
end
local options={unrelated=17,modOptions={other={x=3},test={language='de',showPicker=false}}}
package.loaded['src.import.CacheFs']=Cache
package.loaded['src.core.SaveData']={loadOptions=function()return options end,saveOptions=function(o)assert(o.unrelated==17 and o.modOptions.other.x==3);return true end}
local mod={id='test',path='mods/test',game={mods={modOptions={}},options={}},read=function(_,p)return fs['mods/test/'..p]end,log={warn=function()end}}
local a=create(mod);assert(a.fresh and options.modOptions.test.language=='auto' and options.modOptions.test.showPicker)
assert(a:write('preferences/ui-language.txt','de'));assert(Cache.prefix=='red/')
assert(a:write('preferences/ascendant-intro-v1.txt','seen'))
local b=create(mod);assert(not b.fresh and b:read('preferences/ui-language.txt')=='de')
fail=true;assert(not b:write('preferences/ui-language.txt','ja'));assert(b:read('preferences/ui-language.txt')=='de' and Cache.prefix=='red/')
fail=false;throw=true;assert(not b:write('preferences/ui-language.txt','ja'));assert(Cache.prefix=='red/');throw=false
assert(b:reset() and not b:read('preferences/ascendant-intro-v1.txt'))
assert(b:write('preferences/ui-language.txt','es'))
-- A reinstall has no profile even if stale options or old mod cache remain.
fs['mods/test/baseroms/.uni-language-profile']=nil;options.modOptions.test={language='de',showPicker=false}
local c=create(mod);assert(c.fresh and not c:read('preferences/ui-language.txt') and options.modOptions.test.language=='auto')
fs['mods/test/baseroms/.uni-language-profile']='return os.execute("bad")'
assert(create(mod).fresh,'untrusted profile was interpreted as code')
print('PREFERENCES_UNIT_OK scoped data, restart, reset, reinstall, stale options, failure rollback, prefix restoration')
