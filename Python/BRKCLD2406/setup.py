from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='BRKCLD2406',
      version='1.0',
      description='BRKCLD-2406',
      long_description='CLUS Orlando 2018 BRKCLD-2406 Session.',
      keywords='CLUS Orlando BRKCLD 2406',
      url='http://github.com/dcmattyg/BRKCLD-2406',
      author='Matthew Garrett',
      author_email='matgarre@cisco.com',
      license='MIT',
      packages=['BRKCLD2406'],
      install_requires=[
          'pathlib',
          'requests'
      ],
      include_package_data=True,
      zip_safe=False)
