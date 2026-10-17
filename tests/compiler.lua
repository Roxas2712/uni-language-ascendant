return function(game)
 local ok,err=xpcall(function()
  local compile=dofile(os.getenv('GERMAN_MOD_ROOT')..'/mod/compiler.lua')
  local memory,writes,calls,applied={},0,0,0
  local cache={read=function(_,p)return memory[p]end,write=function(_,p,b)memory[p]=b;writes=writes+1;return true end,delete=function(_,p)memory[p]=nil;return true end}
  local mod={read=function(_,path)local f=assert(io.open(os.getenv('GERMAN_MOD_ROOT')..'/mod/'..path,'rb'));local s=f:read('*a');f:close();return s end,cache=cache,log={warn=function()end},content={text={override=function(_,k,v)assert(k=='sample' and v[1].s=='ÄÖÜ');applied=applied+1 end}}}
  local function build()
   calls=calls+1
   return {files={['a.bin']='abc\0xyz'},operations={{registry='text',method='override',key='sample',value={{t='text',s='ÄÖÜ'}}}},report={display={abilities={[0]='NONE',[65]='NOTDÜNGER'}}}}
  end
  local _,cold=compile(mod,'one',build);assert(not cold.cacheHit and calls==1)
  local _,warm=compile(mod,'one',function()error('ROM compiler ran on warm cache')end)
  assert(warm.cacheHit and warm.display.abilities[65]=='NOTDÜNGER' and warm.display.abilities[0]=='NONE')
  memory['compiled/one/assets/1.bin']='corrupt'
  compile(mod,'one',build);assert(calls==2)
  compile(mod,'two',build);assert(calls==3)
  memory['compiled/two/index.lua']='return os.execute("must not execute")'
  compile(mod,'two',build);assert(calls==4 and applied==5)
  cache.write=function()return nil,'disk full'end
  local _,volatile=compile(mod,'three',build);assert(calls==5 and not volatile.cacheHit and applied==6)
  print('COMPILER_TEST_OK cold, warm, integrity, invalidation, safe parser, write failure')
 end,debug.traceback)
 if not ok then print('COMPILER_TEST_FAILED',err) end
 love.event.quit(ok and 0 or 1)
end
