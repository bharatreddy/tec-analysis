if __name__ == "__main__":
    import locateTrough
    import datetime
    inpDT = datetime.datetime( 2011, 4, 9, 8, 40 )
    trObj = locateTrough.TroughLocator( inpDT, "/home/bharat/Documents/AllTec/" )
    medFltrdTec = trObj.apply_median_filter()
    print "----------------------------med filtered tec values---------------------"
    print medFltrdTec["tec"].min(), medFltrdTec["tec"].max(), medFltrdTec["tec"].mean(), medFltrdTec["tec"].std()
    trLocDF = trObj.find_trough_loc(medFltrdTec)
    print "------------------raw trough----------------------"
    print trLocDF.head()
    fltrdTrghLocDF = trObj.filter_trough_loc(trLocDF)
    print "------------------filtered trough----------------------"
    print fltrdTrghLocDF.head()
    # trObj.plotTecLocTrgh( trLocDF, medFltrdTec, \
    #     "../figs/raw-trough-loc-" + inpDT.strftime("%Y%m%d-%H%M") + ".pdf")
    # trObj.plotTecLocTrgh( fltrdTrghLocDF, medFltrdTec, \
    #     "../figs/fltrd-trough-loc-" + inpDT.strftime("%Y%m%d-%H%M") + ".pdf")

