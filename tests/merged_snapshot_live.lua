return function(game)
 local e=assert(game.mods.exports.german_rom_source)
 assert(e.status=='active' and e.language=='pt-BR','PT-BR activation')
 if os.getenv('QA_EXPECT_COVERED')=='1' and e.coverage.total then
  assert(e.coverage.covered==e.coverage.translated+#e.coverage.retainedProperNames+#e.coverage.inapplicable,'Final authored coverage count')
 end
 assert(e.coverage.cacheHit==(os.getenv('QA_CACHE_STATE')=='warm'),'Compiler cache state')
 return assert(loadfile(assert(os.getenv('GERMAN_MOD_ROOT'))..'/tests/cache_snapshot.lua'))()(game)
end
