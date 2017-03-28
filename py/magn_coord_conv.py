def convert_to_mlt(row):
    mlt, mlat = utils.coord_conv( row['glon'], row['gdlat'], \
                                 "geo", "mlt", altitude=300., \
                                 date_time=row['date'] )
    return mlt, mlat

if __name__ == "__main__":
    import pandas
    import datetime
    import numpy
    from davitpy.models import *
    from davitpy import utils
    import os
    baseDir = "../data/"
    # Loop through the directory and get all files
    for root, dirs, files in os.walk(baseDir):
        for fName in files:
            print "currently working with-->", root + fName
            # Read the data into a DF using pandas
            dataDF = pandas.read_hdf(inpTecFile, 'Data/Table Layout')
            dataDF["date"] = pandas.to_datetime(dataDF["year"]*10000000000 +\
                                                dataDF["month"]*100000000 + dataDF["day"]*1000000 +\
                                                dataDF["hour"]*10000 + dataDF["min"]*100 +\
                                                dataDF["sec"],format='%Y%m%d%H%M%S')
            dataDF["mlt"], dataDF["mlat"] = zip( *dataDF.apply( convert_to_mlt, axis=1 ) )