class TroughLocator(object):
    """
    A class to identify the location of TEC trough
    given a time instance. We use the 5 min, 1 dg GLAT,
    GLON binned TEC data file the one from madrigal!
    """
    def __init__(self, inpDate, tecDataDir):
        import datetime
        import numpy
        import pandas
        # setup some variables used later
        # base directory where all tec files are stored
        self.tecDataDir = tecDataDir
        # input time used else where
        self.inpDate = inpDate
        # for hdf5 files we need provide where table is stored in the file
        # with TEC files it is mostly as shown below
        self.tableLoc = 'Data/Table Layout'
        # choose columns we need to store from the tec file
        # there are redundant columns we can ignore
        self.tecFileselCols = [ "date", "gdlat", "glon", "tec", "dtec" ]
        # set variables for trough location detection
        self.equTrghCutoffMLat = 45.
        self.polTrghCutoffMLat = 70.
        self.nTecValsLongCutoff = 5.
        # set variables for trough location filtering
        self.trghLocGlonbinSize = 10
        self.trghLocGlonbinCntCutoff = 0.5
        # the ones below are used for median filtering
        self.mapDelTime = datetime.timedelta(seconds=5*60.)#numpy.timedelta64(seconds=50*60.)
        self.filterThrshldCutoff = 0.1#0.33
        self.medFiltstartLat = 10.
        # Also, this is very similar to Evan's median filtering implementation
        # total possible weight is
        # in current map
        # 1 center   : 1*5 =  5
        # 4 adjacent : 4*3 = 12
        # 4 diagonal : 4*2 =  8
        # in previous and next map
        # 2 center   : 2*3 =  6
        # 8 adjacent : 8*2 = 16
        # 8 diagonal : 8*1 =  8
        #--------------------------
        #                    55
        self.totWght = 55.
        # set weight arrays 
        self.currMapWghts = numpy.array( [ [2., 3., 2.],\
                                    [3., 5., 3.],\
                                    [2., 3., 2.] ] )
        self.prevMapWghts = numpy.array( [ [1., 2., 1.],\
                                    [2., 3., 2.],\
                                    [1., 2., 1.] ] )
        self.nextMapWghts = numpy.array( [ [1., 2., 1.],\
                                    [2., 3., 2.],\
                                    [1., 2., 1.] ] )
        # read the tec file for the given datetime
        self.dataDF = pandas.read_hdf(self.get_tec_file_from_date(self.inpDate), 'Data/Table Layout')
        self.dataDF["date"] = pandas.to_datetime(self.dataDF["year"]*10000000000 +\
                                            self.dataDF["month"]*100000000 + self.dataDF["day"]*1000000 +\
                                            self.dataDF["hour"]*10000 + self.dataDF["min"]*100 +\
                                            self.dataDF["sec"],format='%Y%m%d%H%M%S')
        # Only take selected datetime
        self.dataDF["selTimeDel"] = abs(self.dataDF["date"] - self.inpDate)
        self.nrstTime = self.dataDF[ self.dataDF["selTimeDel"] == min(self.dataDF["selTimeDel"]) ]["date"].unique()[0]
        self.nrstTime = datetime.datetime.utcfromtimestamp((self.nrstTime).tolist()/1e9)

    def get_tec_file_from_date(self, inpDate):
        """
        Given a time return the name of the tec file
        containing data for that time.
        """
        import os
        fileDtStr = inpDate.strftime("%y%m%d")
        for root, dirs, files in os.walk(self.tecDataDir):
            for fName in files:
                if fName.find(fileDtStr) != -1:
                    return root + "/" + fName
        print "No File FOUND for date-->", inpDate
        return None

    def get_tec_data(self, discardExtrmVals=True):
        """
        From the given input time get data from the closest time instance
        in the file. Remember these are 5 min resolution files. Then get data
        from +/- 5 min time instances. We'll use these for median filtering.
        """
        import datetime
        import numpy
        import pandas
        # DF for current time
        currTimeMap = self.dataDF[ self.dataDF["date"] == self.nrstTime ].reset_index(drop=True)
        # discard extreme values if option is selected
        if discardExtrmVals:
            # Discard tec values which are 2stds away!
            cutOffLimit = currTimeMap["tec"].mean() + 2*currTimeMap["tec"].std()
            currTimeMap = currTimeMap[ currTimeMap["tec"] <= cutOffLimit ].reset_index(drop=True)
        currTimeMap = currTimeMap[ self.tecFileselCols ]
        # if prevTime is in current day then use same self.dataDF
        # else load a new one.! 
        prevTime = self.nrstTime - self.mapDelTime
        if ( ( prevTime.year == self.nrstTime.year ) &\
            ( prevTime.month == self.nrstTime.month ) &\
            ( prevTime.day == self.nrstTime.day ) ):
            prevTimeMap = self.dataDF[ self.dataDF["date"] == prevTime ].reset_index(drop=True)
        else:
            print "reading from a different date for prev map"
            prevTimeMap = pandas.read_hdf(get_tec_file_from_date(prevTime), 'Data/Table Layout')
            # discard extreme values if option is selected
        if discardExtrmVals:
            # Discard tec values which are 2stds away!
            cutOffLimit = prevTimeMap["tec"].mean() + 2*prevTimeMap["tec"].std()
            prevTimeMap = prevTimeMap[ prevTimeMap["tec"] <= cutOffLimit ].reset_index(drop=True)
        prevTimeMap["date"] = pandas.to_datetime(prevTimeMap["year"]*10000000000 +\
                                        prevTimeMap["month"]*100000000 + prevTimeMap["day"]*1000000 +\
                                        prevTimeMap["hour"]*10000 + prevTimeMap["min"]*100 +\
                                        prevTimeMap["sec"],format='%Y%m%d%H%M%S')
        prevTimeMap = prevTimeMap[ prevTimeMap["date"] == prevTime ].reset_index(drop=True)
        prevTimeMap = prevTimeMap[ self.tecFileselCols ]
        # same applies for nextTimeMap
        nextTime = self.nrstTime + self.mapDelTime
        if ( ( nextTime.year == self.nrstTime.year ) &\
            ( nextTime.month == self.nrstTime.month ) &\
            ( nextTime.day == self.nrstTime.day ) ):
            nextTimeMap = self.dataDF[ self.dataDF["date"] == nextTime ].reset_index(drop=True)
        else:
            print "reading from a different date for next map"
            nextTimeMap = pandas.read_hdf(get_tec_file_from_date(nextTime), 'Data/Table Layout')
            # discard extreme values if option is selected
        if discardExtrmVals:
            # Discard tec values which are 2stds away!
            cutOffLimit = nextTimeMap["tec"].mean() + 2*nextTimeMap["tec"].std()
            nextTimeMap = nextTimeMap[ nextTimeMap["tec"] <= cutOffLimit ].reset_index(drop=True)
        nextTimeMap["date"] = pandas.to_datetime(nextTimeMap["year"]*10000000000 +\
                                        nextTimeMap["month"]*100000000 + nextTimeMap["day"]*1000000 +\
                                        nextTimeMap["hour"]*10000 + nextTimeMap["min"]*100 +\
                                        nextTimeMap["sec"],format='%Y%m%d%H%M%S')
        nextTimeMap = nextTimeMap[ nextTimeMap["date"] == nextTime ].reset_index(drop=True)
        nextTimeMap = nextTimeMap[ self.tecFileselCols ]
        # return the dataframes in order --> prev, curr, next
        return ( prevTimeMap, currTimeMap, nextTimeMap )


    def find_trough_loc(self, medFltrdTecDF):
        """
        From the median filtered tec dataframe
        identify the location of trough
        """
        import datetime
        import numpy
        import pandas
        from scipy import signal, ndimage
        from davitpy import utils

        BndGlonArr = numpy.array( [] )
        BndMlonArr = numpy.array( [] )
        BndEquGlatArr = numpy.array( [] )
        BndPolGlatArr = numpy.array( [] )
        minTecGlatArr = numpy.array( [] )
        BndEquMlatArr = numpy.array( [] )
        BndPolMlatArr = numpy.array( [] )
        minTecMlatArr = numpy.array( [] )
        BndEquMlonArr = numpy.array( [] )
        BndPolMlonArr = numpy.array( [] )
        minTecMlonArr = numpy.array( [] )
        minTecValArr = numpy.array( [] )
        minFltrdTecValArr = numpy.array( [] )
        BndEquTecValArr = numpy.array( [] )
        BndPolTecValArr = numpy.array( [] )
        currTimeArr = numpy.array( [] )

        glonList = medFltrdTecDF["glon"].unique().tolist()
        for currGLon in glonList:
            selDF = medFltrdTecDF[ (medFltrdTecDF["glon"] == currGLon) &\
                             (medFltrdTecDF["mlat"] >= self.equTrghCutoffMLat) &\
                             (~medFltrdTecDF["tec"].isnull()) &\
                             (medFltrdTecDF["mlat"] <= self.polTrghCutoffMLat)]
            latArr = selDF["gdlat"].values
            mlatArr = selDF["mlat"].values
            tecArr = selDF["tec"].values
            # If number of values at a particular longitude is low,
            # discard it!
            if len( tecArr ) < self.nTecValsLongCutoff :
                continue
            filtTecArr = ndimage.filters.gaussian_filter1d(tecArr,2) #
            diffTecArr = numpy.gradient(numpy.gradient(filtTecArr))#numpy.gradient(numpy.gradient(filtTecArr))#numpy.gradient(filtTecArr)

            minTroughLocTec = numpy.argmin(filtTecArr)
            # minTroughLocTec is the location of the deepest point of 
            # the TEC trough! Now we need to find the zero crossing locations
            # one simple way to do this is to check for signs of the values
            # in the diffTecArr array, i.e., implement numpy.sign(). Now wherever
            # there is a zero crossing, we'll find numpy.diff() of this sign array
            # would be either +/- 2 depending on the direction of the crossing. Now
            # equatorward of the bottom trough loc, we should find the closest place
            # where value is +2 ( 1 - (-1) ) and vice versa for poleward boundary! Remember
            # we are looking at the second order derivatives!
            diffSignTecArr = numpy.diff( numpy.sign( diffTecArr ) )
            eqBndLocVals = numpy.where( diffSignTecArr == 2 )
            polBndLocVals = numpy.where( diffSignTecArr == -2 )
            eqBndLoc = -1.
            polBndLoc = -1.
            for eq in eqBndLocVals[0]:
                if eqBndLoc == -1 :
                    if eq < minTroughLocTec:
                        eqBndLoc = eq
                else:
                    if eq < minTroughLocTec:
                        if eq > eqBndLoc:
                            eqBndLoc = eq
            for po in polBndLocVals[0]:
                if polBndLoc == -1 :
                    if po > minTroughLocTec:
                        polBndLoc = po
                else:
                    if po > minTroughLocTec:
                        if po < polBndLoc:
                            polBndLoc = po
            # adjust poleward location of the boundary!
            # remember for numpy.diff we loose one element in the array
            if polBndLoc != -1:
                polBndLoc += 1 
            if ( (polBndLoc == -1) | (eqBndLoc == -1) ) :
                continue
            # Convert the coords to mlat and mlon
            currEqMlon, currEqMlat = utils.coord_conv( currGLon, latArr[eqBndLoc], \
                                         "geo", "mag", altitude=300., \
                                         date_time=self.nrstTime )
            currPoMlon, currPoMlat = utils.coord_conv( currGLon, latArr[polBndLoc], \
                                         "geo", "mag", altitude=300., \
                                         date_time=self.nrstTime )
            currMinTrghMlon, currMinTrghMlat = utils.coord_conv( currGLon, latArr[minTroughLocTec], \
                                         "geo", "mag", altitude=300., \
                                         date_time=self.nrstTime )
            BndGlonArr = numpy.append( BndGlonArr, [currGLon] )
            BndEquGlatArr = numpy.append( BndEquGlatArr, latArr[eqBndLoc] )
            BndPolGlatArr = numpy.append( BndPolGlatArr, latArr[polBndLoc] )
            minTecGlatArr = numpy.append( minTecGlatArr, latArr[minTroughLocTec] )
            BndEquMlonArr = numpy.append( BndEquMlonArr, [currEqMlon] )
            BndEquMlatArr = numpy.append( BndEquMlatArr, [currEqMlat] )
            BndPolMlonArr = numpy.append( BndPolMlonArr, [currPoMlon] )
            BndPolMlatArr = numpy.append( BndPolMlatArr, [currPoMlat] )
            minTecMlonArr = numpy.append( minTecMlonArr, [currMinTrghMlon] )
            minTecMlatArr = numpy.append( minTecMlatArr, [currMinTrghMlat] )
            minTecValArr = numpy.append( minTecValArr, tecArr[minTroughLocTec] )
            minFltrdTecValArr = numpy.append( minFltrdTecValArr, filtTecArr[minTroughLocTec] )
            BndEquTecValArr = numpy.append( BndEquTecValArr, tecArr[eqBndLoc] )
            BndPolTecValArr = numpy.append( BndPolTecValArr, tecArr[polBndLoc] )
            currTimeArr = numpy.append( currTimeArr, [ self.nrstTime ] )
        # convert to DF
        trghLocDF = pandas.DataFrame({
            "BndGlon" : BndGlonArr,
            "BndEquGlat" : BndEquGlatArr,
            "BndPolGlat" : BndPolGlatArr,
            "minTecGlat" : minTecGlatArr,
            "BndEquMlat" : BndEquMlatArr,
            "BndPolMlat" : BndPolMlatArr,
            "minTecMlat" : minTecMlatArr,
            "BndEquMlon" : BndEquMlonArr,
            "BndPolMlon" : BndPolMlonArr,
            "minTecMlon" : minTecMlonArr,
            "minTecVal" : minTecValArr,
            "minFltrdTecVal" : minFltrdTecValArr,
            "BndEquTecVal" : BndEquTecValArr,
            "BndPolTecVal" : BndPolTecValArr,
            "date" : currTimeArr
            })
        return trghLocDF

    def filter_trough_loc(self,trghLocDF):
        """
        Once a trough location has been calculated, we'll find 
        a few unwated locations in there. Here we'll fitler them out.
        """
        import numpy
        import pandas
        # Now we need to filter out the trough locs 
        # which are present in odd locations. We do so
        # by binning the Glon arr in a groups 10. and count
        # how many fits we have in each bin. If we have greater
        # than 50% (actual count=5) values in that bin, we keep
        # those bins and remove the rest.
        # check if longitude goes -180 to 180 or 0 to 360.
        if numpy.min( trghLocDF["BndGlon"].values ) < 0 :
            minEdge = -180.
            maxEdge = 180.
        else:
            minEdge = 0.
            maxEdge = 360.
        binList = [ b for b in numpy.arange(minEdge,maxEdge,self.trghLocGlonbinSize) ]
        glonFreq, glonBins = numpy.histogram(trghLocDF["BndGlon"].values, bins=binList)
        goodGlonValues = numpy.where( glonFreq > self.trghLocGlonbinCntCutoff*self.trghLocGlonbinSize )
        fltrdTrghLocDF = trghLocDF[ ( trghLocDF["BndGlon"] >= numpy.min( glonBins[goodGlonValues] ) ) &\
                          ( trghLocDF["BndGlon"] <= numpy.max( glonBins[goodGlonValues] ) ) ].reset_index(drop=True)
        return fltrdTrghLocDF

    def apply_median_filter(self):
        """
        Perform Evan's median filtering here. We use three time isntances
        one is current (to) and the other two are to +/- 5 min
        """
        import datetime
        import numpy
        import pandas
        from davitpy.models import aacgm
        from davitpy import utils
        # Setup arrays to store the new results
        newTecGlatArr = []
        newTecGlonArr = []
        newTecTecArr = []
        newTecDTecArr = []
        newTecDateArr = []
        # get the respective maps
        prevTimeMap, currTimeMap, nextTimeMap = self.get_tec_data()
        # Get a list of lats and lons from currMap
        glatList = currTimeMap["gdlat"].unique()
        glonList = currTimeMap["glon"].unique()
        for selGlat in glatList:
            for selGlon in glonList:
                if abs(selGlat) < self.medFiltstartLat:
                    continue
                # Get corresponding data from the current cells
                currMapCells = currTimeMap[ (currTimeMap["gdlat"] >= selGlat - 1) &\
                                          (currTimeMap["gdlat"] <= selGlat + 1) &\
                                          (currTimeMap["glon"] >= selGlon - 1) &\
                                          (currTimeMap["glon"] <= selGlon + 1) ]
                prevMapCells = prevTimeMap[ (prevTimeMap["gdlat"] >= selGlat - 1) &\
                                          (prevTimeMap["gdlat"] <= selGlat + 1) &\
                                          (prevTimeMap["glon"] >= selGlon - 1) &\
                                          (prevTimeMap["glon"] <= selGlon + 1) ]
                nextMapCells = nextTimeMap[ (nextTimeMap["gdlat"] >= selGlat - 1) &\
                                          (nextTimeMap["gdlat"] <= selGlat + 1) &\
                                          (nextTimeMap["glon"] >= selGlon - 1) &\
                                          (nextTimeMap["glon"] <= selGlon + 1) ]
                # If this is an empty DF set CurrCellWeight to 0.
                currCellTecArr = []
                prevCellTecArr = []
                nextCellTecArr = []
                currCellDTecArr = []
                prevCellDTecArr = []
                nextCellDTecArr = []
                if currMapCells.shape[0] == 0:
                    currCellWght = 0.
                else:
                    currCellWght = 0.
                    # calculate weight from center center current cell
                    currCC = currMapCells[ (currMapCells["gdlat"] == selGlat) &\
                                       (currMapCells["glon"] == selGlon) ]
                    tmpWght = 0.
                    if currCC.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(currCC["tec"].tolist()[0]):
                            tmpWght = self.currMapWghts[1,1]
                            currCellTecArr += currCC["tec"].tolist()
                            currCellDTecArr += currCC["dtec"].tolist()
                    currCellWght += tmpWght
                    # calculate weight from top center current cell
                    currTC = currMapCells[ (currMapCells["gdlat"] == selGlat) &\
                                       (currMapCells["glon"] == selGlon-1) ]
                    tmpWght = 0.
                    if currTC.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(currTC["tec"].tolist()[0]):
                            tmpWght = self.currMapWghts[1,0]
                            currCellTecArr += currTC["tec"].tolist()
                            currCellDTecArr += currTC["dtec"].tolist()
                    currCellWght += tmpWght
                    # calculate weight from bottom center current cell
                    currBC = currMapCells[ (currMapCells["gdlat"] == selGlat) &\
                                       (currMapCells["glon"] == selGlon+1) ]
                    tmpWght = 0.
                    if currBC.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(currBC["tec"].tolist()[0]):
                            tmpWght = self.currMapWghts[1,2]
                            currCellTecArr += currBC["tec"].tolist()
                            currCellDTecArr += currBC["dtec"].tolist()
                    currCellWght += tmpWght
                    # calculate weight from left center current cell
                    currLC = currMapCells[ (currMapCells["gdlat"] == selGlat-1) &\
                                       (currMapCells["glon"] == selGlon) ]
                    tmpWght = 0.
                    if currLC.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(currLC["tec"].tolist()[0]):
                            tmpWght = self.currMapWghts[0,1]
                            currCellTecArr += currLC["tec"].tolist()
                            currCellDTecArr += currLC["dtec"].tolist()
                    currCellWght += tmpWght
                    # calculate weight from right center current cell
                    currRC = currMapCells[ (currMapCells["gdlat"] == selGlat+1) &\
                                       (currMapCells["glon"] == selGlon) ]
                    tmpWght = 0.
                    if currRC.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(currRC["tec"].tolist()[0]):
                            tmpWght = self.currMapWghts[2,1]
                            currCellTecArr += currRC["tec"].tolist()
                            currCellDTecArr += currRC["dtec"].tolist()
                    currCellWght += tmpWght
                    # calculate weight from top left current cell
                    currTL = currMapCells[ (currMapCells["gdlat"] == selGlat-1) &\
                                       (currMapCells["glon"] == selGlon-1) ]
                    tmpWght = 0.
                    if currTL.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(currTL["tec"].tolist()[0]):
                            tmpWght = self.currMapWghts[0,0]
                            currCellTecArr += currTL["tec"].tolist()
                            currCellDTecArr += currTL["dtec"].tolist()
                    currCellWght += tmpWght
                    # calculate weight from top right current cell
                    currTR = currMapCells[ (currMapCells["gdlat"] == selGlat+1) &\
                                       (currMapCells["glon"] == selGlon-1) ]
                    tmpWght = 0.
                    if currTR.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(currTR["tec"].tolist()[0]):
                            tmpWght = self.currMapWghts[2,0]
                            currCellTecArr += currTR["tec"].tolist()
                            currCellDTecArr += currTR["dtec"].tolist()
                    currCellWght += tmpWght
                    # calculate weight from bottom left current cell
                    currBL = currMapCells[ (currMapCells["gdlat"] == selGlat-1) &\
                                       (currMapCells["glon"] == selGlon+1) ]
                    tmpWght = 0.
                    if currBL.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(currBL["tec"].tolist()[0]):
                            tmpWght = self.currMapWghts[0,2]
                            currCellTecArr += currBL["tec"].tolist()
                            currCellDTecArr += currBL["dtec"].tolist()
                    currCellWght += tmpWght
                    # calculate weight from bottom right current cell
                    currBR = currMapCells[ (currMapCells["gdlat"] == selGlat+1) &\
                                       (currMapCells["glon"] == selGlon+1) ]
                    tmpWght = 0.
                    if currBR.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(currBR["tec"].tolist()[0]):
                            tmpWght = self.currMapWghts[0,2]
                            currCellTecArr += currBR["tec"].tolist()
                            currCellDTecArr += currBR["dtec"].tolist()
                    currCellWght += tmpWght
                    
                    
                    
                if prevMapCells.shape[0] == 0:
                    prevCellWght = 0.
                else:
                    prevCellWght = 0.
                    # calculate weight from center center previous cell
                    prevCC = prevMapCells[ (prevMapCells["gdlat"] == selGlat) &\
                                       (prevMapCells["glon"] == selGlon) ]
                    tmpWght = 0.
                    if prevCC.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(prevCC["tec"].tolist()[0]):
                            tmpWght = self.prevMapWghts[1,1]
                            prevCellTecArr += prevCC["tec"].tolist()
                            prevCellDTecArr += prevCC["dtec"].tolist()
                    prevCellWght += tmpWght
                    # calculate weight from top center previous cell
                    prevTC = prevMapCells[ (prevMapCells["gdlat"] == selGlat) &\
                                       (prevMapCells["glon"] == selGlon-1) ]
                    tmpWght = 0.
                    if prevTC.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(prevTC["tec"].tolist()[0]):
                            tmpWght = self.prevMapWghts[1,0]
                            prevCellTecArr += prevTC["tec"].tolist()
                            prevCellDTecArr += prevTC["dtec"].tolist()
                    prevCellWght += tmpWght
                    # calculate weight from bottom center previous cell
                    prevBC = prevMapCells[ (prevMapCells["gdlat"] == selGlat) &\
                                       (prevMapCells["glon"] == selGlon+1) ]
                    tmpWght = 0.
                    if prevBC.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(prevBC["tec"].tolist()[0]):
                            tmpWght = self.prevMapWghts[1,2]
                            prevCellTecArr += prevBC["tec"].tolist()
                            prevCellDTecArr += prevBC["dtec"].tolist()
                    prevCellWght += tmpWght
                    # calculate weight from left center previous cell
                    prevLC = prevMapCells[ (prevMapCells["gdlat"] == selGlat-1) &\
                                       (prevMapCells["glon"] == selGlon) ]
                    tmpWght = 0.
                    if prevLC.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(prevLC["tec"].tolist()[0]):
                            tmpWght = self.prevMapWghts[0,1]
                            prevCellTecArr += prevLC["tec"].tolist()
                            prevCellDTecArr += prevLC["dtec"].tolist()
                    prevCellWght += tmpWght
                    # calculate weight from right center previous cell
                    prevRC = prevMapCells[ (prevMapCells["gdlat"] == selGlat+1) &\
                                       (prevMapCells["glon"] == selGlon) ]
                    tmpWght = 0.
                    if prevRC.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(prevRC["tec"].tolist()[0]):
                            tmpWght = self.prevMapWghts[2,1]
                            prevCellTecArr += prevRC["tec"].tolist()
                            prevCellDTecArr += prevRC["dtec"].tolist()
                    prevCellWght += tmpWght
                    # calculate weight from top left previous cell
                    prevTL = prevMapCells[ (prevMapCells["gdlat"] == selGlat-1) &\
                                       (prevMapCells["glon"] == selGlon-1) ]
                    tmpWght = 0.
                    if prevTL.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(prevTL["tec"].tolist()[0]):
                            tmpWght = self.prevMapWghts[0,0]
                            prevCellTecArr += prevTL["tec"].tolist()
                            prevCellDTecArr += prevTL["dtec"].tolist()
                    prevCellWght += tmpWght
                    # calculate weight from top right previous cell
                    prevTR = prevMapCells[ (prevMapCells["gdlat"] == selGlat+1) &\
                                       (prevMapCells["glon"] == selGlon-1) ]
                    tmpWght = 0.
                    if prevTR.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(prevTR["tec"].tolist()[0]):
                            tmpWght = self.prevMapWghts[2,0]
                            prevCellTecArr += prevTR["tec"].tolist()
                            prevCellDTecArr += prevTR["dtec"].tolist()
                    prevCellWght += tmpWght
                    # calculate weight from bottom left previous cell
                    prevBL = prevMapCells[ (prevMapCells["gdlat"] == selGlat-1) &\
                                       (prevMapCells["glon"] == selGlon+1) ]
                    tmpWght = 0.
                    if prevBL.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(prevBL["tec"].tolist()[0]):
                            tmpWght = self.prevMapWghts[0,2]
                            prevCellTecArr += prevBL["tec"].tolist()
                            prevCellDTecArr += prevBL["dtec"].tolist()
                    prevCellWght += tmpWght
                    # calculate weight from bottom right previous cell
                    prevBR = prevMapCells[ (prevMapCells["gdlat"] == selGlat+1) &\
                                       (prevMapCells["glon"] == selGlon+1) ]
                    tmpWght = 0.
                    if prevBR.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(prevBR["tec"].tolist()[0]):
                            tmpWght = self.prevMapWghts[0,2]
                            prevCellTecArr += prevBR["tec"].tolist()
                            prevCellDTecArr += prevBR["dtec"].tolist()
                    prevCellWght += tmpWght



                if nextMapCells.shape[0] == 0:
                    nextCellWght = 0.
                else:
                    nextCellWght = 0.
                    # calculate weight from center center next cell
                    nextCC = nextMapCells[ (nextMapCells["gdlat"] == selGlat) &\
                                       (nextMapCells["glon"] == selGlon) ]
                    tmpWght = 0.
                    if nextCC.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(nextCC["tec"].tolist()[0]):
                            tmpWght = self.nextMapWghts[1,1]
                            nextCellTecArr += nextCC["tec"].tolist()
                            nextCellDTecArr += nextCC["dtec"].tolist()
                    nextCellWght += tmpWght
                    # calculate weight from top center next cell
                    nextTC = nextMapCells[ (nextMapCells["gdlat"] == selGlat) &\
                                       (nextMapCells["glon"] == selGlon-1) ]
                    tmpWght = 0.
                    if nextTC.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(nextTC["tec"].tolist()[0]):
                            tmpWght = self.nextMapWghts[1,0]
                            nextCellTecArr += nextTC["tec"].tolist()
                            nextCellDTecArr += nextTC["dtec"].tolist()
                    nextCellWght += tmpWght
                    # calculate weight from bottom center next cell
                    nextBC = nextMapCells[ (nextMapCells["gdlat"] == selGlat) &\
                                       (nextMapCells["glon"] == selGlon+1) ]
                    tmpWght = 0.
                    if nextBC.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(nextBC["tec"].tolist()[0]):
                            tmpWght = self.nextMapWghts[1,2]
                            nextCellTecArr += nextBC["tec"].tolist()
                            nextCellDTecArr += nextBC["dtec"].tolist()
                    nextCellWght += tmpWght
                    # calculate weight from left center next cell
                    nextLC = nextMapCells[ (nextMapCells["gdlat"] == selGlat-1) &\
                                       (nextMapCells["glon"] == selGlon) ]
                    tmpWght = 0.
                    if nextLC.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(nextLC["tec"].tolist()[0]):
                            tmpWght = self.nextMapWghts[0,1]
                            nextCellTecArr += nextLC["tec"].tolist()
                            nextCellDTecArr += nextLC["dtec"].tolist()
                    nextCellWght += tmpWght
                    # calculate weight from right center next cell
                    nextRC = nextMapCells[ (nextMapCells["gdlat"] == selGlat+1) &\
                                       (nextMapCells["glon"] == selGlon) ]
                    tmpWght = 0.
                    if nextRC.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(nextRC["tec"].tolist()[0]):
                            tmpWght = self.nextMapWghts[2,1]
                            nextCellTecArr += nextRC["tec"].tolist()
                            nextCellDTecArr += nextRC["dtec"].tolist()
                    nextCellWght += tmpWght
                    # calculate weight from top left next cell
                    nextTL = nextMapCells[ (nextMapCells["gdlat"] == selGlat-1) &\
                                       (nextMapCells["glon"] == selGlon-1) ]
                    tmpWght = 0.
                    if nextTL.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(nextTL["tec"].tolist()[0]):
                            tmpWght = self.nextMapWghts[0,0]
                            nextCellTecArr += nextTL["tec"].tolist()
                            nextCellDTecArr += nextTL["dtec"].tolist()
                    nextCellWght += tmpWght
                    # calculate weight from top right next cell
                    nextTR = nextMapCells[ (nextMapCells["gdlat"] == selGlat+1) &\
                                       (nextMapCells["glon"] == selGlon-1) ]
                    tmpWght = 0.
                    if nextTR.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(nextTR["tec"].tolist()[0]):
                            tmpWght = self.nextMapWghts[2,0]
                            nextCellTecArr += nextTR["tec"].tolist()
                            nextCellDTecArr += nextTR["dtec"].tolist()
                    nextCellWght += tmpWght
                    # calculate weight from bottom left next cell
                    nextBL = nextMapCells[ (nextMapCells["gdlat"] == selGlat-1) &\
                                       (nextMapCells["glon"] == selGlon+1) ]
                    tmpWght = 0.
                    if nextBL.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(nextBL["tec"].tolist()[0]):
                            tmpWght = self.nextMapWghts[0,2]
                            nextCellTecArr += nextBL["tec"].tolist()
                            nextCellDTecArr += nextBL["dtec"].tolist()
                    nextCellWght += tmpWght
                    # calculate weight from bottom right next cell
                    nextBR = nextMapCells[ (nextMapCells["gdlat"] == selGlat+1) &\
                                       (nextMapCells["glon"] == selGlon+1) ]
                    tmpWght = 0.
                    if nextBR.shape[0] > 0:
                        # Check for nan
                        if numpy.isfinite(nextBR["tec"].tolist()[0]):
                            tmpWght = self.nextMapWghts[0,2]
                            nextCellTecArr += nextBR["tec"].tolist()
                            nextCellDTecArr += nextBR["dtec"].tolist()
                    nextCellWght += tmpWght
                
                # Check if the selected cell exceeds threshold value
                if (currCellWght + prevCellWght + nextCellWght)/self.totWght >= self.filterThrshldCutoff:
                    # get the median value of tec from all the cells
                    fullTimeFrameTECList = currCellTecArr + prevCellTecArr + nextCellTecArr
                    medTecVal = numpy.median( numpy.array( fullTimeFrameTECList ) )
                    fullTimeFrameDTECList = currCellDTecArr + prevCellDTecArr + nextCellDTecArr
                    medDTecVal = numpy.median( numpy.array( fullTimeFrameDTECList ) )
                else:
                    medTecVal = numpy.nan
                    medDTecVal = numpy.nan
                newTecTecArr.append( medTecVal )
                newTecDTecArr.append( medDTecVal )
                newTecDateArr.append( self.nrstTime )
                newTecGlatArr.append( selGlat )
                newTecGlonArr.append( selGlon )
        # convert dst data to a dataframe
        newTECDF = pandas.DataFrame(
            {'gdlat': newTecGlatArr,
             'glon': newTecGlonArr,
             'tec': newTecTecArr,
             'dtec': newTecDTecArr,
             'date' : newTecDateArr
            })
        # Add some additional columns for the DF
        gLonArr = newTECDF["glon"].values
        gdLatArr = newTECDF["gdlat"].values
        mlon, mlat = utils.coord_conv( gLonArr, gdLatArr, \
                                         "geo", "mag", altitude=300., \
                                         date_time=self.nrstTime )
        newTECDF["mlon"] = mlon
        newTECDF["mlat"] = mlat
        newTECDF["mlt"] = [ aacgm.mltFromYmdhms(self.nrstTime.year, \
                        self.nrstTime.month,self.nrstTime.day, self.nrstTime.hour,\
                        self.nrstTime.minute, self.nrstTime.second, x) for x in newTECDF["mlon"] ]
        newTECDF["normMLT"] = [x-24 if x >= 12\
                     else x for x in newTECDF['mlt']]
        return newTECDF

    def plotTecLocTrgh(self, trghLocDF, medFltrdTecDF, plotFileName, \
        plotTec=True, plotTrghLoc=True, coords="mag"):
        """
        Overlay actual TEC data and trough location (whichever is chosen)
        on map marked in given coordinates.
        """
        from davitpy import utils
        import matplotlib.pyplot as plt
        from matplotlib.colors import ListedColormap
        import seaborn as sns
        # check if atleast one option is chosen (TEC, loc trough)
        if ( (not plotTec) & (not plotTrghLoc) ):
            print "May be a good idea to plot atleast one of" + \
                    "the options (TEC values or trough location)." +\
                     "You are simply plotting a map now. Just warning you!!"
        # check the coords, currently we'll only plot mag or geo
        if ( (coords != "mag") & (coords != "geo") ):
            print "can use only 'mag' or 'geo' coords!!!, set them again!"
            return
        # Seaborn styling
        sns.set_style("darkgrid")
        sns.set_context("paper")
        # set a colorbar
        seaMap = ListedColormap(sns.color_palette("Spectral_r"))
        # Plot using matplotlib
        fig = plt.figure()
        ax = fig.add_subplot(111)
        m1 = utils.plotUtils.mapObj(boundinglat=30., gridLabels=True, coords=coords, ax=ax, datetime=self.nrstTime)
        if plotTec:
            if coords == "mag":
                xVec, yVec = m1(list(medFltrdTecDF["mlon"]), list(medFltrdTecDF["mlat"]), coords=coords)
            else:
                xVec, yVec = m1(list(medFltrdTecDF["glon"]), list(medFltrdTecDF["glat"]), coords=coords)
            tecPlot = m1.scatter( xVec, yVec , c=medFltrdTecDF["tec"], s=40.,\
                       cmap=seaMap, alpha=0.7, zorder=5.,\
                                 edgecolor='none', marker="s" )
            cbar = plt.colorbar(tecPlot, orientation='vertical')
            cbar.set_label('TEC', size=15)
        if plotTrghLoc:
            if coords == "mag":
                xVecEquBnd, yVecEquBnd = m1(trghLocDF["BndEquMlon"].values, trghLocDF["BndEquMlat"].values, coords=coords)
                xVecPolBnd, yVecPolBnd = m1(trghLocDF["BndPolMlon"].values, trghLocDF["BndPolMlat"].values, coords=coords)
                xVecMinTrghBnd, yVecMinTrghBnd = m1(trghLocDF["minTecMlon"].values, trghLocDF["minTecMlat"].values, coords=coords)
            else:
                xVecEquBnd, yVecEquBnd = m1(trghLocDF["BndGlon"].values, trghLocDF["BndEquGlat"].values, coords=coords)
                xVecPolBnd, yVecPolBnd = m1(trghLocDF["BndGlon"].values, trghLocDF["BndPolGlat"].values, coords=coords)
                xVecMinTrghBnd, yVecMinTrghBnd = m1(trghLocDF["BndGlon"].values, trghLocDF["minTecGlat"].values, coords=coords)
            eqPlot = m1.scatter( xVecEquBnd, yVecEquBnd , s=10.,\
                     c='y', marker="^", zorder=7. )
            poPlot = m1.scatter( xVecPolBnd, yVecPolBnd , s=10.,\
                                 c='y', marker="v", zorder=7. )
            mtPlot = m1.scatter( xVecMinTrghBnd, yVecMinTrghBnd , s=15.,\
                                 c='r', marker="*", zorder=7. )
        ax.get_figure().savefig(plotFileName,bbox_inches='tight')
        plt.close(fig)