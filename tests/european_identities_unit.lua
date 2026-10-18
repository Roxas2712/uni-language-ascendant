local root=assert(arg[1])
local Names=dofile(root..'/mod/gb/shared/official_mon_names.lua')
local party,answer={},nil
local S={HANDLERS={},ALL={},MANIA_OT='MANIA',MANIA_OT_ID=518,
 SHUCKIE_WRONG_MON=2,SHUCKIE_REFUSED=3,SHUCKIE_RETURNED=1,SHUCKIE_HAPPY=4,SHUCKIE_FAINTED=5,SHUCKIE_HAPPY_THRESHOLD=150}
S.shared={party=function()return party end,selectMon=function()return 1,party[1]end,answer=function(_,value)answer=value end}
S.HANDLERS.ReturnShuckie=function()error('Unexpected fallback')end
assert(Names.installGen2ReturnCompatibility(S))
local function try(ot,species,id,hp,happiness)
 party={{ot=ot,species=species or 'SHUCKLE',otId=id or 518,hp=hp or 1,happiness=happiness or 0}}
 S.ALL.ReturnShuckie({});return answer,#party
end
for _,ot in ipairs({'MANIA','GABRIELE','MANÍA','MATTIA'})do
 local result,n=try(ot);assert(result==1 and n==0,ot)
 assert(try(ot,'RATTATA')==2,'Species guard')
 assert(try(ot,nil,123)==2,'ID guard')
 assert(try(ot,nil,nil,0)==5,'Fainted branch')
 assert(try(ot,nil,nil,1,200)==4,'Happy branch')
end
assert(try('MAARTEN')==2,'Unknown trainer accepted')
party={};S.ALL.ReturnShuckie({});assert(answer==3,'Cancel branch')
local rows={{nickname='USER',otName='MANIA',level=15},{nickname='SHUCKIE',otName='MANIA',level=15}}
local report=Names.patchTrades(rows,{{nickname={from='SHUCKIE',to='SHUCKI'}},{nickname={from='SHUCKIE',to='SHUCKI'}}})
assert(rows[1].nickname=='USER' and rows[2].nickname=='SHUCKI' and rows[2].level==15)
assert(report.matched==1 and report.unexpected==1,'Guard report')
print('EU_IDENTITIES_UNIT_OK official multilingual returns, cancel/fainted/happy/species/ID guards, user nickname protection')
