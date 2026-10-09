"""Mingyu policy wrapper; compiler implementation is shared."""
from shared_cloth import ROOT
from cloth_compiler.cook_cloth import main
if __name__=='__main__':main(ROOT/'tools/cloth_policy.json')
