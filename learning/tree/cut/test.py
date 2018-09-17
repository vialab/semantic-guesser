from . import li_abe
from . import wagner
from ..tree.default_tree import DefaultTree


#------------------------------------------------
# Test with data from Table 4 of Li & Abe (1998),
# where they use k+1 to calculate parameter
# description length. We use k (see Page 8),
# but it shouldn't affect the selection of cut.
#------------------------------------------------

t = DefaultTree()
t.insert(['ANIMAL', 'INSECT', 'bee'], 2)
t.insert(['ANIMAL', 'INSECT', 'bug'], 0)
t.insert(['ANIMAL', 'INSECT', 'insect'], 0)
t.insert(['ANIMAL', 'BIRD', 'bird'], 4)
t.insert(['ANIMAL', 'BIRD', 'crow'], 2)
t.insert(['ANIMAL', 'BIRD', 'eagle'], 2)
t.insert(['ANIMAL', 'BIRD', 'swallow'], 0)

print li_abe.findcut(t)
print wagner.findcut(t)


#------------------------------------------------
# Test with data from Figure 8 of Li & Abe (1998),
# should be consistent with our values.
#------------------------------------------------

t = DefaultTree()
t.insert(['ENTITY', 'ANIMAL', 'BIRD', 'swallow'], 4)
t.insert(['ENTITY', 'ANIMAL', 'BIRD', 'crow'], 4)
t.insert(['ENTITY', 'ANIMAL', 'BIRD', 'eagle'], 4)
t.insert(['ENTITY', 'ANIMAL', 'BIRD', 'bird'], 6)
t.insert(['ENTITY', 'ANIMAL', 'INSECT', 'bug'], 0)
t.insert(['ENTITY', 'ANIMAL', 'INSECT', 'bee'], 8)
t.insert(['ENTITY', 'ANIMAL', 'INSECT', 'insect'], 0)
t.insert(['ENTITY', 'ARTIFACT', 'VEHICLE', 'car'],  1)
t.insert(['ENTITY', 'ARTIFACT', 'VEHICLE', 'bike'], 0)
t.insert(['ENTITY', 'ARTIFACT', 'AIRPLANE', 'jet'], 4)
t.insert(['ENTITY', 'ARTIFACT', 'AIRPLANE', 'helicopter'], 0)
t.insert(['ENTITY', 'ARTIFACT', 'AIRPLANE', 'airplane'], 4)
print li_abe.findcut(t)
print wagner.findcut(t)