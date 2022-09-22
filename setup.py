from distutils.core import setup
import os

setup(
    name='vaktin',
    version='0.0.4',  # Required
    package_dir={'vaktin': 'vaktin'},
    packages=find_packages(),
    package_data={'': ['*.json', '*.pyx']},

    description='PC build and price monitor.',  # Optional
    author='Adam Hart Runarsson',  # Optional

    include_package_data=True,
    include_dirs=[numpy.get_include()],
    python_requires='>=3.6',
    install_requires=[
        'beautifulsoup4',
        'pandas',
        'dash',
        'dash_bootstrap_components'
    ]
)

