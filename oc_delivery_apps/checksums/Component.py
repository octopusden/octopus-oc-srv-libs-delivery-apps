#!/usr/bin/env python3
"""
Component represents artifact type defined by name, code and set of regexes. 
This concept is probably is very close to checkums' CiType (and in fact it's used internally) and probably should be merged into it.
"""


from . import models


class Component(object):
    def __init__(self, ci_type):
        self.short_name = ci_type.code
        self.full_name = ci_type.name
        self.stubs = self._get_regexp_list(ci_type)

    def get_templates(self, version_start):
        version = version_start+"[^:]*"
        return [self.preprocess_template(stub, version)
                for stub in self.stubs]

    def preprocess_template(self, stub, version):
        placeholders = {"_VERSION_": version}
        template = stub
        for ph in placeholders.keys():
            template = template.replace(ph, placeholders[ph])
        return template


    def _get_regexp_list(self, ci_type):
        _loc_type = models.LocTypes.objects.get(code="NXS")
        _regexps = list(map(lambda x: x.regexp, models.CiRegExp.objects.filter(loc_type=_loc_type, ci_type=ci_type)))
        _regexps = list(filter(lambda x: bool(x) and isinstance(x, str), _regexps))
        return _regexps

def get_all_components(self, cls):
    # load components from database
    # little trick: 'FILE' is to be first in the list
    # we should raise an exception if no such type in the database, so do not catch it
    _file = models.CiTypes.objects.get(code="FILE")
    _result = list(map(lambda x: x), models.CiTypes.objects.filter(code__ne=="FILE").order_by('-is_standard', 'name')))
    _result = [_file] + list(map(lambda x: Component(x), _result))
    return _result

def get_all_names(cls):
    return [(item.short_name, item.full_name) for item in get_all_components()]
