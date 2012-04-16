from distutils.core import setup

setup(
    name = "django-comet",
    version = "0.1.0",
    author = "Ziyan Zhou",
    author_email = "zhou@ziyan.info",
    description = "Django comet server based on tornado and redis",
    #download_url = "",
    url = "https://github.com/ziyan/django-comet",
    packages=[
        'comet',
        'comet.management',
        'comet.management.commands',
    ],
    platforms=['any'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities'
    ],
)
