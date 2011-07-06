from setuptools import setup

version = "0.0.1"

setup(
    name="consys-client",
    version=version,
    url="http://gitorious.org/neerc-linux/consys",
    namespace_packages=['consys'],
    packages=['consys.client'],
    entry_points = {
        'console_scripts': [
            'consys-client = consys.client:run',
        ]
    },
    required_installs=['consys-common=={0}'.format(version)],
    author="NEERC Linux group",
    author_email="acm-neerc@googlegroups.com"
)
