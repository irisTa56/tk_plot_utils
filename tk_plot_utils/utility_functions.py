"""Submodule containing utility functions."""

import copy as cp

def merged_dict(dct, merge_dct):
  """Makes a new dictionary by merging two dictionaries.

  Return a *new* merged dictionary initially *deep-copied* from
  the first given dictionary; the given two dictionaries stay unchanged.

  Parameters:

  dct: dict
    The first dictionary to be merged. If some of its keys are also in
    the second dictionary, the corresponding values will be overwritten.

  merge_dct: dict
    The second dictionary to be merged.

  """
  tmp = cp.deepcopy(dct)
  _merge_dict(tmp, merge_dct)
  return tmp

def _merge_dict(dct, merge_dct):
  """Recursive part of ``merged_dict()``."""
  for k, v in merge_dct.items():
    if (k in dct and isinstance(dct[k], dict) and isinstance(v, dict)):
      _merge_dict(dct[k], v)
    else:
      dct[k] = v
