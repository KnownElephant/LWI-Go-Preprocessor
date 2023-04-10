import pandas as pd
import h5py
import os
from hecras.flowarea2d import FlowArea2D

class WSE_extract:
    """Class which handles extracting maximum WSE data from mini-hdf files and stitching them into
    a single pandas dataframe with grid cell points as rows and HEC-RAS runs as columns

    To Do: Update code to check whether a file in the directory is a .hdf before trying to read it
    """
    def __init__(
            self,
            flow_area: FlowArea2D,
            directory: str
    ):
        """Constructor for the WSE_extract object
        Args:
            flow_area: A FlowArea2D object from the hecras class which specifies which flow area in a
            mini-hdf file to extract from
            directory: a directory containing mini-hdf files for multiple hec-ras runs in a given area
        """
        self.__flow_area = flow_area
        self.__directory = directory
        self.__files_list = os.listdir(directory)
    
    
    def extract(self)-> pd.DataFrame:
        """Reads the files from specified directory and places them in a pd.DataFrame
        Returns:
            pd.DataFrame
        """
        print("Extracting for "+self.__flow_area.name())
        wse_data=pd.DataFrame()
        for file in self.__files_list:
            with h5py.File(self.__directory+"/"+file, "r") as f:
                wse = f['Results/Unsteady/Output/Output Blocks/Base Output/Unsteady Time Series/2D Flow Areas/'+self.__flow_area.name()+'/Max Values/Water Surface'][:]
                wse_data[file] = wse
        return wse_data
            

    