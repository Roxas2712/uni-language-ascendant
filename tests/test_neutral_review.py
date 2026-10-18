import hashlib,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_language_remainders import audit,apply_neutral_review,canonical

class NeutralReviewTests(unittest.TestCase):
 def setUp(self):
  self.source={'name':[{'t':'text','s':'BIRCH'},{'t':'eos'}],'dialogue':[{'t':'text','s':'Hello!'},{'t':'eos'}]}
  digest=hashlib.sha256(canonical(self.source['name']).encode()).hexdigest()
  self.review={'entries':[{'source_sha256':digest,'keys':['name'],'reason':'proper-name-retained'}]}
 def test_only_exact_reviewed_identity_is_classified(self):
  report=audit(self.source,self.source,{})
  apply_neutral_review(report,self.source,self.review)
  self.assertEqual(report['unreviewed_unique_candidates'],1)
  self.assertEqual(report['reviewed_neutral_unique'],1)
  self.assertFalse(report['completeness_proven'])
 def test_changed_source_requires_new_review(self):
  self.source['name'][0]['s']='Hello, BIRCH!'
  with self.assertRaisesRegex(ValueError,'Stale neutral'):
   apply_neutral_review(audit(self.source,self.source,{}),self.source,self.review)
if __name__=='__main__':unittest.main()
