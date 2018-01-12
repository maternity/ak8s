from pathlib import Path
from setuptools import setup


if __name__ == '__main__':
    setup(
            name='ak8s',
            version='0.1.5',
            description='asyncio Kubernetes API client',
            author='Kai Groner',
            author_email='kai@gronr.com',
            packages={
                str(py.parent).replace('/', '.')
                for py in Path('ak8s').rglob('*.py') },
            install_requires=[
                'aiohttp>=2.3',
                # YAML is needed to read kubeconfig only, could be optional
                # when using a pod serviceaccount.
                'pyyaml>=3.12',
            ],
            package_data={
                'ak8s.data': ['release-*.json'],
            },
            python_requires='~=3.6',
            classifiers=[
                #'License :: OSI Approved :: MIT License',
                'Development Status :: 3 - Alpha',
                'Programming Language :: Python :: 3.6',
            ])
