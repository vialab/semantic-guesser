from . import findcut
from ..tree.default_tree import DefaultTree


t = DefaultTree()
t.insert(['ANIMAL', 'INSECT', 'bee'])
t.insert(['ANIMAL', 'INSECT', 'bee'])
t.insert(['ANIMAL', 'INSECT', 'bug'], 0)
t.insert(['ANIMAL', 'INSECT', 'insect'], 0)
t.insert(['ANIMAL', 'BIRD', 'bird'])
t.insert(['ANIMAL', 'BIRD', 'bird'])
t.insert(['ANIMAL', 'BIRD', 'bird'])
t.insert(['ANIMAL', 'BIRD', 'bird'])
t.insert(['ANIMAL', 'BIRD', 'crow'])
t.insert(['ANIMAL', 'BIRD', 'crow'])
t.insert(['ANIMAL', 'BIRD', 'eagle'])
t.insert(['ANIMAL', 'BIRD', 'eagle'])
t.insert(['ANIMAL', 'BIRD', 'swallow'], 0)

print findcut(t.root, t.root.value)