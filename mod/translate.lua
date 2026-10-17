return function(mod, profile, bytes, policy)
  local IR=require('src.core.game3.scripting.text_ir')
  local dialect=IR.dialectOf(profile.game)
  local pending={texts={},names={}}
  local report={translated=0,total=0,names=0,missing={},authored={},retainedProperNames={},inapplicable={},display={abilities={},classes={},types={}}}
  local strings={}
  local function stringPair(english,german)
    if not english or english=='' or english==german then return end
    if strings[english]~=nil and strings[english]~=german then strings[english]=false
    else strings[english]=german end
  end
  local glyphs=profile.glyphs or {[0x15]='ß',[0xF1]='Ä',[0xF2]='Ö',[0xF3]='Ü',[0xF4]='ä',[0xF5]='ö',[0xF6]='ü'}
  local previous={}
  for k,v in pairs(glyphs) do previous[k]=IR.CHARMAP[k]; IR.CHARMAP[k]=v end

  -- The old engine exposes a shared decoder map. Install the seven missing
  -- glyphs only for this synchronous extraction and restore even on failure.
  local ok,err=pcall(function()
    local function decode(offset,battle,limit,fragment)
      assert(type(offset)=='number' and offset>=0 and offset<#bytes,'Invalid German text address')
      local ir=IR.decode(bytes:sub(offset+1,math.min(#bytes,offset+(limit or 16384))),
        {dialect=dialect,battle=battle or nil})
      assert(fragment or ir[#ir] and ir[#ir].t=='eos','Unterminated German text at '..offset)
      return ir
    end
    local function plain(offset,limit)
      local out={}
      for _,seg in ipairs(decode(offset,false,limit)) do
        if seg.t=='text' then out[#out+1]=seg.s
        elseif seg.t=='tag' then out[#out+1]=IR.toPlain({seg},{})
        elseif seg.t=='nl' or seg.t=='para' or seg.t=='scroll' then out[#out+1]='\n'
        elseif seg.t~='eos' and seg.t~='ext' then error('Unexpected '..seg.t..' in German display name at '..offset) end
      end
      return table.concat(out)
    end
    local function pointer(offset)
      local a,b,c,d=bytes:byte(offset+1,offset+4)
      assert(d,'Truncated German pointer')
      local n=a+b*256+c*65536+d*16777216-0x08000000
      if n>=0 and n<#bytes then return n end
    end
    for key,original in mod.content.text:each() do
      report.total=report.total+1
      local addr=profile.texts[key]
      if addr then
        local battle=addr[2]
        for _,s in ipairs(type(original)=='table' and original or {}) do
          if s.t=='bph' then battle=true end
        end
        local ir
        if addr[3] and addr[3]:match('^braille') then
          local raw={}
          local skip=addr[3]=='braille' and 0 or 6
          for i=addr[1]+1+skip,math.min(#bytes,addr[1]+16384) do
            local b=bytes:byte(i);raw[#raw+1]=b;if b==255 then break end
          end
          ir=require('src.import.gba.extract_scripts').decodeBraille(raw)
          if (addr[3]=='braille_ruby' or addr[3]=='braille_sapphire') then
            local format={bytes:byte(addr[1]+1,addr[1]+6)}
            table.insert(ir,1,{t='ext',cmd='brailleformat',args=format})
          end
        else ir=decode(addr[1],battle,addr[4],addr[3]=='fragment') end
        pending.texts[#pending.texts+1]={key,ir}
        local simple=true
        for _,segments in ipairs({original,ir}) do
          for _,s in ipairs(segments) do
            if s.t~='text' and s.t~='eos' and s.t~='nl' then simple=false end
          end
        end
        if simple then stringPair(IR.toPlain(original,{}),IR.toPlain(ir,{})) end
        report.translated=report.translated+1
      elseif policy and policy[key] then
        local rule=policy[key]
        local ir
        if rule.kind=='retainedProperNames' then ir=original
        elseif rule.kind=='inapplicable' then ir={{t='eos'}}
        elseif rule.kind=='authored' then
          assert(type(rule.value)=='string' and rule.value~='','Empty authored GBA text')
          ir=IR.fromAscii(rule.value)
        else error('Unknown GBA text policy for '..key) end
        pending.texts[#pending.texts+1]={key,ir}
        report[rule.kind][#report[rule.kind]+1]=key
      else
        report.missing[#report.missing+1]=key
      end
    end
    local F=profile.fields
    local function names(registry,base,stride,count,offset,indexFn)
      if not base or not stride or not count then return end
      for id,record in mod.content[registry]:each() do
        local n=indexFn and indexFn(id,record) or record.index
        if n and n>=0 and n<count then
          local name=plain(base+n*stride+(offset or 0),registry=='items' and 14 or
            registry=='trainers' and 12 or stride)
          if name~='' then
            local patch={name=name}
            if registry=='items' then
              local address=pointer(base+n*stride+20)
              if address then patch.description=IR.toPlain(decode(address,false,4096),{}) end
            elseif registry=='pokemon' and record.dex and record.dexEntry then
              patch.dexEntry={kind=plain(F.POKEDEX_ENTRIES+record.dex*F.POKEDEX_ENTRY_SIZE,12)}
            end
            pending.names[#pending.names+1]={registry,id,patch}
            report.names=report.names+1
          end
        end
      end
    end
    names('pokemon',F.SPECIES_NAMES,F.SPECIES_NAME_LENGTH,F.NUM_SPECIES)
    names('moves',F.MOVE_NAMES,F.MOVE_NAME_LENGTH+1,355)
    names('items',F.ITEMS,F.ITEM_STRIDE,F.ITEMS_COUNT)
    names('trainers',F.TRAINERS_TABLE,F.TRAINER_STRIDE,F.TRAINERS_COUNT,4,function(id) return tonumber(id) end)
    if F.ABILITY_NAMES then
      for id=0,F.ABILITIES_COUNT-1 do
        report.display.abilities[id]=plain(F.ABILITY_NAMES+id*(F.ABILITY_NAME_LENGTH+1),F.ABILITY_NAME_LENGTH+1)
      end
    end
    if F.TRAINER_CLASS_NAMES then
      for id=0,F.TRAINER_CLASS_COUNT-1 do
        report.display.classes[id]=plain(F.TRAINER_CLASS_NAMES+id*F.TRAINER_CLASS_NAME_STRIDE,F.TRAINER_CLASS_NAME_STRIDE)
      end
    end
    if F.TYPE_NAMES then
      for id=0,F.TYPE_COUNT-1 do
        report.display.types[id]=plain(F.TYPE_NAMES+id*(F.TYPE_NAME_LENGTH+1),F.TYPE_NAME_LENGTH+1)
      end
    end
    if F.ABILITY_DESCRIPTIONS and mod.content.strings then
      local cache=require('src.core.game3.dataset').cache()
      local function read(name) return assert(loadstring(assert(cache:read('data/generated/gba/pokemon/'..name..'.lua'))))() end
      local descriptions=read('descriptions')
      for _,kind in ipairs({'abilities','moves'}) do
        local original=read(kind=='abilities' and 'ability_names' or 'move_names')
        local base=kind=='abilities' and F.ABILITY_DESCRIPTIONS or F.MOVE_DESCRIPTIONS
        for id,name in pairs(original) do
          if kind=='abilities' or id>0 then
            local ptr=pointer(base+(kind=='abilities' and id or id-1)*4)
            if ptr then
              local key=(kind=='abilities' and 'ABILITY_' or 'MOVE_')..name:upper():gsub('%s+','_'):gsub('[^%w_]','')
              stringPair(descriptions[kind=='abilities' and 'ABILITIES' or 'MOVES'][key],IR.toPlain(decode(ptr,false,2048),{}))
            end
          end
        end
      end
    end
  end)
  for k in pairs(glyphs) do IR.CHARMAP[k]=previous[k] end
  assert(ok,err)
  -- Stage all parsing before registering anything. The engine also rolls back
  -- this mod's registry operations if validation fails during entry loading.
  for _,row in ipairs(pending.texts) do
    mod.content.text:override(row[1],row[2])
    mod.content.rom_text:override(row[1],row[2])
  end
  for _,row in ipairs(pending.names) do mod.content[row[1]]:patch(row[2],row[3]) end
  report.strings=0
  if mod.content.strings then
    for source,target in pairs(strings) do
      if target then mod.content.strings:override(source,target);report.strings=report.strings+1 end
    end
  end
  table.sort(report.missing)
  report.covered=report.translated
  for _,kind in ipairs({'authored','retainedProperNames','inapplicable'}) do
    table.sort(report[kind]);report.covered=report.covered+#report[kind]
  end
  return report
end
