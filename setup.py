import email
from setuptools import setup, find_packages


setup(name='ftsa',
 version='1.0',
 author='Mohamad Mansouri',
 email='mohamad.mansouri@thalesgroup.com',
 packages=find_packages(),
 python_requires=">=3.6",
 install_requires=[
        'gmpy2',
        'pycryptodome',
        'ecdsa',
        'numpy',
        'matplotlib'
    ]
 )