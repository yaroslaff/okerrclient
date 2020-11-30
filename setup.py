from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='okerrclient',
    version='2.0.163',
    description='client for okerr cloud monitoring system',
    long_description=long_description,
    long_description_content_type="text/markdown",    
    url='https://github.com/yaroslaff/okerr-dev',
    author='Yaroslav Polyakov',
    author_email='xenon@sysattack.com',
    license='MIT',
    packages=['okerrclient', 'okerrclient.pyping'],
    scripts=['scripts/okerrclient'],
    data_files = [
        ('okerrclient/conf',['data/conf/okerrclient.conf']),
        ('okerrclient/init.d', ['data/init.d/okerrclient']),
        ('okerrclient/systemd',['data/systemd/okerrclient.service']),
    ], 
    install_requires=['six', 'requests', 'evalidate', 'python-daemon', 'configargparse', 'fasteners', 'okerrupdate>=1.1.17','psutil'],
    include_package_data = True,
    zip_safe=False
)    

