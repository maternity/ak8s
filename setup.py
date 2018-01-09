from setuptools import find_packages
from setuptools import setup


if __name__ == '__main__':
    setup(
            name='ak8s',
            version='0.1.0',
            description='asyncio Kubernetes API client',
            author='Kai Groner',
            author_email='kai@gronr.com',
            packages=find_packages(),
            install_requires=[
                'aiohttp>=2.3',
                'pyyaml>=3.12',
            ],
            python_requires='~=3.6',
            classifiers=[
                #'License :: OSI Approved :: MIT License',
                'Development Status :: 3 - Alpha',
                'Programming Language :: Python :: 3.6',
            ])
