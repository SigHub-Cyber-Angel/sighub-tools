import setuptools

long_description = ""
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='sighub.jsondb',
    version='0.1.0',
    author='James Hulka',
    author_email='james@sighub.io',
    description='A TinyDB wrapper (https://github.com/msiemens/tinydb)'  \
                'providing log database and configuration database functionality.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/SigHub-Cyber-Angel/sighub-tools',
    project_urls={
        "Bug Tracker": "https://github.com/SigHub-Cyber-Angel/sighub-tools/issues"},
    license='MIT',
    packages=['sighub'],
    install_requires=['tinydb'],
)
