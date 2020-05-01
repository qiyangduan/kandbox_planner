
worker_names = {
    'list_display': ['worker_code'      
        ,'geo_longitude', 'geo_latitude'
        ] ,
    'model': { 
            'worker_code': 'Worker Code',
            'requested_worker_code': 'Requested Worker',
            'scheduled_worker_code': 'Scheduled Worker',
     },

    'list_filter': ['worker_code',]

}


job_names = {
    'list_display': [ 'job_code', 'job_type' ,  'planning_status','requested_start_datetime', 'scheduled_worker_code','scheduled_start_datetime',  'scheduled_duration_minutes', 'scheduled_share_status'  
        , 'geo_longitude', 'geo_latitude'],

    'list_filter' : [ 'job_type' ,  "scheduled_worker_code",'planning_status','scheduled_start_datetime',   "requested_worker_code",'requested_start_datetime', 'scheduled_share_status'],

    'readonly_fields':[ 'effective_from_date' ] # , 'last_update_by'  

}


absence_names = {
    'list_display': ['absence_code',  'absence_type', 'worker_code', 'start_datetime', 'end_datetime' , ]
}