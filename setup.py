from distutils.core import setup

setup(
    name='ipython_doctester',
    author='Catherine Devlin',
    author_email='catherine.devlin@gmail.com',
    version='0.1.0',
    url='http://pypi.python.org/pypi/ipython_doctester/',
    packages=['towelstuff',],
    license='MIT',
    description='Run doctests in individual IPython Notebook cells',
    long_description=open('README.txt').read(),
    install_requires=[
        "ipython >= 0.13",
        ]
)
