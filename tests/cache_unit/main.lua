function love.load()
 local ok,err=xpcall(function()
  local root=assert(os.getenv('GERMAN_MOD_ROOT'))
  package.path=assert(os.getenv('QA_ENGINE'))..'/?.lua;'..package.path
  local B=dofile(root..'/mod/cache_codec.lua')
  local W=require('src.core.SaveSerializer')
  local values={false,true,0,-0.5,1e100,'','Olá\0\255\n"\\',{},
   {[0]='zero',[8]=false,[-3]='negative',[false]=true,['1']='string key',nested={{t='text',s='ãõé'},{t='eos'}}}}
  for _,v in ipairs(values)do
   local encoded=B.encode(v)
   assert(W.encode(B.decode(encoded))==W.encode(v),'Round trip changed value')
   for n=0,#encoded-1 do assert(not pcall(B.decode,encoded:sub(1,n)),'Truncation accepted')end
   assert(not pcall(B.decode,encoded..'x'),'Trailing data accepted')
  end
  assert(B.decode(B.encode(nil))==nil)
  assert(not pcall(B.decode,'return os.execute("must not execute")'))
  for _,v in ipairs({math.huge,-math.huge,0/0,function()end})do assert(not pcall(B.encode,v))end
  local cyclic={};cyclic.self=cyclic;assert(not pcall(B.encode,cyclic))
  local deep={};local head=deep;for _=1,41 do head.next={};head=head.next end;assert(not pcall(B.encode,deep))
  assert(not pcall(B.decode,'ULAC\1'..'5'..love.data.pack('string','<I4',4294967295)))
  local key=B.encode('key'):sub(6);local value=B.encode(false):sub(6)
  assert(not pcall(B.decode,'ULAC\1'..'5'..love.data.pack('string','<I4',2)..key..value..key..value),'Duplicate key accepted')
  local compile=dofile(root..'/mod/compiler.lua')
  local memory={};local cache={read=function(_,p)return memory[p]end,write=function(_,p,b)memory[p]=b;return true end,delete=function(_,p)memory[p]=nil end}
  local Registry=require('src.mods.Registry')
  local function mod()
   return {read=function(_,path)local f=assert(io.open(root..'/mod/'..path));local b=f:read('*a');f:close();return b end,
    content={text=Registry.new('text')},cache=cache,log={warn=function()end}}
  end
  local ops={
   {registry='text',method='patch',key='a',value={gone=true}},
   {registry='text',method='patch',key='b',value={nested={x=1}}},
   {registry='text',method='override',key='a',value={old=true}},
   {registry='text',method='patch',key='a',value={obsolete=true}},
   {registry='text',method='override',key='a',value={current=true}},
   {registry='text',method='patch',key='a',value={nested={z=3}}},
   {registry='text',method='patch',key='b',value={nested={y=2}}},
  }
  local original=mod()
  for _,op in ipairs(ops)do original.content.text[op.method](original.content.text,op.key,op.value)end
  local builds=0
  local function build()builds=builds+1;return {files={['a.bin']='abc\0xyz'},operations=ops,report={translated=2}}end
  local function same(m)
   local function rows(reg)local out={};for k,v in reg:each()do out[k]=v end;return out end
   assert(W.encode(rows(m.content.text))==W.encode(rows(original.content.text)))
   assert(W.encode(m.content.text.order)==W.encode(original.content.text.order),'First-touch order changed')
   local n=0;for _,v in pairs(m.content.text.ops)do n=n+#v end;assert(n==4,'Redundant overrides retained')
  end
  local cold=mod();local _,r=compile(cold,'case',build);assert(not r.cacheHit and builds==1);same(cold)
  local warm=mod();local _,r=compile(warm,'case',function()error('Warm cache recompiled')end);assert(r.cacheHit);same(warm)
  -- A corrupted late batch must trigger a rebuild before any registry write.
  local index=assert(W.decode(memory['compiled/case/index.lua']))
  for _,row in ipairs(index.rows)do if row.kind=='operations' then memory['compiled/case/'..row.path]='corrupt' end end
  local recovered=mod();local _,r=compile(recovered,'case',build);assert(not r.cacheHit and builds==2);same(recovered)
  -- Exercise compression on cold and warm loads, exact bytes and deferred reads.
  local raw=string.rep('graphic bytes\0\255',5000)
  local function graphics()
   return {files={['one.gfx']=raw,['two.map']=raw..'map',['manifest.lua']=raw,['image.png']=raw},operations=ops,report={translated=2}}
  end
  local f,rep,materialize=compile(mod(),'graphics',graphics,{lazyAssets=true})
  assert(not rep.cacheHit and rawget(f,'one.gfx')==nil and rawget(f,'two.map')==nil)
  assert(f['manifest.lua']==raw and f['image.png']==raw)
  assert(f['one.gfx']==raw and rawget(f,'one.gfx')==raw)
  assert(rawget(f,'two.map')==nil);assert(materialize()==f and f['two.map']==raw..'map')
  local f,rep,materialize=compile(mod(),'graphics',function()error('Warm graphics recompiled')end,{lazyAssets=true})
  assert(rep.cacheHit and rawget(f,'one.gfx')==nil and rawget(f,'two.map')==nil)
  materialize();local n=0;for k,v in pairs(f)do n=n+1;assert(v==(k=='two.map' and raw..'map' or raw))end;assert(n==4)
  local f,rep=compile(mod(),'graphics',function()error('Eager compatibility recompiled')end)
  assert(rep.cacheHit and rawget(f,'one.gfx')==raw and rawget(f,'two.map')==raw..'map')
  -- A valid compressed stream with the wrong expanded digest cannot be applied.
  local ix=assert(W.decode(memory['compiled/graphics/index.lua']))
  for _,row in ipairs(ix.rows)do if row.kind=='asset-zlib' then row.rawHash='wrong';break end end
  memory['compiled/graphics/index.lua']=W.encode(ix)
  local rebuilt=0;local m=mod();local f,rep=compile(m,'graphics',function()rebuilt=rebuilt+1;return graphics()end,{lazyAssets=true})
  assert(not rep.cacheHit and rebuilt==1 and f['one.gfx']==raw);same(m)
  -- Corrupt the second of two operation batches: no first-batch history
  -- may leak into the rebuilt registry.
  local many={};for i=1,501 do many[i]={registry='text',method='override',key='key-'..i,value={i=i}}end
  local function batchBuild()return {files={},operations=many,report={translated=501}}end
  compile(mod(),'batches',batchBuild)
  local ix=assert(W.decode(memory['compiled/batches/index.lua']));local batches=0
  for _,row in ipairs(ix.rows)do if row.kind=='operations' then batches=batches+1;if batches==2 then memory['compiled/batches/'..row.path]='corrupt' end end end
  assert(batches==2)
  local recovered=mod();local _,rep=compile(recovered,'batches',batchBuild);assert(not rep.cacheHit)
  local n=0;for k,history in pairs(recovered.content.text.ops)do n=n+1;assert(#history==1)end;assert(n==501)
  print('CACHE_BATCH_ROLLBACK_OK corrupt second batch rebuilds without partial writes')
  print('CACHE_LAZY_ASSETS_OK cold/warm, exact bytes, deferred reads, full inspection, eager compatibility, expanded integrity')
  print('CACHE_CODEC_UNIT_OK lossless types, Unicode/binary, limits, truncation, invalid data')
  print('CACHE_COMPACTION_UNIT_OK cold/warm effective values, patch chains, first-touch order, corrupt cache rollback')
  -- Existing unit cases include cache-key invalidation and disk-full behavior.
  assert(loadfile(root..'/tests/compiler.lua'))()({})
 end,debug.traceback)
 if not ok then print(err);love.event.quit(1)end
end
