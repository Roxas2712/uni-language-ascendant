local root=assert(arg[1])
local Json=require('src.link.Json')
local function read(path)local f=assert(io.open(root..'/mod/'..path));local b=f:read('*a');f:close();return b end
local m=Json.decode(read('manifest.json'))
local catalog=dofile(root..'/mod/catalog.lua')
local requirements=dofile(root..'/mod/rom_requirements.lua')
local profiles,imports,listed={},{},{}
for _,i in ipairs(m.optional_imports) do assert(not imports[i.id]);imports[i.id]=i end
for _,r in ipairs(requirements) do listed[r.game]=r;assert(#r.base.sha1==40) end
for _,c in ipairs(catalog) do
 assert(not profiles[c.id]);profiles[c.id]=true
 local p=dofile(root..'/mod/'..c.profile);local i=assert(imports[c.sourceId or c.id])
 assert(i.md5==p.md5 and i.size==p.size,'Manifest/profile identity mismatch: '..c.id)
 local found
 for _,s in ipairs(assert(listed[c.game]).sources) do if s.language==c.language and s.sha1==p.sha1 then found=s end end
 assert(found,'ROM list/profile SHA-1 mismatch: '..c.id)
 if c.root then
  assert(loadfile(root..'/mod/'..c.adapter));assert(loadfile(root..'/mod/'..c.runtime))
 else assert(loadfile(root..'/mod/'..c.assets));assert(loadfile(root..'/mod/'..c.world)) end
end
assert(#requirements==11 and #catalog==38 and #m.games==11)
print('CATALOG_OK 11 editions, 38 language profiles, exact manifest/profile/ROM-list identities, generation adapters')
