import copy as cp

def merged_dict(dct, merge_dct):
  tmp = cp.deepcopy(dct)
  _merge_dict(tmp, merge_dct)
  return tmp

def _merge_dict(dct, merge_dct):
  for k, v in merge_dct.items():
    if (k in dct and isinstance(dct[k], dict) and isinstance(v, dict)):
      _merge_dict(dct[k], v)
    else:
      dct[k] = v
