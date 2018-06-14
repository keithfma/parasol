from setuptools import setup, find_packages

setup(
    name='parasol_mvp',
    version='0.0.0',
    description='Parasol - Minimal Viable Product Edition',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'wget',
        'requests',
        'flask',
        ],
    entry_points={
        'console_scripts': [
            'parasol-mvp=parasol_mvp.server:cli'
            ]
        }
    )
