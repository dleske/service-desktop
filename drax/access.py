# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
"""
Provides a class for evaluating access rights based on LDAP-like conditions.
For example, this would evaluate to true if both key1=value1 and key2=value2.
  &(key1=value1)(key2=value2)

The following evaluates to true if key1=value1 and either key2=value2 or
key3=value3:
  &(key1=value1)(|(key2=value2)(key3=value3))

Simpler cases:
  key1=value1
  (key1=value1)

The parser works by building a parse tree for the access condition and then
evaluating a dictionary of values against this tree.  There are three types of
nodes in the tree: AND and OR nodes where children are either predicate leaf
nodes or further conditional branches, and the predicate nodes defined by a
key, a comparison operator, and a value.  When evaluating the given key-value
dictionary representing the access entitlements of the user in question, the
predicate node is evaluated as whether its key is available in the access
dictionary and that the associated value matches that of the predicate node's.
The AND and OR nodes are evaluated based on how their children evaluate: an AND
node evaluates its children left-to-right and returns False on the first False,
otherwise True; an OR node evaluates to True on the first child that evaluates
True and False if none do.
"""
# TODO: needs to be tested for proper syntax evaluation
# Because who knows what sorts of nonsense people will enter for access strings

import re

basetok_re = re.compile('^(\\(|\\)|\\||&|[^\\)]+)')
predtok_re = re.compile('^(?P<key>\\w+)(?P<op>=)(?P<value>[^\\)]*)$')
valid_ops = ['=']

class Evaluator:

  class Node:

    def __init__(self):
      pass

    def evaluate(self, kv):
      raise NotImplementedError

  class Predicate(Node):

    def __init__(self, key, op, value):
      super().__init__()

      self._key = key
      self._op = op
      self._value = value

    def evaluate(self, kv):
      if self._op == '=':
        #return kv[self._key] == self._value
        # TODO: generalize with a specifiable comparison function
        return self._key in kv and self._value in kv[self._key]
      raise NotImplementedError(f"Comparison operator '{self._op}' not supported")

  # pylint: disable=abstract-method
  class Decision(Node):

    def __init__(self):
      super().__init__()
      self._children = []

    def add(self, node):
      self._children.append(node)

  class AndNode(Decision):

    def evaluate(self, kv):
      for node in self._children:
        if not node.evaluate(kv):
          return False
      return True

  class OrNode(Decision):

    def evaluate(self, kv):
      for node in self._children:
        if node.evaluate(kv):
          return True
      return False

  @classmethod
  def buildtree(cls, str):
    """
    Builds tree based on input string representing LDAP-like filter.
    """

    # parsing stack used to make tree, idk.
    stack = []
    while str:

      [tok, str] = basetok_re.split(str)[1:]

      if tok == '&':
        stack.append(cls.AndNode())
      elif tok == '|':
        stack.append(cls.OrNode())
      elif tok == '(':
        stack.append('(')
      elif tok == ')':
        node = stack.pop()
        dc = stack.pop()
        if dc != '(':
          raise Exception(f"Should not have seen '{dc}' on stack here")

        # last element on stack should be decision node (?); add this one as child
        if len(stack) > 0:
          stack[-1].add(node)
        else:  # first element was an open parenthesis, s'fine too
          stack.append(node)
      # Python 3.8+
      ## elif m := predtok_re.match(tok):
      ##   stack.append(cls.Predicate(m['key'], m['op'], m['value']))
      ## else:
      ##   raise Exception(f"Hi yeah unexpected {tok} with {str} remaining")
      else:
        m = predtok_re.match(tok)
        if m:
          stack.append(cls.Predicate(m['key'], m['op'], m['value']))
        else:
          raise Exception(f"Hi yeah unexpected {tok} with {str} remaining")

    # there should be one thing left on the stack
    if len(stack) > 1:
      # TODO: proper exception
      raise Exception(f"There is stuff left on the stack: {stack}")
    return stack.pop()

  def __init__(self, str):
    self._root = self.__class__.buildtree(str)

  def evaluate(self, kv):
    """
    Evaluate decision tree against the given dict `kv` using function `fn`.
    """
    if not self._root:
      raise Exception(
        "Bad call exception: should not call evaluate() before parse()"
      )
    return self._root.evaluate(kv)

def evaluate_access(restrictions, rights):
  evaluator = Evaluator(restrictions)
  return evaluator.evaluate(rights)
