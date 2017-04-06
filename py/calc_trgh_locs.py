if __name__ == "__main__":
    """
    In the current code we'll loop through each and every
    file (representing l-o-s velocities for a given day)
    and get the best lshell fits out of them!!!
    """
    import pandas
    import datetime
    import locateTrough
    figsFldr = "../figs/sel-dates/"
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
                 datetime.datetime( 2011, 8, 6, 4, 0 ) ]
    for inpDT in inpDtList:
        print "currently working with--->", inpDT
        trObj = locateTrough.TroughLocator( inpDT, "/home/bharat/Documents/AllTec/" )
        medFltrdTec = trObj.apply_median_filter()
        trLocDF = trObj.find_trough_loc(medFltrdTec)
        fltrdTrghLocDF = trObj.filter_trough_loc(trLocDF)
        trObj.plotTecLocTrgh( trLocDF, medFltrdTec, \
        "../figs/raw-trough-loc-" + inpDT.strftime("%Y%m%d-%H%M") + ".pdf")
        trObj.plotTecLocTrgh( fltrdTrghLocDF, medFltrdTec, \
            "../figs/fltrd-trough-loc-" + inpDT.strftime("%Y%m%d-%H%M") + ".pdf")