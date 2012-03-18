#!/usr/bin/env python

try:
    # these imports register directives/roles defined in sphinx
    import sphinx.directives
    import sphinx.roles
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


def get_sphinx_domain_directive_specs_and_roles():
    """Get ``DOMAIN:NAME`` type directives and roles from Sphinx"""
    from sphinx.domains import BUILTIN_DOMAINS
    directive_specs = []
    role_list = []

    def directive_specs_add(dirname, clsobj):
        directive_specs.append({
            'directive': dirname,
            'option': list(clsobj.option_spec if clsobj.option_spec else []),
            })

    for (domname, domain) in BUILTIN_DOMAINS.iteritems():
        if domname == "std":
            genename = lambda x: x
        else:
            genename = lambda x: ":".join([domname, x])
        for (dirname, clsobj) in domain.directives.iteritems():
            directive_specs_add(genename(dirname), clsobj)
        role_list.extend(map(genename, domain.roles))

    return (directive_specs, role_list)


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


def get_directive_specs():
    from docutils.parsers.rst import directives
    sub_modules = get_directives_sub_modules()
    directive_specs = []

    def directive_specs_add(dirname, clsobj):
        directive_specs.append({
            'directive': dirname,
            'option': list(clsobj.option_spec if clsobj.option_spec else []),
            })

    for (dirname, (modname, clsname),
         ) in directives._directive_registry.iteritems():
        clsobj = getattr(getattr(sub_modules, modname), clsname)
        directive_specs_add(dirname, clsobj)

    for (dirname, clsobj) in directives._directives.iteritems():
        directive_specs_add(dirname, clsobj)

    return directive_specs


def get_roles():
    from docutils.parsers.rst import roles
    from docutils.parsers.rst.languages import en
    role_registry = {}
    role_registry.update(roles._roles)
    role_registry.update(roles._role_registry)
    role_registry.update(
        (a, role_registry[r]) for (a, r) in en.roles.iteritems())

    unimplemented = roles.unimplemented_role
    return sorted(
        r for (r, f) in role_registry.iteritems() if f is not unimplemented)


def genelisp():
    import jinja2

    directive_specs = get_directive_specs()
    role_list = get_roles()

    (sphinx_directive_specs, sphinx_role_list,
    ) = get_sphinx_domain_directive_specs_and_roles()

    env = jinja2.Environment()
    template = env.from_string(TEMP_SOURCE)
    print template.render(
        roles=role_list + sphinx_role_list,
        directive_specs=directive_specs + sphinx_directive_specs,
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

    try:
        get_sphinx_app()
    except:
        pass

    genelisp(**vars(args))


if __name__ == '__main__':
    main()
