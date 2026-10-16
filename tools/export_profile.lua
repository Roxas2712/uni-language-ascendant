-- Developer-only: export address metadata, never ROM text.
local game, digest, output = assert(arg[1]), assert(arg[2]), assert(arg[3])
local G = require('src.core.GameVersion')
G.set(game)
local V = require('src.import.gba.versions')
V.select(digest)
local p = { game = game, named = {}, tables = V.TEXT_TABLES,
  battleIds = V.BATTLE_STRING_IDS, fields = {} }
for k,v in pairs(V.NAMED_TEXTS) do p.named[k] = {v, false} end
for k,v in pairs(V.NAMED_BATTLE_TEXTS) do p.named[k] = {v, true} end
for _,k in ipairs({'SPECIES_NAMES','SPECIES_NAME_LENGTH','NUM_SPECIES',
  'MOVE_NAMES','MOVE_NAME_LENGTH','ABILITY_NAMES','ABILITY_NAME_LENGTH','ABILITIES_COUNT',
  'ITEMS','ITEMS_COUNT','ITEM_STRIDE','TRAINERS_TABLE','TRAINER_STRIDE','TRAINERS_COUNT',
  'TRAINER_CLASS_NAMES','TRAINER_CLASS_NAME_STRIDE','TRAINER_CLASS_COUNT',
  'POKEDEX_ENTRIES','POKEDEX_ENTRY_SIZE','NATIONAL_DEX_COUNT',
  'STD_STRING_PTRS','STD_STRING_COUNT','ABILITY_DESCRIPTIONS','MOVE_DESCRIPTIONS',
  'TYPE_NAMES','TYPE_NAME_LENGTH','TYPE_COUNT'}) do p.fields[k] = V[k] end
local f = assert(io.open(output, 'w'))
f:write(require('src.link.Json').encode(p)); f:close()
