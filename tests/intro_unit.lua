local root=assert(arg[1]);local Intro=dofile(root..'/mod/intro.lua')
local function setup(fail)
 local store={};local calls={draw=0,play=0,release=0,resume=0,finish=0,warn=0}
 love={audio={pause=function()return {{play=function()calls.resume=calls.resume+1 end}}end},graphics={getDimensions=function()return 800,600 end}}
 local mod={game={options={}},cache={read=function(_,k)return store[k]end,write=function(_,k,v)if fail then return nil,'disk full' end;store[k]=v;return true end},log={warn=function()calls.warn=calls.warn+1 end}}
 local own=function()return {new=function()return {duration=.4,play=function(_,volume)calls.play=calls.play+1;calls.volume=volume end,draw=function(_,t,w,h)assert(w==800 and h==600);calls.draw=calls.draw+1 end,release=function()calls.release=calls.release+1 end}end}end
 local scene=Intro.new(mod,own,function()calls.finish=calls.finish+1 end)
 return mod,scene,calls,store
end
local mod,s,c=setup();assert(Intro.pending(mod));s:update(100);assert(s.elapsed==0 and not s:skip())
s:draw();for _=1,4 do s:update(.1) end
assert(not Intro.pending(mod) and c.play==1 and c.release==1 and c.resume==1 and c.finish==1)
s:close();s:update(.1);s:draw();assert(c.release==1 and c.finish==1,'duplicate cleanup')
local m2,s2,c2=setup();s2:draw();s2:update(.1);assert(not s2:skip());s2:update(.1);assert(s2:skip() and not Intro.pending(m2))
local m3,s3,c3=setup();s3:draw();s3:close();assert(Intro.pending(m3) and c3.release==1 and c3.finish==0,'aborted intro consumed marker')
local m4,s4,c4=setup(true);s4:draw();for _=1,4 do s4:update(.1) end;assert(Intro.pending(m4) and c4.warn==1 and c4.finish==1)
local m5,s5,c5=setup();m5.game.options.splashMute=true;s5:draw();assert(c5.volume==0);s5:close()
print('INTRO_UNIT_OK natural completion, restart marker, skip, interruption, storage failure, mute, cleanup')
