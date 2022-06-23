import setuptools

long_description = ""
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='sighub.twisted',
    version='1.0.0',
    author='James Hulka',
    author_email='james@sighub.io',
    description='Wrapper functions and classes for common patterns used with the Twisted framework (https://twistedmatrix.com)',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/SigHub-Cyber-Angel/sighub-tools',
    project_urls={
        "Bug Tracker": "https://github.com/SigHub-Cyber-Angel/sighub-tools/issues"},
    license='MIT',
    packages=['sighub'],
    install_requires=['twisted'],
)
