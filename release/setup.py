from setuptools import setup, find_packages

setup(
    name='parasol',
    version='0.1.0',
    description='Parasol - Optimizing navigation for comfortable outdoor travel',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'wget',
        'requests',
        'flask',
        'psycopg2',
        'numpy',
        'scipy',
        'pdal',
        'pyproj',
        ],
    entry_points={
        'console_scripts': [
            'parasol-server=parasol.server:cli',
            'parasol-init-lidar=parasol.lidar:initialize_cli',
            'parasol-init-surface=parasol.surface:initialize_cli',
            'parasol-init-osm=parasol.osm:initialize_cli',
            ]
        }
    )
