# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
from drax import access

def test_access_evaluation():

  kv = {
    'key': 'value',
    'key1': 'value1',
    'key2': 'value2',
    'key3': 'value3',
    'key4': 'value4'
  }

  s1t1 = 'key=value'
  s1f1 = 'key=snarf'
  s2t1 = '(key=value)'
  s2f1 = '(key=snarf)'

  # Note: these aren't actually valid for ldapsearch
  # s3t1 = '(key1=value1)(key2=value2)'
  # s3f1 = '(key1=snart)(key2=value2)'
  # s3f2 = '(key1=value1)(key2=snarf)'
  # s3f3 = '(key1=snarf)(key2=snarf)'

  s4t1 = '&(key1=value1)(key2=value2)'
  s4f1 = '&(key1=snart)(key2=value2)'
  s4f2 = '&(key1=value1)(key2=snarf)'
  s4f3 = '&(key1=snarf)(key2=snarf)'
  s5t1 = '|(key1=value1)(key2=value2)'
  s5t2 = '|(key1=snart)(key2=value2)'
  s5t3 = '|(key1=value1)(key2=snarf)'
  s5f1 = '|(key1=snarf)(key2=snarf)'
  s6t1 = '|(key1=value1)(&(key2=value2)(key3=value3))'
  s6t2 = '|(key1=snarf)(&(key2=value2)(key3=value3))'
  s6t3 = '|(key1=value1)(&(key2=snarf)(key3=value3))'
  s6t4 = '|(key1=value1)(&(key2=value2)(key3=snarf))'
  s6t5 = '|(key1=value1)(&(key2=snarf)(key3=snarf))'
  s6t6 = '|(key1=value1)(&(key2=snarf)(key3=snarf))'
  s6f1 = '|(key1=snarf)(&(key2=snarf)(key3=value3))'
  s6f2 = '|(key1=snarf)(&(key2=value2)(key3=snarf))'
  s6f3 = '|(key1=snarf)(&(key2=snarf)(key3=snarf))'
  s7t1 = '&(key1=value1)(|(key2=value2)(key3=value3))'
  s7t2 = '&(key1=value1)(|(key2=snarf)(key3=value3))'
  s7t3 = '&(key1=value1)(|(key2=value2)(key3=snarf))'
  s7f1 = '&(key1=snarf)(|(key2=value2)(key3=value3))'
  s7f2 = '&(key1=snarf)(|(key2=snarf)(key3=value3))'
  s7f3 = '&(key1=snarf)(|(key2=value2)(key3=snarf))'
  s7f4 = '&(key1=snarf)(|(key2=snarf)(key3=snarf))'
  s7f5 = '&(key1=value1)(|(key2=snarf)(key3=snarf))'
  s8t1 = '&(|(key1=value1)(key2=value2))(key3=value3)'
  s8t2 = '&(|(key1=snarf)(key2=value2))(key3=value3)'
  s8t3 = '&(|(key1=value1)(key2=snarf))(key3=value3)'
  s8f1 = '&(|(key1=snarf)(key2=snarf))(key3=value3)'
  s8f2 = '&(|(key1=value1)(key2=value2))(key3=snarf)'
  s8f3 = '&(|(key1=snarf)(key2=snarf))(key3=snarf)'
  s8f4 = '&(|(key1=snarf)(key2=value2))(key3=snarf)'
  s8f5 = '&(|(key1=value1)(key2=snarf))(key3=snarf)'

  s9t1 = '(&(|(key1=value1)(key2=value2))(key3=value3))'
  s9f1 = '(&(|(key1=value1)(key2=snarf))(key3=snarf))'

  assert access.Evaluator(s1t1).evaluate(kv)
  assert not access.Evaluator(s1f1).evaluate(kv)

  assert access.Evaluator(s2t1).evaluate(kv)
  assert not access.Evaluator(s2f1).evaluate(kv)

# These fail and that's fine because they're not valid for ldapsearch either
# assert access.Evaluator(s3t1).evaluate(kv)
# assert not access.Evaluator(s3f1).evaluate(kv)
# assert not access.Evaluator(s3f2).evaluate(kv)
# assert not access.Evaluator(s3f3).evaluate(kv)

  assert access.Evaluator(s4t1).evaluate(kv)
  assert not access.Evaluator(s4f1).evaluate(kv)
  assert not access.Evaluator(s4f2).evaluate(kv)
  assert not access.Evaluator(s4f3).evaluate(kv)

  assert access.Evaluator(s5t1).evaluate(kv)
  assert access.Evaluator(s5t2).evaluate(kv)
  assert access.Evaluator(s5t3).evaluate(kv)
  assert not access.Evaluator(s5f1).evaluate(kv)

  assert access.Evaluator(s6t1).evaluate(kv)
  assert access.Evaluator(s6t2).evaluate(kv)
  assert access.Evaluator(s6t3).evaluate(kv)
  assert access.Evaluator(s6t4).evaluate(kv)
  assert access.Evaluator(s6t5).evaluate(kv)
  assert access.Evaluator(s6t6).evaluate(kv)
  assert not access.Evaluator(s6f1).evaluate(kv)
  assert not access.Evaluator(s6f2).evaluate(kv)
  assert not access.Evaluator(s6f3).evaluate(kv)

  assert access.Evaluator(s7t1).evaluate(kv)
  assert access.Evaluator(s7t2).evaluate(kv)
  assert access.Evaluator(s7t3).evaluate(kv)
  assert not access.Evaluator(s7f1).evaluate(kv)
  assert not access.Evaluator(s7f2).evaluate(kv)
  assert not access.Evaluator(s7f3).evaluate(kv)
  assert not access.Evaluator(s7f4).evaluate(kv)
  assert not access.Evaluator(s7f5).evaluate(kv)

  assert access.Evaluator(s8t1).evaluate(kv)
  assert access.Evaluator(s8t2).evaluate(kv)
  assert access.Evaluator(s8t3).evaluate(kv)
  assert not access.Evaluator(s8f1).evaluate(kv)
  assert not access.Evaluator(s8f2).evaluate(kv)
  assert not access.Evaluator(s8f3).evaluate(kv)
  assert not access.Evaluator(s8f4).evaluate(kv)
  assert not access.Evaluator(s8f5).evaluate(kv)

  assert access.Evaluator(s9t1).evaluate(kv)
  assert not access.Evaluator(s9f1).evaluate(kv)
