if __name__ == "__main__":
    import medFiltTrghLoc
    import datetime
    inpDT = datetime.datetime( 2011, 4, 9, 9, 0 )
    mftrObj = medFiltTrghLoc.MFTrough( \
        "/home/bharat/Documents/medFiltTec/tec-medFilt-20110409.txt" )
    allTimesList = mftrObj.get_all_uniq_times()
    print allTimesList
    trBndDF = mftrObj.find_trough_loc(inpDT)


class MFTrough(object):
    """
    A class to identify the location of TEC trough
    given a time instance. We use Evan's median filtered
    TEC data!!!
    """
    def __init__(self, tecFileName):
        import datetime
        import numpy
        import pandas
        # choose columns we need to store from the tec file
        tecFileselCols = [ "dateStr", "timeStr", "Mlat",\
              "Mlon", "med_tec", "dlat", "dlon" ]
        # set variables for trough location detection
        self.equTrghCutoffMLat = 45.
        self.polTrghCutoffMLat = 70.
        self.nTecValsLongCutoff = 5.
        # set variables for trough location filtering
        self.trghLocMlonbinSize = 10
        self.trghLocMlonbinCntCutoff = 0.5
        # read the tec file for the given datetime
        self.medFltrdTecDF = pandas.read_csv(tecFileName, delim_whitespace=True,\
                                    header=None, names=tecFileselCols)
        self.medFltrdTecDF["date"] = self.medFltrdTecDF.apply(\
         self.convert_to_datetime, axis=1 )


    def convert_to_datetime(self,row):
        """
        Convert date and time strings to datetime objects
        """
        import datetime
        currDateStr = str( int( row["dateStr"] ) )
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

    def get_all_uniq_times(self):
        """
        Get all the unique times (dt objs) present
        in the inp TEC file!!!
        """
        return self.medFltrdTecDF["date"].unique()


    def find_trough_loc(self, selDT):
        """
        From the median filtered tec dataframe
        identify the location of trough
        """
        import datetime
        import numpy
        import pandas
        from scipy import signal, ndimage
        from davitpy import utils

        BndMlonArr = numpy.array( [] )
        BndEquMlatArr = numpy.array( [] )
        BndPolMlatArr = numpy.array( [] )
        minTecMlatArr = numpy.array( [] )
        minTecValArr = numpy.array( [] )
        minFltrdTecValArr = numpy.array( [] )
        BndEquTecValArr = numpy.array( [] )
        BndPolTecValArr = numpy.array( [] )
        currTimeArr = numpy.array( [] )
        selInpDTDF = self.medFltrdTecDF[ \
            self.medFltrdTecDF["date"] == selDT ].reset_index(drop=True)
        mlonList = selInpDTDF["Mlon"].unique().tolist()
        for currMLon in mlonList:
            selDF = selInpDTDF[ (selInpDTDF["Mlon"] == currMLon) &\
                             (selInpDTDF["Mlat"] >= self.equTrghCutoffMLat) &\
                             (~selInpDTDF["med_tec"].isnull()) &\
                             (selInpDTDF["Mlat"] <= self.polTrghCutoffMLat)]
            mlatArr = selDF["Mlat"].values
            tecArr = selDF["med_tec"].values
             # If number of values at a particular longitude is low,
            # discard it!
            if len( tecArr ) < self.nTecValsLongCutoff :
                continue
            filtTecArr = ndimage.filters.gaussian_filter1d(tecArr,2)
            diffTecArr = numpy.gradient(numpy.gradient(filtTecArr))
            minTroughLocTec = numpy.argmin(filtTecArr)
            # minTroughLocTec is the location of the deepest point of 
            # the TEC trough! Now we need to find the zero crossing locations
            # one simple way to do this is to check for signs of the values
            # in the diffTecArr array, i.e., implement numpy.sign(). Now wherever
            # there is a zero crossing, we'll find numpy.diff() of this sign array
            # would be either +/- 2 depending on the direction of the crossing. Now
            # equatorward of the bottom trough loc, we should find the closest place
            # where value is +2 ( 1 - (-1) ) and vice versa for poleward boundary! 
            # Remember we are looking at the second order derivatives!
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
            BndMlonArr = numpy.append( BndMlonArr, [currMLon] )
            BndEquMlatArr = numpy.append( BndEquMlatArr, \
                                            mlatArr[eqBndLoc] )
            BndPolMlatArr = numpy.append( BndPolMlatArr, \
                                            mlatArr[polBndLoc] )
            minTecMlatArr = numpy.append( minTecMlatArr, \
                                            mlatArr[minTroughLocTec] )
            minTecValArr = numpy.append( minTecValArr, \
                                            tecArr[minTroughLocTec] )
            minFltrdTecValArr = numpy.append( minFltrdTecValArr,\
                                     filtTecArr[minTroughLocTec] )
            BndEquTecValArr = numpy.append( BndEquTecValArr, \
                                                tecArr[eqBndLoc] )
            BndPolTecValArr = numpy.append( BndPolTecValArr, \
                                                tecArr[polBndLoc] )
            currTimeArr = numpy.append( currTimeArr, [ selDT ] )
        # convert to DF
        trghLocDF = pandas.DataFrame({
            "BndMlon" : BndMlonArr,
            "BndEquMlat" : BndEquMlatArr,
            "BndPolMlat" : BndPolMlatArr,
            "minTecMlat" : minTecMlatArr,
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
        if numpy.min( trghLocDF["BndMlon"].values ) < 0 :
            minEdge = -180.
            maxEdge = 180.
        else:
            minEdge = 0.
            maxEdge = 360.
        binList = [ b for b in numpy.arange(minEdge,maxEdge,self.trghLocMlonbinSize) ]
        mlonFreq, mlonBins = numpy.histogram(trghLocDF["BndMlon"].values, bins=binList)
        goodMlonValues = numpy.where( mlonFreq >= self.trghLocMlonbinCntCutoff*self.trghLocMlonbinSize )
        if goodMlonValues[0].size == 0:
            return None
        fltrdTrghLocDF = trghLocDF[ ( trghLocDF["BndMlon"] >= numpy.min( mlonBins[goodMlonValues] ) ) &\
                          ( trghLocDF["BndMlon"] <= numpy.max( mlonBins[goodMlonValues] ) ) ].reset_index(drop=True)
        return fltrdTrghLocDF