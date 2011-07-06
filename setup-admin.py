from setuptools import setup

version = "0.0.1"

setup(
    name="consys-admin",
    version=version,
    url="http://gitorious.org/neerc-linux/consys",
    namespace_packages=['consys'],
    packages=['consys.admin'],
    entry_points = {
        'console_scripts': [
            'consys-admin = consys.admin:run',
        ]
    },
    required_installs=['consys-common=={0}'.format(version)],
    author="NEERC Linux group",
    author_email="acm-neerc@googlegroups.com"
)
