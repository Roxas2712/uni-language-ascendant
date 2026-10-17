-- Registry/cache behavior only; not gameplay or translation evidence.
local root=assert(arg[1]);local version='ruby';local enabled=true
local Runtime={events={},wants=function()return enabled end}
local Cache={readAt=function(path)return 'base:'..path end}
local Blob={readFs=function(path)return 'disk:'..path end}
local wraps=0
local Font={glyphId=function()return 0 end,wrap=function(text,width)
 wraps=wraps+1;return width..':'..text
end}
local dataset={read=function()end,write=function()end,assetWorkerSpec=function()return 'worker' end}
local noop=function()end
local mods={
 ['src.import.CacheFs']=Cache,['src.import.CacheBlob']=Blob,['src.mods.Runtime']=Runtime,
 ['src.core.GameVersion']={get=function()return version end},['src.ui.game3.frlg_font']=Font,
 ['src.core.game3.indexed_png']={load=noop},['src.ui.game3.rse.gba_machine']={manifest=noop},
 ['src.ui.game3.rse.scene_kit']={loadLua=noop,resetCaches=noop},['src.ui.game3.rs.title']={bannerLeftCb=noop,bannerRightCb=noop},
 ['src.core.game3.pokemon']={abilityName=function()return 'base ability' end},
 ['src.core.game3.scripting.trainers']={get=function()end},['src.core.game3.dataset']={cache=function()return dataset end},
 ['src.core.game3.tileset_native']={invalidate=noop},['src.core.game3.gba_ppu']={clearCache=noop},
 ['src.ui.game3.rse.mapsec']={reset=noop},['src.core.game3.summary_data']={moveDescription=function()return 'two\nlines' end},
 ['src.ui.game3.rs.summary_menu']={manifest=function()return {nativeWindow={fontNum=3}}end},
 ['src.ui.game3.rs.egg_hatch']={Scene={text=function()return 'native hatch' end,draw=function(self)return self.displayFx[14].color end}},
 ['src.ui.game3.rs.berry_blender']={STACK_ID='test-blender'},
 ['src.ui.game3.stack']={},
 ['src.core.game3.rs.easy_chat_message']={build=noop},
 ['src.ui.game3.help_system']={show=noop,close=noop,installPack=noop},
 ['src.ui.game3.fame_checker']={pack=noop,iconDescription=noop,reloadAssets=noop},
 ['src.core.game3.rse.contest']={reset=noop},
 ['src.ui.game3.rse.contest']={manText=function(_,row)return row.bytes end,ir=function(k)return 'base:'..k end},
 ['src.ui.game3.naming']={templateFromManifest=function(man)return man.title end,pagesFromKeyboard=function(kb)return kb end},
}
local blender=mods['src.ui.game3.rs.berry_blender'];local host={};local nativeUpdates=0
host.update=function()nativeUpdates=nativeUpdates+1 end
host.stepper={run=function(_,dt,fn)assert(fn({})==true)end}
blender.open=function()host.screen={frame=function(self)self.done=true;host.screen=nil end};return host.screen end
mods['src.ui.game3.stack'].top=function()return {id=blender.STACK_ID,mod=host}end
local Help=mods['src.ui.game3.help_system']
Help.installPack=function(pack)Help.pack=pack end
Help.show=function()return Help.pack end
for name,value in pairs(mods)do package.loaded[name]=value end
love={image={newImageData=noop},graphics={newImage=noop},data={newByteData=noop}}
local function mod()return {events={on=noop},exports={},read=function(_,path)local f=assert(io.open(root..'/mod/'..path));local s=f:read('*a');f:close();return s end}end
local path='data/generated/gba/rse/summary/interface.gfx'
local apply=dofile(root..'/mod/overlay.lua')
local contestPath='data/generated/gba/rse/rs_contest_gfx/manifest.lua'
local contest=mods['src.ui.game3.rse.contest']
local manifest='data/generated/gba/naming/manifest.lua'
apply(mod(),'ruby',{[path]='localized tiles',[contestPath]='return {localizedTexts={test="translated contest"}}',[manifest]='return {title="SEU NOME?"}'},{language='pt-BR',abilities={},classes={}})
assert(contest.ir('test')=='translated contest' and contest.ir('absent')=='base:absent')
local naming=mods['src.ui.game3.naming']
assert(naming.templateFromManifest({title='YOUR NAME?'})=='SEU NOME?')
local hatch=mods['src.ui.game3.rs.egg_hatch'].Scene
local hatchScene={displayFx={[14]={y=8,color=0x7fff}}}
local color=hatch.draw(hatchScene);assert(color[1]==31 and color[2]==31 and color[3]==31)
assert(hatchScene.displayFx[14].color==0x7fff,'Native palette state changed')
blender.open();host.update(1/60);assert(host.screen==nil)
assert(Blob.readFs(path)=='localized tiles')
assert(Blob.readFs('ruby/'..path)=='localized tiles')
assert(Cache.readAt('ruby/'..path)=='localized tiles')
assert(Blob.readFs('sapphire/'..path)=='disk:sapphire/'..path)
assert(Blob.readFs('unowned.gfx')=='disk:unowned.gfx')
local desc=mods['src.core.game3.summary_data'].moveDescription
assert(desc()=='152:two lines' and desc()=='152:two lines' and wraps==1)
enabled=false;assert(hatch.draw(hatchScene)==0x7fff);host.update(1/60);assert(nativeUpdates==1);assert(contest.ir('test')=='base:test');assert(Blob.readFs(path)=='disk:'..path and desc()=='two\nlines')
assert(naming.templateFromManifest({title='YOUR NAME?'})=='YOUR NAME?')
enabled=true;version='sapphire';assert(contest.ir('test')=='base:test');assert(Blob.readFs(path)=='disk:'..path)
version='ruby';Runtime.events={};assert(contest.ir('test')=='base:test');assert(Blob.readFs(path)=='disk:'..path)
-- Reinstallation adopts the new bus and its own formatting cache.
apply(mod(),'ruby',{[path]='new tiles'},{language='pt-BR',abilities={},classes={}})
assert(contest.ir('test')=='base:test')
assert(Blob.readFs(path)=='new tiles' and desc()=='152:two lines' and wraps==2)
print('OVERLAY_UNIT_OK scoped raw tiles, inactive fallback, game/bus isolation, cached description reflow')

-- Help must restore even an absent base pack, including a language-owner loss.
local helpPath='data/generated/gba/help/pack.lua'
version='firered';apply(mod(),'firered',{[helpPath]='return {id="pt"}'},{language='pt-BR'})
assert(Help.show().id=='pt');Help.close();assert(Help.pack==nil)
local native={id='base'};Help.pack=native
assert(Help.show().id=='pt');Help.close();assert(Help.pack==native)
assert(Help.show().id=='pt');enabled=false;assert(Help.show()==native)
assert(not Help._ulaHasBasePack)
print('HELP_OVERLAY_UNIT_OK absent/populated base restoration and owner removal')

-- Inspecting exports materializes every deferred asset once; ordinary overlay
-- reads remain independent of that inspection path.
version='ruby';enabled=true
local m=mod();local reads=0;local files={[path]='tiles'}
apply(m,'ruby',files,{language='pt-BR',abilities={},classes={}},nil,function()reads=reads+1;files.extra='bytes';return files end)
assert(reads==0 and Blob.readFs(path)=='tiles')
assert(m.exports.assets.extra=='bytes' and m.exports.assets==files and reads==1)
local count=0;for _ in pairs(m.exports.assets)do count=count+1 end;assert(count==2 and reads==1)
print('LAZY_EXPORTS_UNIT_OK full inspection materializes once')
