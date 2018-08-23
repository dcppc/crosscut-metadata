#!/usr/bin/env python3

# ------------------------------------------------------
# ccmm.util
# ------------------------------------------------------

# nested dicts not natively supported in Python3?
def make_multilevel_dict(items, keys):
    md = {}
    for item in items:
        d = md
        for k in keys[:-1]:
            kv = item[k]
            if kv not in d:
                d[kv] = {}
            d = d[kv]
        d[item[keys[-1]]] = item

    return md

# check whether a given key exists within a multilevel dict. Returns True or False.
def multilevel_dict_key_exists(d, key):
    for k in d:
        if k == key:
            return True
        v = d[k]
        if v is None:
            pass
        elif isinstance(v, str):
            pass
        elif multilevel_dict_key_exists(v, key):
            return True
    return False
