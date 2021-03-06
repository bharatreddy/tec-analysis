if __name__ == "__main__":
    import troughStats
    import datetime
    inpDT = datetime.datetime( 2011, 4, 9, 9, 0 )
    trObj = troughStats.TroughAnlytcs( "../data/newRawTrghLoc.txt" )
    trObj.get_fltrd_locs(saveToCsv=True)
    fltTrDF = trObj.filter_trough_loc(inpDT)
    inpFileName = "/home/bharat/Documents/tec-plots/trough-bndrs/trghFltrd"\
                     + inpDT.strftime("%Y%m%d-%H%M") + ".pdf"
    trObj.plot_trgh_loc(fltTrDF)

class TroughAnlytcs(object):
    """
    A class which takes in the trough location identified
    and then applies more filters to discard bad data
    then finally perform analytics on trough loc
    """
    def __init__(self, trghLocFile):
        """
        Set up some constants and read data!
        """
        import datetime
        import numpy
        import pandas
        # setup some cutoff vals to be used later
        # only choose the North American sector for analysis
        self.mlonRngNA = [ 30., 255. ]
        # We verify if there is continous data availability
        # over extended longitudinal sector. We discard locations
        # with sparse data
        self.segLgthCutoff = 10.
        # everytime we miss data for 5 lons 
        # we'll see it as a jump/miss in data.
        # This will be used to find segments
        # which have continuous data
        self.jumpCutoff = 5.
        # Load the data into DF
        self.fltTecDataDF = pandas.read_csv(trghLocFile, sep=' ',\
                            parse_dates=["date"],\
                               infer_datetime_format=True)
        # select only those longitudes that cover North America
        self.fltTecDataDF = self.fltTecDataDF[ (self.fltTecDataDF["BndMlon"]\
                         <= self.mlonRngNA[0]) |\
                      (self.fltTecDataDF["BndMlon"] >= self.mlonRngNA[1]) \
                      ].reset_index(drop=True)

    def get_fltrd_locs(self, saveToCsv=True):
        """
        Get filtered locations for all unique times/dates
        present in the Data
        """
        import pandas
        uniqTimes = self.fltTecDataDF["date"].unique()
        # Loop through each of the times, filter trough loc
        # and store them in a single DF
        trghLocDFList = []
        for inpTime in uniqTimes:
            print "curr time--->", inpTime
            currTrghLocDF = self.filter_trough_loc(inpTime)
            trghLocDFList.append( currTrghLocDF )
            del currTrghLocDF
        trghLocDF = pandas.concat( trghLocDFList )
        if saveToCsv:
            trghLocDF.to_csv("../data/finTrghLocFltrd.txt", sep=' ',\
                       index=False)
        return trghLocDF


    def filter_trough_loc(self,inpTime):
        """
        Given an input time, apply some filters
        to TEC data so that we discard any bad locations
        that are identified...
        """
        import numpy
        # select data from the five time
        selTrDF = self.fltTecDataDF[ self.fltTecDataDF["date"] == inpTime ]
        # get a sorted list of glons
        sortedMlonArr = numpy.sort( selTrDF["BndMlon"] )
        # Identify sudden and big jumps in Long
        # We'll identify jumps by using the gradient
        # Function!
        mlonGradInds = numpy.where( numpy.diff( sortedMlonArr ) > self.jumpCutoff )
        # get the length of the segments
        segLgnthArr = []
        currStrtElmnt = 0
        for ele in mlonGradInds[-1]:
            segLgnthArr.append( ele - currStrtElmnt )
            currStrtElmnt = ele
        segLgnthArr.append( len(sortedMlonArr) - currStrtElmnt )
        # Now choose the segments from the segLgnthArr
        prevSegInd = 0 
        finTrghMlons = numpy.array( [] )
        for currSegLen in segLgnthArr:
            if prevSegInd == 0 :
                strtElementInd = prevSegInd
            else:
                strtElementInd = prevSegInd + 1
            endElementInd = prevSegInd + currSegLen
            if endElementInd == len(sortedMlonArr):
                endElementInd -= 1
            if currSegLen >= self.segLgthCutoff:
                segIndsSel = [ prevSegInd , prevSegInd + currSegLen ]
                finTrghMlons = numpy.append( finTrghMlons, sortedMlonArr[strtElementInd:endElementInd+1] )
            prevSegInd = prevSegInd + currSegLen
        # Only include the glons that are selected
        selTrDF = selTrDF[ selTrDF["BndMlon"].isin( finTrghMlons )\
                         ].reset_index(drop=True)
        # Now discard TEC values which are 2 stds away!!!!
        selTrDF = selTrDF[ \
                    selTrDF["minFltrdTecVal"] <= \
                    ( selTrDF["minFltrdTecVal"].mean()\
                     + 2 * selTrDF["minFltrdTecVal"].std() ) ]
        return selTrDF

    def plot_trgh_loc(self,trghDF,plotFileName="../figs/trghLocFltrd.pdf"):
        """
        Given a trough location DF plot the trough
        this includes, the equatorward and poleward
        boundaries as well as min location.
        """
        import matplotlib.pyplot as plt
        import seaborn as sns
        sns.set_style("darkgrid")
        sns.set_context("paper")
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot( trghDF["BndMlon"], trghDF["BndEquMlat"], "b^" )
        ax.plot( trghDF["BndMlon"], trghDF["minTecMlat"], "ro" )
        ax.plot( trghDF["BndMlon"], trghDF["BndPolMlat"], "bv" )
        ax.get_figure().savefig(plotFileName,bbox_inches='tight')
        plt.close(fig)