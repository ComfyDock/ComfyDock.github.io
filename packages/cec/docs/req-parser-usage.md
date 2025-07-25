This is a small Python module for parsing Pip requirement files.

The goal is to parse everything in the Pip requirement file format spec.

Installation
pip install requirements-parser
or

poetry add requirements-parser
Examples
requirements-parser can parse a file-like object or a text string.

>>> import requirements
>>> with open('requirements.txt', 'r') as fd:
...     for req in requirements.parse(fd):
...         print(req.name, req.specs)
Django [('>=', '1.11'), ('<', '1.12')]
six [('==', '1.10.0')]
It can handle most (if not all) of the options in requirement files that do not involve traversing the local filesystem. These include:

editables (-e git+https://github.com/toastdriven/pyelasticsearch.git]{.title-ref})
version control URIs
egg hashes and subdirectories ([\#egg=django-haystack&subdirectory=setup]{.title-ref})
extras ([DocParser[PDF]]{.title-ref})
URLs

Welcome to Requirements Parser's documentation!
===============================================

Requirements parser is a Python module for parsing Pip_ requirement files.

.. _Pip: http://www.pip-installer.org

Requirements parser is (now) `Apache 2.0`_ licensed.

.. _Apache 2.0: https://www.apache.org/licenses/LICENSE-2.0

Quickstart:

.. code-block:: python

    import requirements

    reqfile = """
    Django>=1.5,<1.6
    DocParser[PDF]==1.0.0
    """

    for req in requirements.parse(reqfile):
        print(req.name, req.specs, req.extras)

Will output:

::

    Django [('>=', '1.5'), ('<', '1.6')] []
    DocParser [('==', '1.0.0')] ['pdf']


Usage
=====

Requirements parser works very similarly to the way pip actually parses requirement files except that pip typically
proceeds to install the relevant packages.

Requirements come in a variety of forms such as requirement specifiers (such as requirements>=0.0.5), version control
URIs, other URIs and local file paths.

Parsing requirement specifiers
------------------------------

.. code-block:: python

    import requirements
    req = "django>=1.5,<1.6"
    parsed = list(requirements.parse(req))[0]
    parsed.name       # django
    parsed.specs      # [('>=', '1.5'), ('<', '1.6')]
    parsed.specifier  # True

Parsing version control requirements
------------------------------------

.. code-block:: python

    req = "-e git+git://github.com/toastdriven/django-haystack@259274e4127f723d76b893c87a82777f9490b960#egg=django_haystack"
    parsed = list(requirements.parse(req))[0]
    parsed.name      # django_haystack
    parsed.vcs       # git
    parsed.revision  # 259274e4127f723d76b893c87a82777f9490b960
    parsed.uri       # git+git://github.com/toastdriven/django-haystack
    parsed.editable  # True (because of the -e option)


Parsing local files
-------------------

.. code-block:: python

    req = "-e path/to/project"
    parsed = list(requirements.parse(req))[0]
    parsed.local_file    # True
    parsed.path          # path/to/project