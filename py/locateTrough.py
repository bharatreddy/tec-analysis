class TroughLocator(object):
    """
    A class to identify the location of TEC trough
    given a time instance and a (5 min, 1 dg GLAT, GLON binned) 
    # TEC data file the one from madrigal!
    """
    def __init__(self, losdataFile, rbspSatAFile, \
             rbspSatBFile, inpSAPSDataFile=None, applyPOESBnd=False):
        import pandas