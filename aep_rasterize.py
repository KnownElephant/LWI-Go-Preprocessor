from hecras.hecgeometry import HecGeometry
from hecras.triangulation import Triangulation
from hecras.flowarea2d import FlowArea2D
from hecras.inversedistanceinterpolator import InverseDistanceInterpolator
from hecras.rasterformat import RasterFormat
from wse_extract import WSE_extract
from aep_calc import AEP_calc
import numpy as np
from matplotlib.tri import LinearTriInterpolator as mpl_LinearTriInterpolator
from matplotlib.tri import Triangulation as mpl_Triangulation
from scipy.interpolate import LinearNDInterpolator as scipy_LinearNDInterpolator
from osgeo import gdal
from pyproj import CRS
import os


class AEP_rasterize:
    """Class which handles extracting maximum WSE data from mini-hdf files and pulling aep values
    out of them to create raster files
    """
    def __init__(
            self,
            geometry_file: str,
            results_directory: str,
            weight_list_file: str,
            resolution: float,
            bounding_box: list,
            output_directory: str = "."
    ):
        """
        Constructor for the aep_rasterize object

        Args:
            geometry_file: a filepath to a .hdf file containing a hecras geometry
            results_directory: a filepath to a directory containing mini-hdf file outputs from
            HEC_RAS Runs
            weight_list_file: a filepaath to a .csv file containing the weights for each storm
            resolution: the resolution for the desired raster output
            bounding_box: the bounding box for the associated raster output
            output_directory: a filepath to the directory where the output files will be saved
        """
        self.__geometry = HecGeometry(geometry_file)
        self.__triangles = Triangulation(self.__geometry)
        self.__results_directory = results_directory
        self.__weight_list_file = weight_list_file
        self.__bounding_box = bounding_box
        self.__resolution = resolution
        self.__output_directory = output_directory
        self.__xmax = max(self.__bounding_box[0], self.__bounding_box[2])
        self.__xmin = min(self.__bounding_box[0], self.__bounding_box[2])
        self.__ymax = max(self.__bounding_box[1], self.__bounding_box[3])
        self.__ymin = min(self.__bounding_box[1], self.__bounding_box[3])
        self.__bounding_box = [self.__xmin, self.__ymin, self.__xmax, self.__ymax]
        self.__nx = int((self.__xmax - self.__xmin) / self.__resolution)
        self.__ny = int((self.__ymax - self.__ymin) / self.__resolution)
        self.__xx = np.linspace(self.__xmin, self.__xmax, self.__nx, endpoint=True)
        self.__yy = np.linspace(self.__ymin, self.__ymax, self.__ny, endpoint=True)
        self.__xg, self.__yg = np.meshgrid(self.__xx, self.__yy)

    def __construct_linear_tri_interpolator(
        self,
        flow_area: FlowArea2D,
        flow_area_index: int,
        results: np.ndarray,
    ) -> mpl_LinearTriInterpolator:
        """
        Construct a linear interpolator for the given variable and results
        Code take from hecras class (author zcobbell)

        Args:
            flow_area: Flow area object
            flow_area_index: Index of the flow area
            variable: Output variable
            results: Results array

        Returns:
            dict containing the triangulation and the interpolator
        """
        import copy
        import logging

        log = logging.getLogger(__name__)

        interpolated_results = flow_area.cell_array_to_facepoints(results)


        tri = copy.deepcopy(self.__triangles.mpl_triangulation(flow_area_index, True))

        log.info("Creating mask")
        tri_mask, tri_results = self.__triangles.create_mask(
            flow_area_index, interpolated_results, method="extend"
        )
        tri.set_mask(tri_mask)
        interpolator = mpl_LinearTriInterpolator(tri, tri_results)

        return interpolator
    
    def to_AEP_raster(
        self, 
        AEP: list
    ):
        """Creates rasters corresponding to AEP values for a set of storm runs

        Returns:
            None
        """
        from osgeo import gdal
        from pyproj import CRS
        import logging

        crs_4326 = CRS.from_epsg(4326)
        wkt = crs_4326.to_wkt()

        log = logging.getLogger(__name__)

        AEP_data_list=[]
        

        for i, flow_area in enumerate(self.__geometry.flow_areas()):
            wse_extract_flow_area = WSE_extract(flow_area, self.__results_directory)
            AEP_calc_flow_area = AEP_calc(wse_extract_flow_area, AEP, self.__weight_list_file)
            AEP_data = AEP_calc_flow_area.return_AEP()
            AEP_data_list.append(AEP_data)
        

        for j, AEP_value in enumerate(AEP):
            data_for_raster=[]
            for i, flow_area in enumerate(self.__geometry.flow_areas()):
                print("Constructing "+str(AEP_value)+" data for  "+flow_area.name())

                results = AEP_data_list[i].iloc[:,j].to_numpy()
                
                data_for_raster.append(
                    self.__construct_linear_tri_interpolator(
                        flow_area, i, results
                    )
                )
            print("Constructiong z data for "+str(AEP_value))
            z = data_for_raster[0](self.__xg, self.__yg)


            raster_filename = self.__output_directory+"/AEP_"+str(AEP_value)+"_wse.tif"
            if os.path.exists(raster_filename):
                os.remove(raster_filename)
            
            print("Writing raw results raster for "+str(AEP_value))
            driver = gdal.GetDriverByName("GTiff")
            outdata = driver.Create(
                raster_filename, self.__nx, self.__ny, 1, gdal.GDT_Float32
            )
            outdata.SetProjection(wkt)
            outdata.SetGeoTransform(
                [
                    self.__bounding_box[0],
                    self.__resolution,
                    0,
                    self.__bounding_box[3],
                    0,
                    -self.__resolution,
                ]
            )
            outdata.GetRasterBand(1).SetNoDataValue(np.nan)
            outdata.GetRasterBand(1).WriteArray(np.flipud(z))
            outdata.FlushCache()
            outdata = None


                
                