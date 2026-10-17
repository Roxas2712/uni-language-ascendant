-- Unit tests for the compatibility hook; no dialogue or gameplay evidence.
local root=assert(arg[1])
package.loaded['src.core.game3.party']={PLAYER_HAS_TWO_USABLE_MONS=0,
 monsStateToDoubles=function(party)return #party>=2 and 0 or 1 end}
local releases=0
package.loaded['src.core.game3.scripting.ops_a']={dispatchUnhooked=function(vm,row)
 assert(row.op=='releaseall');releases=releases+1;vm.ctx.frozen=false
end}
local hook
dofile(root..'/mod/compat.lua')({hooks={wrap=function(_,name,fn)
 assert(name=='script.command');hook=fn
end}})
local function fixture(count)
 local party={};for i=1,count do party[i]={} end
 return {runner={ctx={status='running',mode='bytecode',frozen=true}},session={party=party}}
end
local context=fixture(1);local closed=false
assert(hook(function(c)
 c.runner.ctx.mode='native';c.runner.ctx.status='waiting'
 c.runner.ctx.nativePoll=function()if closed then c.runner.ctx.status='halted' end;return false end
 return true
end,context,'trainerbattle',{type=7}))
context.runner.ctx.nativePoll();assert(releases==0 and context.runner.ctx.frozen)
closed=true;context.runner.ctx.nativePoll()
assert(releases==1 and not context.runner.ctx.frozen and not context.runner.ctx.nativePoll)
assert(context.runner.ctx.mode=='bytecode')
-- A valid double battle's own native wait must never be wrapped/released.
context=fixture(2);local poll=function()return false end
hook(function(c)c.runner.ctx.mode='native';c.runner.ctx.nativePoll=poll;return true end,
 context,'trainerbattle',{type=7})
assert(context.runner.ctx.nativePoll==poll and releases==1)
-- A rejected rematch that falls through has not shown a rejection message.
context=fixture(1)
hook(function()return false end,context,'trainerbattle',{type=7})
assert(context.runner.ctx.frozen and releases==1)
-- The synchronous close branch also restores control.
context=fixture(1)
hook(function(c)c.runner.ctx.status='halted';return true end,context,'trainerbattle',{type=4})
assert(not context.runner.ctx.frozen and releases==2)
local version='emerald'
package.loaded['src.core.GameVersion']={get=function()return version end}
package.loaded['src.core.game3.rom_text']={plain=function(key)
 assert(key=='stdstring:29');return 'PIRÂMIDE DE BATALHA'
end}
package.loaded['src.core.game3.scripting.flags']={getVar=function(store,ctx,id)
 assert(id==0x8000);return 29
end}
local function buffer(src,value)
 local c={runner={ctx={stringVars={}}}}
 local result=hook(function()c.runner.ctx.stringVars[1]=value;return false end,c,'bufferstdstring',{dest=0,src=src})
 assert(result==false);return c.runner.ctx.stringVars[1]
end
assert(buffer(29,'29')=='PIRÂMIDE DE BATALHA')
assert(buffer(0x8000,'29')=='PIRÂMIDE DE BATALHA')
assert(buffer(28,'28')=='28')
assert(buffer(29,'already resolved')=='already resolved')
version='firered';assert(buffer(29,'29')=='29')
print('COMPAT_UNIT_OK')
