#! /usr/bin/python2.7
""" Component represents artifact type defined by name, code and set of regexes. This concept is probably is very close to checkums' CiType (and in fact it's used internally) and probably should be merged into it. """


from checksums import models


class Component(object):
    def __init__(self, sname, fname, stubs):
        self.short_name=sname
        self.full_name=fname
        self.stubs=stubs

    def get_templates(self, version_start):
        version=version_start+"[^:]*"
        return [self.preprocess_template(stub, version)
                for stub in self.stubs]

    #placeholders cancelled since they give no flexibility in regexp
    #_VERSION_ is the only one left
    def preprocess_template(self, stub, version):
        placeholders={ #".": "\.", # in stub dot means exactly dot
                       #"_CLIENT_": "[A-Z0-9_]+?",
                       #"_BRANCHES_": "branches-[a-zA-Z0-9_\-]+?",
                       "_VERSION_": version,
                       #"_ANY_": "[a-zA-Z0-9_\-]+?",
        }
        template = stub
        for ph in placeholders.keys():
            template=template.replace(ph, placeholders[ph])
        return template

    def get_all_names(cls):
        return [(item.short_name, item.full_name)
                for item in cls.get_all_components()];  

    @classmethod
    def _get_regexp_list( self, obj_component ):
        obj_loc_type = models.LocTypes.objects.get( code = "NXS" );

        ls_regexp = list();
        for obj_regexp in models.CiRegExp.objects.filter( loc_type = obj_loc_type, ci_type = obj_component ) :
            if ( obj_regexp.regexp is not None and len( obj_regexp.regexp ) > 0 ):
                ls_regexp.append( obj_regexp.regexp );

        return ls_regexp;

    @classmethod
    def get_component( self, str_code ):
        obj_component = models.CiTypes.objects.get( code = str_code );
        return Component( obj_component.code, obj_component.name, self._get_regexp_list( obj_component ) );

    @classmethod
    def get_all_components(self, cls):
        #load components from database
        components=[];

        #get CiTypes (components) list
        for obj_component in models.CiTypes.objects.all().order_by( '-is_standard', 'name' ):
            components.append( Component ( obj_component.code, obj_component.name, cls._get_regexp_list( obj_component ) ) );

        # a little trick: 'FILE' is to be a first value in the list
        obj_component = components [ map( lambda x: x.short_name == "FILE", components ).index( True ) ];
        components.remove( obj_component );
        components.insert( 0, obj_component );

        return components;

