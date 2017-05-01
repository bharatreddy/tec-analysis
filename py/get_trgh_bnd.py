if __name__ == "__main__":
    """
    In the current code we'll loop through each and every
    file (representing l-o-s velocities for a given day)
    and get the best lshell fits out of them!!!
    """
    import pandas
    import datetime
    import numpy
    import medFiltTrghLoc
    import os
    # Loop through the dir which contains med filt tec data
    # and get a list of all the files
    mfTecDir = "/home/bharat/Documents/medFiltTec/"
    for root, dirs, files in os.walk(mfTecDir):
        for fName in files:
            print "currently working with----->", root + fName
            mftrObj = medFiltTrghLoc.MFTrough( root + fName )
            allTimesList = mftrObj.get_all_uniq_times()
            for currTS in numpy.nditer(allTimesList):
                inpDT = datetime.datetime.utcfromtimestamp(currTS.astype(int)*1e-9)
                print "current Time--->", inpDT
                trLocDF = mftrObj.find_trough_loc(inpDT)
                fltrdTrLocDF = mftrObj.filter_trough_loc(trLocDF)
                # Write data to the file in append mode...
                if not os.path.isfile('../data/newRawTrghLoc.txt'):
                    trLocDF.to_csv("../data/newRawTrghLoc.txt", sep=' ',\
                           index=False)
                else:
                    trLocDF.to_csv("../data/newRawTrghLoc.txt", sep=' ',\
                     mode='a', index=False, header=False)
                if fltrdTrLocDF is not None:
                    if not os.path.isfile('../data/newFltrdTrghLoc.txt'):
                        fltrdTrLocDF.to_csv("../data/newFltrdTrghLoc.txt",\
                                 sep=' ', index=False)
                    else:
                        fltrdTrLocDF.to_csv("../data/newFltrdTrghLoc.txt",\
                                 sep=' ', mode='a',\
                               index=False, header=False)
                del trLocDF
                del fltrdTrLocDF