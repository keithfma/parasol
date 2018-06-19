"""
Raster data handlers
"""

from parasol import lidar


logger = logging.getLogger(__name__)


# def connect_db(dbname=LIDAR_DB):
#     """
#     Return connection to lidar DB and return cursor
# 
#     Arguments:
#         dbname: string, database name to connect to
# 
#     Returns: psycopg2 connection object
#     """
#     conn = pg.connect(dbname=dbname, user=PSQL_USER, password=PSQL_PASS,
#         host=PSQL_HOST, port=PSQL_PORT)
#     return conn
#     
# 
# def create_db(clobber=False):
#     """
#     Create a new database and initialize for lidar point data
# 
#     Arguments:
#         clobber: set True to delete and re-initialize an existing database
# 
#     Return: Nothing
#     """
#     # TODO: add indexes as needed
#     # connect to default database
#     with connect_db('postgres') as conn:
#         conn.set_isolation_level(pg.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
#         cur = conn.cursor()
#         if clobber:
#             logger.info(f'Dropped existing database: {LIDAR_DB} @ {PSQL_HOST}:{PSQL_PORT}')
#             cur.execute(f'DROP DATABASE IF EXISTS {LIDAR_DB}');
#         cur.execute(f'CREATE DATABASE {LIDAR_DB};')
#     # init new database
#     with connect_db() as conn:
#         cur = conn.cursor()
#         cur.execute('CREATE EXTENSION postgis;')
#         cur.execute('CREATE EXTENSION pointcloud;')
#         cur.execute('CREATE EXTENSION pointcloud_postgis;')
#         cur.execute(f'CREATE TABLE {LIDAR_TABLE} (id SERIAL PRIMARY KEY, pa PCPATCH(1));')
#     logger.info(f'Created new database: {LIDAR_DB} @ {PSQL_HOST}:{PSQL_PORT}')


def grid_points(xmin, xmax, ymin, ymax, grnd=False):
    """
    Grid scattered points using kNN median filter

    Arguments:
        xmin, xmax, ymin, ymax: floats, limits for bounding box 
        grnd: set True to compute surface from ground returns, False to compute
            surface from (first) non-ground returns
    
    Returns: ?
    """
    # constants
    RESOLUTION = 1 # meters

    # build output grid spanning bbox
    x_vec = np.arange(math.ceil(xmin), math.floor(xmax), RESOLUTION)   
    y_vec = np.arange(math.ceil(ymin), math.floor(ymax), RESOLUTION)   
    x_grd, y_grd = np.meshgrid(x_vec, y_vec)

    # retrieve data
    pts = lidar.retrieve(xmin, ymin, xmax, ymax)

    # filter for ground returns
    mask = np.zeros(len(pts)) 
    if grnd:
        # extract ground points
        for idx, pt in enumerate(pts):
            if pt[3] == pt[4]  and pt[5] == 2:
                # last or only return, classified as "ground"
                mask[idx] = 1
    else:
        # extract upper surface points
        for idx, pt in enumerate(pts):
            if (pt[3] == 1 or pt[4] == 1) and pt[5] == 1:
                # first or only return, classified as "default"
                mask[idx] = 1
    pts = np.extract(mask, pts)

    # extract [x, y] and z arrays
    npts = len(pts)
    xy = np.zeros((npts, 2))
    zz = np.zeros(npts)
    for idx, pt in enumerate(pts):
        xy[idx, 0] = pt[0]
        xy[idx, 1] = pt[1]
        zz[idx] = pt[2]

    # construct KDTree
    tree = cKDTree(xy) 

    # find NN for all grid points
    xy_grd = np.hstack([x_grd.reshape((-1,1)), y_grd.reshape((-1,1))])
    nn_dist, nn_idx = tree.query(xy_grd, k=16)

    # compute local medians
    z_grd = np.median(zz[nn_idx], axis=1).reshape(x_grd.shape)
    
    # DEBUG: make a quick plot of the results
    plt.imshow(z_grd, cmap='hot', interpolation='nearest')
    plt.show()

    return x_vec, y_vec, z_grd  # TODO: decide what outputs I need
