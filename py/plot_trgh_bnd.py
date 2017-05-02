def convert_to_datetime(row):
    currDateStr = str( int( row["dateStr"] ) )
#     return currDateStr
    if row["timeStr"] < 10:
        currTimeStr = "000" + str( int( row["timeStr"] ) )
    elif row["timeStr"] < 100:
        currTimeStr = "00" + str( int( row["timeStr"] ) )
    elif row["timeStr"] < 1000:
        currTimeStr = "0" + str( int( row["timeStr"] ) )
    else:
        currTimeStr = str( int( row["timeStr"] ) )
    return datetime.datetime.strptime( currDateStr\
                    + ":" + currTimeStr, "%Y%m%d:%H%M" )

if __name__ == "__main__":
    """
    In the current code we'll check if our trgh bnd 
    pred is going well by plotting it for all SAPS 
    dates we have available.
    """
    import pandas
    import datetime
    import numpy
    import os
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    import seaborn as sns
    from davitpy.models import *
    from davitpy import utils
    # set some plotting details
    seaMap = ListedColormap(sns.color_palette("Spectral_r"))
    # cols for TEC data
    mfColList = [ "dateStr", "timeStr", "Mlat",\
              "Mlon", "med_tec", "dlat", "dlon" ]
    # Loop through the dir which contains med filt tec data
    # and get a list of all the files
    fltdTrghLocFname = "/home/bharat/Documents/code/tec-analysis/data/finTrghLocFltrd.txt"
    fltTecDataDF = pandas.read_csv(fltdTrghLocFname, sep=' ',\
                            parse_dates=["date"],\
                               infer_datetime_format=True)
    fltTecDataDF["AdjBndMlon"] = [ x if x <=180. else x-360. for x in fltTecDataDF["BndMlon"] ]
    for currTS in numpy.nditer(fltTecDataDF["date"].unique()):
        inpDT = datetime.datetime.utcfromtimestamp(currTS.astype(int)*1e-9)
        print "current Time--->", inpDT
        # Read actual median filtered tec data for the given date and time
        mfTecDir = "/home/bharat/Documents/medFiltTec/"
        for root, dirs, files in os.walk(mfTecDir):
            fileDtStr = inpDT.strftime("%y%m%d")
            for fName in files:
                if fName.find(fileDtStr) != -1:
                    fullTECFname = root + "/" + fName
        # Med filtered TEC data
        medFiltTECDF = pandas.read_csv(fullTECFname, delim_whitespace=True,\
                                    header=None, names=mfColList)
        medFiltTECDF["date"] = medFiltTECDF.apply( convert_to_datetime, axis=1 )
        selTecDF = medFiltTECDF[ medFiltTECDF["date"] == inpDT ].reset_index(drop=True)
        # Plot the figure
        f = plt.figure(figsize=(12, 8))
        ax = f.add_subplot(1,1,1)
        m1 = utils.plotUtils.mapObj(boundinglat=30., gridLabels=True, coords="mag", ax=ax, datetime=inpDT)
        xVec, yVec = m1(list(selTecDF["Mlon"]), list(selTecDF["Mlat"]), coords="mag")
        # get the corresponding boundaries
        selBndDF = fltTecDataDF[ fltTecDataDF["date"] == inpDT ].reset_index(drop=True)
        xVecEquBnd, yVecEquBnd = m1(list(selBndDF["BndMlon"]), list(selBndDF["BndEquMlat"]), coords="mag")
        xVecPolBnd, yVecPolBnd = m1(list(selBndDF["BndMlon"]), list(selBndDF["BndPolMlat"]), coords="mag")
        xVecMinTrghBnd, yVecMinTrghBnd = m1(list(selBndDF["BndMlon"]), list(selBndDF["minTecMlat"]), coords="mag")        
        tecPlot = m1.scatter( xVec, yVec , c=selTecDF["med_tec"], s=40.,\
           cmap=seaMap, alpha=0.7, zorder=5., \
                     edgecolor='none', marker="s", vmin=0., vmax=20. )

        eqPlot = m1.scatter( xVecEquBnd, yVecEquBnd , s=10.,\
                             c='y', marker="^", zorder=7. )
        poPlot = m1.scatter( xVecPolBnd, yVecPolBnd , s=10.,\
                             c='y', marker="v", zorder=7. )
        mtPlot = m1.scatter( xVecMinTrghBnd, yVecMinTrghBnd , s=15.,\
                             c='r', marker="*", zorder=7. )

        cbar = plt.colorbar(tecPlot, orientation='vertical')
        cbar.set_label('TEC', size=15)
        plotFileName = "/home/bharat/Documents/tec-plots/maps/tec-bnd-map-" + inpDT.strftime("%Y%m%d-%H%M") + ".png"
        ax.get_figure().savefig(plotFileName,bbox_inches='tight')
        plt.close(f)