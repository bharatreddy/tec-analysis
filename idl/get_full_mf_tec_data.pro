pro get_full_mf_tec_data


common tec_data_blk


baseDir = '/home/bharatr/Docs/data/tecMedFilt-alldata/'

date_rng = [ 20150101, 20151231 ]
timeRange=[0000,2400]


dt_skip_time=5.d ;;; we search data the grd file every 5 min

del_jul_nday=24.d*60.d/1440.d

sfjul, date_rng, [0000, 2400], sjul_nday, fjul_nday

ndays_search=((fjul_nday-sjul_nday)/del_jul_nday)+1 ;; Num of 2-min times to be searched..


sfjul, date_rng, timeRange, sjul_day, fjul_day

print, "ndays_search", ndays_search
for srchDay=0.d,double(ndays_search) do begin
	

	juls_day=sjul_day+srchDay*del_jul_nday
	sfjul,dateDay,timeDay,juls_day,/jul_to_date

	sfjul,dateDay,timeRange,sjul_search,fjul_search
	del_jul=dt_skip_time/1440.d ;;; This is the time step used to read the data 


	nele_search=((fjul_search-sjul_search)/del_jul)+1 ;; Num of n-min times to be searched..


    if srchDay eq 0.d then begin
		fname_saps_tec = baseDir + 'tec-medFilt-' + strtrim( string(dateDay), 2 ) + '.txt'
		print, 'OPENING FIRST EVENT FILE-->', fname_saps_tec
		openw,1,fname_saps_tec
		workingSapsFileDate = dateDay
	endif else begin
		if workingSapsFileDate ne dateDay then begin
			print, 'CLOSED FILE-->', fname_saps_tec
			close,1
			fname_saps_tec = baseDir + 'tec-medFilt-' + strtrim( string(dateDay), 2 ) + '.txt'
			print, 'OPENING NEW FILE-->', fname_saps_tec
			openw,1,fname_saps_tec
			workingSapsFileDate = dateDay
		endif
	endelse


	nele_search=((fjul_search-sjul_search)/del_jul)+1 ;; Num of n-min times to be searched..


	tec_read, dateDay

	for srch=0.d,double(nele_search-1) do begin

	        ;;;Calculate the current jul
	        juls_curr=sjul_search+srch*del_jul
	    	sfjul,datesel,timesel,juls_curr,/jul_to_date
	    	print, "currently working with-->", datesel,timesel, "completed days-->", srchDay, ndays_search
	    	tec_median_filter,date=dateDay,time=timesel, threshold=0.10
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