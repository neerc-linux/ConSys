from setuptools import setup

version = "0.0.1"

setup(
    name="consys-server",
    version=version,
    url="http://gitorious.org/neerc-linux/consys",
    namespace_packages=['consys'],
    packages=['consys.server'],
    entry_points = {
        'console_scripts': [
            'consys-server = consys.server:run',
        ]
    },
    install_requires=['consys-common=={0}'.format(version)],
    author="NEERC Linux group",
    author_email="acm-neerc@googlegroups.com"
)
