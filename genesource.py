#!/usr/bin/env python


def import_sphinx():
    """Import sphinx so that some directives/roles are registered."""
    try:
        import sphinx.directives
        import sphinx.roles
        return sphinx
    except:
        pass


def get_sphinx_app(dummydir=None):
    """Return Sphinx app object (to get some additional directives)."""
    import os
    from sphinx.application import Sphinx
    if dummydir is None:
        dummydir = os.path.join(os.path.dirname(__file__), "tmp")
    srcdir = outdir = doctreedir = dummydir
    confdir = None
    buildername = "pickle"
    app = Sphinx(
        srcdir, confdir, outdir, doctreedir, buildername,
        status=None, freshenv=True)
    return app


class InfoGetter(object):

    def __init__(self):
        self.directives = []
        self.roles = []

    def _add_directive(self, dirname, clsobj):
        self.directives.append({
            'directive': dirname,
            'option': list(clsobj.option_spec if clsobj.option_spec else []),
            })

    def getinfo(self):
        """ Set the value of `self.directives` and `self.roles`."""
        raise NotImplementedError


class InfoGetterSphinx(InfoGetter):

    def __init__(self):
        super(InfoGetterSphinx, self).__init__()
        self.domains = []

    def add_domain(self, domain):
        self.domains.append(domain)

    def _getinfo_domain(self, domain):
        """Get directive and role information from `domain`."""
        domname = domain.name
        if domname == "std":
            genename = lambda x: x
        else:
            genename = lambda x: ":".join([domname, x])
        for (dirname, clsobj) in domain.directives.iteritems():
            self._add_directive(genename(dirname), clsobj)
        self.roles.extend(map(genename, domain.roles))

    def getinfo(self):
        map(self._getinfo_domain, self.domains)


def get_sphinx_domain_directive_specs_and_roles():
    """Get ``DOMAIN:NAME`` type directives and roles from Sphinx"""
    from sphinx.domains import BUILTIN_DOMAINS
    ig = InfoGetterSphinx()
    map(ig.add_domain, BUILTIN_DOMAINS.itervalues())
    ig.getinfo()
    return (ig.directives, ig.roles)


class InfoGetterDocutils(InfoGetter):

    @staticmethod
    def get_directives_sub_modules():
        """
        Do ``from docutils.parsers.rst.directives import body, images, ...``

        This returns a top level object, so

          getattr(get_directives_sub_modules(), "body")

        returns the body module object.

        See: http://docs.python.org/library/functions.html#__import__

        """
        from docutils.parsers.rst import directives
        sub_module_names = list(set(
            m for (d, (m, c)) in directives._directive_registry.iteritems()))
        sub_modules = __import__(
            directives.__name__, globals(), locals(), sub_module_names, -1)
        return sub_modules

    def _getinfo_directives(self):
        from docutils.parsers.rst import directives
        sub_modules = self.get_directives_sub_modules()

        for (dirname, (modname, clsname),
             ) in directives._directive_registry.iteritems():
            clsobj = getattr(getattr(sub_modules, modname), clsname)
            self._add_directive(dirname, clsobj)

        for (dirname, clsobj) in directives._directives.iteritems():
            self._add_directive(dirname, clsobj)

    def _getinfo_roles(self):
        from docutils.parsers.rst import roles
        from docutils.parsers.rst.languages import en
        role_registry = {}
        role_registry.update(roles._roles)
        role_registry.update(roles._role_registry)
        role_registry.update(
            (a, role_registry[r]) for (a, r) in en.roles.iteritems())

        unimplemented = roles.unimplemented_role
        self.roles = sorted(
            r for (r, f) in role_registry.iteritems()
            if f is not unimplemented)

    def getinfo(self):
        self._getinfo_directives()
        self._getinfo_roles()


def genelisp():
    import jinja2

    igdoc = InfoGetterDocutils()
    igdoc.getinfo()

    (sphinx_directive_specs, sphinx_role_list,
    ) = get_sphinx_domain_directive_specs_and_roles()

    env = jinja2.Environment()
    template = env.from_string(TEMP_SOURCE)
    print template.render(
        roles=igdoc.roles + sphinx_role_list,
        directive_specs=igdoc.directives + sphinx_directive_specs,
        )


TEMP_SOURCE = r"""
(defun auto-complete-rst-directives-candidates ()
  '({% for spec in directive_specs %}"{{ spec.directive }}::" {% endfor %}))

(defun auto-complete-rst-roles-candidates ()
  '({% for item in roles %}"{{ item }}:" {% endfor %}))

{% for spec in directive_specs -%}
(puthash "{{ spec.directive }}"
         '({% for item in spec.option %}"{{ item }}:" {% endfor %})
         auto-complete-rst-directive-options-map)
{% endfor %}
"""


def main():
    from argparse import ArgumentParser

    parser = ArgumentParser(
        description="Generate source from rst file")
    args = parser.parse_args()

    import_sphinx()
    try:
        get_sphinx_app()
    except:
        pass

    genelisp(**vars(args))


if __name__ == '__main__':
    main()
