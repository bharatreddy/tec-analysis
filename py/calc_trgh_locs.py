if __name__ == "__main__":
    """
    In the current code we'll loop through each and every
    file (representing l-o-s velocities for a given day)
    and get the best lshell fits out of them!!!
    """
    import pandas
    import datetime
    import locateTrough
    import os
    figsFldr = "/home/bharat/Documents/tec-plots/maps/"#"../figs/sel-dates/"
    inpDtList = [ datetime.datetime( 2011, 2, 5, 2, 30 ),\
                 datetime.datetime( 2011, 2, 5, 3, 0 ),\
                 datetime.datetime( 2011, 2, 5, 3, 30 ),\
                 datetime.datetime( 2011, 4, 9, 8, 30 ),\
                 datetime.datetime( 2011, 4, 9, 9, 0 ),\
                 datetime.datetime( 2011, 4, 9, 9, 30 ),\
                 datetime.datetime( 2011, 8, 1, 5, 0 ),\
                 datetime.datetime( 2011, 8, 1, 5, 30 ),\
                 datetime.datetime( 2011, 8, 1, 6, 0 ),\
                 datetime.datetime( 2011, 8, 1, 6, 30 ),\
                 datetime.datetime( 2011, 8, 1, 7, 0 ),\
                 datetime.datetime( 2011, 8, 1, 7, 30 ),\
                 datetime.datetime( 2011, 8, 6, 1, 0 ),\
                 datetime.datetime( 2011, 8, 6, 1, 30 ),\
                 datetime.datetime( 2011, 8, 6, 2, 0 ),\
                 datetime.datetime( 2011, 8, 6, 2, 30 ),\
                 datetime.datetime( 2011, 8, 6, 3, 0 ),\
                 datetime.datetime( 2011, 8, 6, 3, 30 ),\
                 datetime.datetime( 2011, 8, 6, 4, 0 ),\
                 datetime.datetime( 2012, 6, 18, 2, 0 ),\
                 datetime.datetime( 2012, 6, 18, 2, 30 ),\
                 datetime.datetime( 2012, 6, 18, 3, 0 ),\
                 datetime.datetime( 2012, 6, 18, 3, 30 ),\
                 datetime.datetime( 2012, 6, 18, 4, 0 ) ]
    # Read dates from saps file
    sapsDatesDF = pandas.read_csv( "../data/saps-dates.txt", delim_whitespace=True )
    sapsDatesDF['start_time'] = sapsDatesDF['start_time'].astype(str)
    sapsDatesDF["start_time"] = [ x.rjust( 4, "0" ) for \
                                    x in sapsDatesDF["start_time"] ]
    sapsDatesDF["start_time"] = pandas.to_datetime( \
                sapsDatesDF['date'].astype(str) + ":" +\
                 sapsDatesDF['start_time'], format='%Y%m%d:%H%M' )
    sapsDatesDF['end_time'] = sapsDatesDF['end_time'].astype(str)
    sapsDatesDF["end_time"] = [ x.rjust( 4, "0" ) for \
                                    x in sapsDatesDF["end_time"] ]
    sapsDatesDF["end_time"] = pandas.to_datetime( \
                sapsDatesDF['date'].astype(str) + ":" +\
                 sapsDatesDF['end_time'], format='%Y%m%d:%H%M')
    dateCnt = sapsDatesDF.shape[0]
    for index, row in sapsDatesDF.iterrows():
        if index < 10:
            continue
        print "num of days completed/remaining", index,"/", dateCnt
        # We need to iterate over the time range with in the same date
        inpDT = row["start_time"]
        delta = datetime.timedelta(days=1)
        while inpDT <= row["end_time"]:
            print "currently working with--->", inpDT
            inpDT += datetime.timedelta(seconds=5*60)
            trObj = locateTrough.TroughLocator( inpDT, "/home/bharat/Documents/AllTec/" )
            medFltrdTec = trObj.apply_median_filter()
            trLocDF = trObj.find_trough_loc(medFltrdTec)
            fltrdTrghLocDF = trObj.filter_trough_loc(trLocDF)
            fltrdPltFile = figsFldr + "fltrd-trough-loc-" + inpDT.strftime("%Y%m%d-%H%M") + ".pdf"
            trObj.plotTecLocTrgh( fltrdTrghLocDF, medFltrdTec, fltrdPltFile )
            # Write data to the file in append mode...
            if not os.path.isfile('../data/rawTrghLoc.txt'):
                trLocDF.to_csv("../data/rawTrghLoc.txt", sep=' ',\
                       index=False)
            else:
                trLocDF.to_csv("../data/rawTrghLoc.txt", sep=' ', mode='a',\
                       index=False, header=False)
            if not os.path.isfile('../data/fltrdTrghLoc.txt'):
                fltrdTrghLocDF.to_csv("../data/fltrdTrghLoc.txt", sep=' ',\
                       index=False)
            else:
                fltrdTrghLocDF.to_csv("../data/fltrdTrghLoc.txt", sep=' ', mode='a',\
                       index=False, header=False)
            del trLocDF
            del fltrdTrghLocDF