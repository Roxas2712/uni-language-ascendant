-- Persistent, disposable compilation cache in mod.cache. The commit index is
-- written last; missing/corrupt payloads cause a complete rebuild before apply.
return function(mod,key,compile)
 local W=require('src.core.SaveSerializer')
 local function hash(bytes) return love.data.encode('string','hex',love.data.hash('string','sha256',bytes)) end
 local cache=mod.cache
 local root='compiled/'..key..'/'
 local function decode(bytes) return assert(W.decode(bytes,{maxBytes=16*1024*1024,maxNodes=500000,maxDepth=40})) end
 local function load()
  if not cache then return end
  local index=cache:read(root..'index.lua')
  if not index then return end
  local ok,value=pcall(function()
   local index=decode(index)
   assert(index.key==key and type(index.rows)=='table')
   local files,operations,report={},{},nil
   for _,row in ipairs(index.rows) do
    assert(type(row.path)=='string' and row.path:match('^[%w_./-]+$') and not row.path:find('..',1,true))
    local data=assert(cache:read(root..row.path))
    assert(#data==row.size and hash(data)==row.hash,'incomplete language cache')
    if row.kind=='asset' then files[row.name]=data
    elseif row.kind=='report' then report=decode(data)
    elseif row.kind=='operations' then for _,op in ipairs(decode(data)) do operations[#operations+1]=op end
    else error('unknown cache payload') end
   end
   assert(report and #operations>0)
   return {files=files,operations=operations,report=report}
  end)
  if ok then return value end
  mod.log:warn('Language cache invalid; rebuilding: %s',tostring(value))
 end
 local compiled=load()
 local hit=compiled~=nil
 if not compiled then
  compiled=compile()
  if cache then
   local ok,err=pcall(function()
    cache:delete(root..'index.lua')
    local index={key=key,rows={}}
    local function write(path,bytes,kind,name)
     assert(cache:write(root..path,bytes))
     index.rows[#index.rows+1]={path=path,size=#bytes,hash=hash(bytes),kind=kind,name=name}
    end
    local names={};for path in pairs(compiled.files) do names[#names+1]=path end;table.sort(names)
    for i,path in ipairs(names) do write('assets/'..i..'.bin',compiled.files[path],'asset',path) end
    for i=1,#compiled.operations,100 do
     local batch={};for j=i,math.min(i+99,#compiled.operations) do batch[#batch+1]=compiled.operations[j] end
     write('operations/'..i..'.lua',W.encode(batch),'operations')
    end
    write('report.lua',W.encode(compiled.report),'report')
    assert(cache:write(root..'index.lua',W.encode(index)))
   end)
   if not ok then mod.log:warn('Language cache could not be saved: %s',tostring(err)) end
  end
 end
 -- All cached payloads are validated before any operation reaches the loader.
 for _,op in ipairs(compiled.operations) do
  local registry=assert(mod.content[op.registry])
  assert(op.method=='override' or op.method=='patch')
  registry[op.method](registry,op.key,op.value)
 end
 compiled.report.cacheHit=hit
 return compiled.files,compiled.report
end
