pro get_tec_med_filt_data


common tec_data_blk


fname_event='/home/bharatr/Docs/data/sapsTECDates.txt' 
dt_skip_time=5.d ;;; we search data the grd file every 5 min


nel_arr_all = 2000
dateArr = lonarr(nel_arr_all)
minTimeArr = uintarr(nel_arr_all)
maxTimeArr = uintarr(nel_arr_all)

dateStr = lonarr(1)
minTime = uintarr(1)
maxTime = uintarr(1)

rcnt=0
OPENR, 1, fname_event
WHILE not eof(1) do begin
	;; read the data line by line

	READF,1, dateStr, minTime, maxTime
	currDate = ulong(dateStr)
	currMinTime = uint(minTime)
	currMaxTime = uint(maxTime)

	print, currDate, currMinTime, currMaxTime

	dateArr[rcnt] = currDate
	minTimeArr[rcnt] = currMinTime
	maxTimeArr[rcnt] = currMaxTime

	rcnt += 1

ENDWHILE         
close,1	

dateArr = dateArr[0:rcnt-1]
minTimeArr = minTimeArr[0:rcnt-1]
maxTimeArr = maxTimeArr[0:rcnt-1]



;; now unlike vels we just











; now instead of putting all the data in a single file
; we'll seperate data by event days into seperate files
; then deal with one event/day at a time!!!
baseDir = '/home/bharatr/Docs/data/tecMedFilt/'

for dtRdCnt=0.d,double(rcnt-1) do begin


	if dtRdCnt eq 0.d then begin
		fname_saps_tec = baseDir + 'tec-medFilt-' + strtrim( string(dateArr[dtRdCnt]), 2 ) + '.txt'
		print, 'OPENING FIRST EVENT FILE-->', fname_saps_tec
		openw,1,fname_saps_tec
		workingSapsFileDate = dateArr[dtRdCnt]
	endif else begin
		if workingSapsFileDate ne dateArr[dtRdCnt] then begin
			print, 'CLOSED FILE-->', fname_saps_tec
			close,1
			fname_saps_tec = baseDir + 'tec-medFilt-' + strtrim( string(dateArr[dtRdCnt]), 2 ) + '.txt'
			print, 'OPENING NEW FILE-->', fname_saps_tec
			openw,1,fname_saps_tec
			workingSapsFileDate = dateArr[dtRdCnt]
		endif
	endelse


	print, "working with---->", dateArr[dtRdCnt], minTimeArr[dtRdCnt], maxTimeArr[dtRdCnt]
	date = dateArr[dtRdCnt]


	;; need to check if minTime and maxTime are same. 
	;; In that case we'll just check for next 30 min of
	;; data
	if minTimeArr[dtRdCnt] ne maxTimeArr[dtRdCnt] then begin
		timeRange = [ minTimeArr[dtRdCnt], maxTimeArr[dtRdCnt] ]
	endif else begin
		simMinMaxTime = minTimeArr[dtRdCnt]
		sfjul, date, simMinMaxTime, simMinMaxJuls
		sfjul, dateNew, timeRange, [ simMinMaxJuls, simMinMaxJuls + 30.d/1440.d ],/jul_to_date
		print, "NEW TIME RANGE SET---->", timeRange
	endelse


	sfjul,date,timeRange,sjul_search,fjul_search
	del_jul=dt_skip_time/1440.d ;;; This is the time step used to read the data --> Selected to be 60 min

	nele_search=((fjul_search-sjul_search)/del_jul)+1 ;; Num of n-min times to be searched..


	tec_read, date

	for srch=0.d,double(nele_search-1) do begin

	        ;;;Calculate the current jul
	        juls_curr=sjul_search+srch*del_jul
	    	sfjul,datesel,timesel,juls_curr,/jul_to_date
	    	print, "currently working with-->", datesel,timesel
	    	tec_median_filter,date=date,time=timesel, threshold=0.10
	    	; get tec vals
	    	medarr = tec_median.medarr
			lats = tec_median.lats
			lons = tec_median.lons
			juls = tec_median.juls
			dlat = median_info.dlat
			dlon = median_info.dlon


			dd = min( abs( juls - juls_curr ), minind )
			for a=0, n_elements(lats)-2 do begin
				for o=0, n_elements(lons)-2 do begin
					alats = lats[a]
					alons = lons[o]
					tecvalue = medarr[a,o,minind]
					if finite(tecvalue) eq 1 then begin

	                    printf,1, datesel,timesel, alats, alons, tecvalue, dlat, dlon, $
	                                                                format = '(I8, I5, 2f9.4, f11.4, 2f9.4)'

					endif
				endfor
			endfor



	endfor








endfor


close,1

end