pro sd_tec_saps_plot

common rad_data_blk
common radarinfo
common tec_data_blk
common omn_data_blk
common aur_data_blk
common kpi_data_blk
common amp_data_blk



dateSel = 20120618
timeSel = 0300


;; set plot/map parameters
xrangePlot = [-44, 44]
yrangePlot = [-44,30]
velScale = [0,800]
tecScale = [0.,20.]
coords = "mlt"



tec_read, dateSel
rad_map_read, dateSel

sfjul,dateSel,timeSel,juls_curr




ps_open, '/home/bharatr/Docs/plots/tec-sd-saps' + strtrim( string(dateSel), 2) + '.ps'


clear_page
set_format, /sardi



rad_load_colortable,/leicester



mapPos = define_panel(1,1.4,0,0.4, aspect=aspect,/bar)

map_plot_panel,date=dateSel,time=timeSel,coords=coords,/no_fill,xrange=xrangePlot, $
        yrange=yrangePlot,pos=mapPos,/isotropic,grid_charsize='0.5',/north, charsize = 0.5




rad_load_colortable, /bw
;;plot tec vectors
tec_median_filter,date=dateSel,time=timeSel, threshold=0.10
overlay_tec_median, date=dateSel, time=timeSel, scale=tecScale, coords=coords




rad_load_colortable, /leicester
rad_map_overlay_vectors, date = dateSel, time=timeSel, coords = coords, $
                 /no_fov_names, /no_show_Nvc,/no_vector_scale, scale=velScale, symsize=0.25;,fixed_color = 215


overlay_coast, coords=coords, jul=juls_curr, /no_fill
map_overlay_grid, grid_linestyle=0, grid_linethick=1, grid_linecolor=get_gray()
;map_label_grid, coords=coords

rad_load_colortable, /leicester
;plot_colorbar, 1., 1.4, -0.15, 0.4, /square,scale=tecScale,legend='Total Electron Content [TECU]', level_format='(f6.2)',param='power',/keep_first_last_label;, /left
plot_colorbar, 1., 1.4, -0.15, 0.4, /square, scale=velScale, parameter='velocity',/keep_first_last_label

ps_close, /no_filename


end





