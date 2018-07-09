from setuptools import setup, find_packages

setup(
    name='parasol',
    version='0.2.1',
    description='Parasol - Optimizing navigation for comfortable outdoor travel',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'wget',
        'requests',
        'flask',
        'psycopg2',
        'numpy', # note: pdal requires this be installed first
        'cython', # ditto
        'packaging', # ditto 
        'scipy',
        'pyproj',
        'numpy',
        'shapely',
        'psycopg2',
        'matplotlib',
        ],
    entry_points={
        'console_scripts': [
            'parasol-server=parasol.server:cli',
            'parasol-init-apache=parasol.server:deploy',
            'parasol-init-lidar=parasol.lidar:initialize_cli',
            'parasol-init-surface=parasol.surface:initialize_cli',
            'parasol-init-shade=parasol.shade:initialize_cli',
            'parasol-update-shade=parasol.shade:update_cli',
            'parasol-init-geoserver=parasol.geoserver:initialize_geoserver_cli',
            'parasol-init-osm=parasol.osm:initialize_cli',
            'parasol-update-osm=parasol.osm:update_cli',
            ]
        }
    )
