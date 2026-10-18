-- Assertions on actual captured game state, separate from translation evidence.
return function(before,after)
 local S=require('src.core.SaveSerializer')
 local fields={'player','playerName','name','trainerId','secretId','position','map','x','y','facing','party','boxes','pcItems','bag','inventory','bagOrder','bagStacks','items','keyItems','balls','tmhm','money','coins','flags','vars','events','modData','badges','pokedex','dex','daycare','storage','registeredItem','playerState','move_overlay','store','mapScenes','mapObjectMasks'}
 local checked=0
 for _,key in ipairs(fields)do
  if before[key]~=nil or after[key]~=nil then
   local a,b=before[key],after[key]
   -- Species display names are derived from the selected language; custom
   -- nicknames, IDs, stats, moves, PP, ownership and every other field remain.
   if key=='party' then
    local function semantic(rows)
     local out={};for i,row in ipairs(rows or {})do out[i]={};for k,v in pairs(row)do if k~='name'then out[i][k]=v end end end;return out
    end
    a,b=semantic(a),semantic(b)
   end
   if S.encode(a)~=S.encode(b)then
    local function diff(x,y,path)
     if type(x)=='table' and type(y)=='table'then
      local keys={};for k in pairs(x)do keys[k]=true end;for k in pairs(y)do keys[k]=true end
      for k in pairs(keys)do diff(x[k],y[k],path..'.'..tostring(k))end
     elseif x~=y then print('LIVE_STATE_DIFF',path,tostring(x),tostring(y))end
    end
    diff(a,b,key);error('Progress changed at '..key)
   end
   checked=checked+1
  end
 end
 return checked
end
