from setuptools import setup

version = "0.0.1"

setup(
    name="consys-common",
    version=version,
    url="http://gitorious.org/neerc-linux/consys",
    namespace_packages=['consys'],
    packages=['consys.common', 'consys.common.ampi'],
    author="NEERC Linux group",
    author_email="acm-neerc@googlegroups.com"
)
