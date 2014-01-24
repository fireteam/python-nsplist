from setuptools import setup

with open('README', 'r') as f:
    LONG_DESCRIPTION = f.read()


setup(
    name='nsplist',
    version='0.1',
    url='http://fireteam.net',
    author='Fireteam Ltd.',
    description='''A parser for NextStep-style plists.''',
    long_description=LONG_DESCRIPTION,
    license='MIT License',
    classifiers=[
        'Intended Audience :: Developers',
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    packages=['nsplist'],
    include_package_data=True,
)
