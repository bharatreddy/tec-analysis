pro get_tec_med_filt_data


common radarinfo
common rad_data_blk


fname_event='/home/bharatr/Docs/data/sapsVelDates.txt' 

nel_arr_all = 2000
dateArr = lonarr(nel_arr_all)
radIdArr = intarr(nel_arr_all)
minTimeArr = uintarr(nel_arr_all)
maxTimeArr = uintarr(nel_arr_all)

dateStr = lonarr(1)
radId = intarr(1)
minTime = uintarr(1)
maxTime = uintarr(1)

rcnt=0
OPENR, 1, fname_event
WHILE not eof(1) do begin
	;; read the data line by line

	READF,1, dateStr, radId, minTime, maxTime
	currDate = ulong(dateStr)
	currRadId = uint(radId)
	currMinTime = uint(minTime)
	currMaxTime = uint(maxTime)

	print, currDate, currRadId, currMinTime, currMaxTime

	dateArr[rcnt] = currDate
	radIdArr[rcnt] = currRadId
	minTimeArr[rcnt] = currMinTime
	maxTimeArr[rcnt] = currMaxTime

	rcnt += 1

ENDWHILE         
close,1	

dateArr = dateArr[0:rcnt-1]
radIdArr = radIdArr[0:rcnt-1]
minTimeArr = minTimeArr[0:rcnt-1]
maxTimeArr = maxTimeArr[0:rcnt-1]
