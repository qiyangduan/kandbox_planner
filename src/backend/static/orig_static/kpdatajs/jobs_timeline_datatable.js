
var global_loaded_data = {};
var global_job_data_latlng = {};

// 准备用adminlte的color： https://adminlte.io/themes/AdminLTE/pages/calendar.html
// https://adminlte.io/themes/AdminLTE/pages/UI/general.html

//https://www.datafocus.ai/wp-content/uploads/2018/10/word-image.png
//https://www.datafocus.ai/14461.html
//#37A2DA #67E0E3 #FFDB5C #FF9F7F #E062AE #EA6A6A #97C979 #FB8D34 #FEE BAE #FDC F 84 #48B788 #9F4EF4 #7894EA
/*
var job_types = { 
    'FS' : { name: 'Fixed Schedule' ,color: '#7b9ce1'},
    'FD' : { name: 'Fixed Day' ,color: '#75d874'},
    'N' :  { name: 'Normal' , color: '#72b362'} ,
    'NN' : { name: 'Night Service' ,color: '#dc77dc'},   
    'CO' : { name: 'Call Out' ,color: '#F0F048'},
    'NA' : { name: 'Need Appointment' ,color: '#e0bc78'},
    'nan' : { name: 'Unknown' ,color: '#D2A8A8'},
    'P' : { name: 'Planned' ,color: '#B6B6B6'},
    'CFLT' : { name: 'Conflicted' ,color: '#ff0000'}, // #bd6d6c

};
*/
var job_types = { 
    'FS' : { name: 'Fixed Schedule' ,color: '#7b9ce1'},
    'N' :  { name: 'Normal' , color: '#72b362'} ,
    'nan' : { name: 'Unknown' ,color: '#D2A8A8'},
    'CFLT' : { name: 'Conflicted' ,color: '#ff0000'}, // #bd6d6c
    
};


// "R_nan_0_0_0"
// console.log(categories);
// a category is a worker
function renderWorkingTime(params, api) {
    //console.log(api.value(0), api.value(1), api.value(2)) // worker, start, end
    var categoryIndex = api.value(0);
    var jobStartTimeMS = api.value(1);
    var jobEndTimeMS = api.value(2);

    var start = api.coord([jobStartTimeMS, categoryIndex]); 
    var end = api.coord([jobEndTimeMS, categoryIndex]);

    var worker_timeline_height = api.size([0, 1])[1] 
    var height = (worker_timeline_height * 0.05) ;
    if (height < 2) {
        height = 2
    }
     
    var start_y = (api.size([0, 1])[1] * 0)   ; 

    new_style = api.style(); 

    var rectShape = echarts.graphic.clipRectByRect({
        x: start[0],
        y: start[1]  - (worker_timeline_height*0.5) - 1 , //- 1 to overwrite the normal dashed splitline
        width: end[0] - start[0],
        height: height
    }, {
        x: params.coordSys.x,
        y: params.coordSys.y,
        width: params.coordSys.width,
        height: params.coordSys.height
    });
    var childRectShape = {
        type: 'rect',
        shape: rectShape, 
        style: new_style
    }

    return childRectShape

    if ( start[0] > params.coordSys.x + params.coordSys.width || end[0] + params.coordSys.width < params.coordSys.x  ) {
        return
    }

    //var groupShape = {}
    var line_start = start[0]
    if (line_start < params.coordSys.x ) {
        line_start =  params.coordSys.x
    } 
    var line_end = end[0]
    if (line_end > params.coordSys.x  + params.coordSys.width ) {
        line_end =  params.coordSys.x  + params.coordSys.width
    } 

    
    return  {
            type: 'group',
            children: [
                {
                    type: 'line',
                    shape: {
                        x1:  line_start , 
                        y1: (start[1] - start_y ) +  (height ),
                        x2:  line_start , 
                        y2: (start[1] - start_y ) ,
                    },
                    style: new_style
                },
                {
                    type: 'line',
                    shape: {
                        x1:  line_start, 
                        y1: (start[1] - start_y ) +  (height  ),
                        x2: line_end , 
                        y2: (start[1] - start_y ) +  (height  ),
                    },
                    style: new_style
                },
                {
                    type: 'line',
                    shape: {
                        x1: line_end, 
                        y1: (start[1] - start_y ) +  (height  ),
                        x2: line_end , 
                        y2: (start[1] - start_y )  ,
                    },
                    style: new_style
                },
            ]
        } 

 
}





// "R_nan_0_0_0"
// console.log(categories);
// a category is a worker
function renderItem(params, api) {
    //console.log(api.value(0), api.value(1), api.value(2)) // worker, start, end
    var categoryIndex = api.value(0);
    var jobStartTimeMS = api.value(1);
    var jobEndTimeMS = api.value(2);
    var travelTimeMS = api.value(6) * 1000 * 60


    var start = api.coord([jobStartTimeMS, categoryIndex]); 
    var end = api.coord([jobEndTimeMS, categoryIndex]);
    var conflict_level = api.value(4) ; //0; // 
    var nbr_conflicts =  api.value(5) + 1; //1; //
    var height = (api.size([0, 1])[1] * 0.6) /  nbr_conflicts  ;
    var start_y = (api.size([0, 1])[1] * 0.2)   ;
    // console.log(conflict_level, nbr_conflicts, height, start_y)
    
    var travelTimeStartXY = api.coord([jobStartTimeMS - travelTimeMS, categoryIndex])
    var travelTime = start[0] - travelTimeStartXY[0]
    // console.log([api.value(0), api.value(1), api.value(2), api.value(6), '--', travelTime, '-',  ((end[0] - start[0]) / 3)])


    if ( start[0] > params.coordSys.x + params.coordSys.width || start[0] + params.coordSys.width < params.coordSys.x  ) {
        return
    }

    new_style = api.style(); 

    var rectShape = echarts.graphic.clipRectByRect({
        x: start[0],
        y: (start[1] - start_y ) +  (height * conflict_level ) ,
        width: end[0] - start[0],
        height: height
    }, {
        x: params.coordSys.x,
        y: params.coordSys.y,
        width: params.coordSys.width,
        height: params.coordSys.height
    });
    
    var childRectShape = {
        type: 'rect',
        shape: rectShape, 
        style: new_style
    }

    //var groupShape = {}
    if ( start[0] - travelTime < params.coordSys.x  ) {
        var line_end = start[0]
        if (line_end < params.coordSys.x ) {
            line_end =  params.coordSys.x
        } 
        return  {
            type: 'group',
            children: [
                {
                    type: 'circle',
                    shape: {
                        cx:  params.coordSys.x , 
                        cy: (start[1] - start_y ) +  (height * (  conflict_level + 0.5 ) ),
                        r:  height/6
                    },
                    style: new_style
                },
                {
                    type: 'line',
                    shape: {
                        x1:  params.coordSys.x , 
                        y1: (start[1] - start_y ) +  (height * (  conflict_level + 0.5 ) ),
                        x2: line_end , 
                        y2: (start[1] - start_y ) +  (height * (  conflict_level + 0.5 ) ),
                    },
                    style: new_style
                },
                childRectShape
            ]
        } 
    } else {
        return {
            type: 'group',
            children: [
                {
                    type: 'circle',
                    shape: {
                        cx:  start[0] - travelTime, 
                        cy: (start[1] - start_y ) +  (height * (  conflict_level + 0.5 ) ),
                        r:  height/6
                    },
                    style: new_style
                },
                {
                    type: 'line',
                    shape: {
                        x1:  start[0] - travelTime, 
                        y1: (start[1] - start_y ) +  (height * (  conflict_level + 0.5 ) ),
                        x2: start[0] , 
                        y2: (start[1] - start_y ) +  (height * (  conflict_level + 0.5 ) ),
                    },
                    style: new_style
                },
                childRectShape
            ]
        } 
    }

    return groupShape;
}


// 基于准备好的dom，初始化echarts实例
var myChart = echarts.init(document.getElementById('jobs_timeline'));

function date_formatter_hhmm(val) {
    //console.log("axis", new Date(val) )  
    var vdate= new Date(val)
    var texts=[vdate.getHours(),vdate.getMinutes()]
    return texts.join(":")
    
}

function date_formatter_mmdd_hhmm(val) {
    //console.log("axis", new Date(val) ) 
    vdate = new Date(val) 
    mmdd = [(vdate.getMonth() + 1) , vdate.getDate()].join('-');
    // hhmm = vdate.toTimeString().split(' ')[0];
    var minute = "" + vdate.getMinutes()
    if (minute.length < 2) 
        minute = "0" + minute;
    var hour = "" + vdate.getHours()
        if (hour.length < 2) 
        hour = "0" + hour;
    hhmm = hour + ":" + minute;
    return mmdd + ' ' + hhmm // 
    
}

function draw_chart(loaded_data) { 
    var categories = []
    var timeline_data = []
    
    //var startTime = new Date('2019-01-01T00:00:00').getTime();
    // var endTime   = startTime + (24*60*60*1000);
    var startTime = new Date(loaded_data["start_time"] ).getTime();
    var endTime   = new Date(loaded_data["end_time"] ).getTime(); 


    
    // {nbr_conflicts: 1, index: 3}
    // workers_list = []
    //jobs_list = []
    
    //console.log(data);
    workers_dict = loaded_data["workers_dict"]

    var working_timeslot_data = []
    for (var key in workers_dict){
        //console.log( key, workers_dict[key] );
        categories.push(key);

        currentDate = new Date(loaded_data["start_time"] )
        while (currentDate < new Date(loaded_data["end_time"] ) ){
            weekDayIndex = currentDate.getDay()
            day_timeslot = JSON.parse(workers_dict[key]['weekly_working_minutes'])[weekDayIndex]
            working_timeslot_data.push([
                key,
                currentDate.getTime() + day_timeslot[0]*60000,
                currentDate.getTime() + day_timeslot[1]*60000
                //new Date(currentDate.getTime() + day_timeslot[0]*60000), new Date(currentDate.getTime() + day_timeslot[1]*60000),
            ])
            //console.log(currentDate, weekDayIndex)
            currentDate.setDate(currentDate.getDate() + 1);
        }
        //console.log('loaded worker data: ', working_timeslot_data)
        
    } 

    jobs_list = loaded_data["planned_jobs_list"] 
    if (jobs_list.length < 1) {
        alert ("No jobs found!")
        //return
        //still draw workers.
    }
    jobs_list.forEach(function(job){
        global_job_data_latlng[job["job_code"]] = [job['geo_latitude'], job['geo_longitude']]


        var baseTime = new Date(job["scheduled_start_datetime"]);
        var travelTime =  job["scheduled_travel_minutes"] 
        var duration = job["scheduled_duration_minutes"]*60*1000;
        var job_worker_code = job["scheduled_worker_code"]
        var conflict_level =job["conflict_level"]
        var worker_max_conflict_level = workers_dict[job["scheduled_worker_code"]]["max_conflict_level"]

        var itemTypeStr =   job["job_type"] ;
        var jobServiceType = itemTypeStr.split("_")[0];

        var node_color = job_types[ jobServiceType ]["color"]
        var node_itemStyle =  {
            normal: {
                color: node_color, 
                borderWidth : 1,
                borderColor: node_color,
                text: "duan-1",
            }}

        if (conflict_level >0 ) {
            node_itemStyle =  {
                normal: {
                    color: node_color, 
                    borderWidth : 1,
                    borderColor: job_types[ "CFLT" ] ["color"],
                }}
        }
        timeline_data.push({
            name: job["job_code"] ,
            value: [
                workers_dict[job_worker_code]["index"], //0
                baseTime ,
                new Date (baseTime.getTime() + duration),
                duration,
                conflict_level,   // #4
                worker_max_conflict_level,
                job["scheduled_travel_minutes_before"] ,
                job["scheduled_travel_minutes_after"] ,
                job['scheduled_travel_prev_code'], // #8
                //job['geo_latitude']  // #9
            ],
            itemStyle: node_itemStyle
        });
        
    }); 
    // 使用刚指定的配置项和数据显示图表。
    // console.log("show list of workers: ", categories)

    var workerCount = 2
    if (categories.length < 2) {
        workerCount = 2
    } else if (categories.length > 10) {
        workerCount = 10
    } else {
        workerCount = categories.length
    }
    
    chartHeight  = workerCount * 50 

    document.getElementById("jobs_timeline").style.height = (chartHeight + 150) + 'px';


    option = {
        tooltip: {
            formatter: function (params) {
                // console.log(params )
                return params.marker + params.name + ' (time: '
                 + date_formatter_hhmm (params.value[1]) + '-'
                 + date_formatter_hhmm(params.value[2]) + ' , travel: '
                 + parseFloat( params.value[6]).toFixed(1)
                 + ' min)';
            }
        }, 
        grid: {
            height: (chartHeight + 50) + 'px',
            //width: ( window.innerWidth - 100) +'px'
        },
        dataZoom: [{
            type: 'slider',
            filterMode: 'weakFilter',
            showDataShadow: false,
            top: chartHeight  + 140,
            height: 10,
            borderColor: 'transparent',
            backgroundColor: '#e2e2e2',
            handleIcon: 'M10.7,11.9H9.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4h1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7v-1.2h6.6z M13.3,22H6.7v-1.2h6.6z M13.3,19.6H6.7v-1.2h6.6z', // jshint ignore:line
            handleSize: 20,
            handleStyle: {
                shadowBlur: 6,
                shadowOffsetX: 1,
                shadowOffsetY: 2,
                shadowColor: '#aaa'
            },
            labelFormatter: ''
        }, {
            type: 'inside',
            filterMode: 'weakFilter'
        }],
        xAxis: {
            min: startTime,
            max: endTime,
            type:"time",
            scale: true,
            axisLabel: {
                formatter: date_formatter_mmdd_hhmm  
            }
        },
        yAxis: {
            type:'category',
            data: categories,
            splitLine:{ show:true, 
                lineStyle: {
                    // 使用深浅的间隔色
                    color: ['rgba(53, 54, 38, 0.50)'],
                    type:'dashed'

            }},
            axisLine: {show: true},  
            //https://github.com/apache/incubator-echarts/issues/3485
            axisLabel: {interval:0}, 
        },
        series: [
            {
                name: "jobs_boxes",
                type: 'custom',
                renderItem: renderItem,
                itemStyle: {
                    normal: {
                        opacity: 0.8
                    }
                },
                encode: {
                    x: [1, 2],
                    y: 0
                },
                data: timeline_data
            },  
            {
                name: "working_timeslots",
                type: 'custom',
                renderItem: renderWorkingTime,
                itemStyle: {
                    normal: {   
                        opacity: 1,
                        color: '#72b362',
                        borderWidth:2,
                        borderType:'solid'
                    }
                },
                encode: {
                    x: [1, 2],
                    y: 0
                },
                data: working_timeslot_data
            }, //working_timeslot_data
        ]
    };

    myChart.setOption(option);
 
    
    //根据窗口的大小变动图表 
    //https://blog.csdn.net/qq_38382380/article/details/80460729
    window.onresize = function(){
        //myChartContainer();
        myChart.resize();
        //myChart1.resize();    //若有多个图表变动，可多写

    }
    myChart.on('click', function (params) {
        console.log(params.name, global_job_data_latlng[params.value[8]], global_job_data_latlng[params.name]);
        // window.location.href="${base}/admin/file/list.htm";
        // window.open(`/admin/kpdata/job/${params.name}/change/`) 
        $('#myModalLabel').text("Routing path from Job (" + params.value[8] + ") to (" + params.name  + ")");

        show_job_route  (global_job_data_latlng[params.value[8]], global_job_data_latlng[params.name]) 

    });


}
function download_as_image() {
    var img = ($('canvas')[0]).toDataURL('image/png')
    document.write('<img src="'+img+'"/>')
}


function load_Data_and_Draw() {
  
    query_data = { 
        "start_date": $('#start_date').val(), 
        "end_date": $('#end_date').val(),  
        "planner_code": $('#planner_code').val(), 
        "source_system_code": $('#source_system_code').val() ,
        "game_code": $('#game_code').val() ,
        "worker_list": $('#worker_list').val() ,

    } 

    $.ajax({
        url: '/kpdata/games',
        dataType: 'json',
        type: 'get', 
        processData: false,
        success: function( data, textStatus, jQxhr ){
            //$('#response pre').html( JSON.stringify( data ) );
            console.log("Loaded game codes by ajax: ", data)
            // https://stackoverflow.com/questions/47824/how-do-you-remove-all-the-options-of-a-select-box-and-then-add-one-option-and-se
            $('#game_code')
                .find('option')
                .remove()
            for(var i=0; i< data.length;i++) {
            //creates option tag
                jQuery('<option/>', {
                    value: data[i]['game_code'],
                    html:  data[i]['game_code']
                    }).appendTo('#game_code'); //appends to select if parent div has id dropdown
            } 
        
        },
        error: function( jqXhr, textStatus, errorThrown ){
            console.log( errorThrown );
        }
    });

    console.log(query_data)


    $.ajax({
        url: '/kpdata/worker_job_filtered.json',
        dataType: 'json',
        type: 'post',
        contentType: 'application/json',
        data: JSON.stringify( query_data ),
        processData: false,
        success: function( data, textStatus, jQxhr ){
            //$('#response pre').html( JSON.stringify( data ) );
            console.log("Loaded jobs by ajax: ", data)
            global_loaded_data = data
            draw_chart(loaded_data = data)

            //$('#jobs_datatable').DataTable().clear().draw();
            datatable = window.job_datatable
            datatable.clear().draw();
            datatable.rows.add(data.not_planned_jobs_list); // Add new data
            datatable.columns.adjust().draw(); // Redraw the DataTable


        
        },
        error: function( jqXhr, textStatus, errorThrown ){
            console.log( errorThrown );
        }
    });

}
/*
//myChart.showLoading();

myFunction() ;

$.get('/kpdata/worker_job_echarts.json').done(function (loaded_data) {
    draw_jobs(loaded_data);
});  


var tdata1    = [
    [ "Tiger Nixon", "System Architect", "Edinburgh", "5421", "2011/04/25", "$320,800" ],
    [ "Garrett Winters", "Accountant", "Tokyo", "8422", "2011/07/25", "$170,750" ],
    [ "Ashton Cox", "Junior Technical Author", "San Francisco", "1562", "2009/01/12", "$86,000" ],
    [ "Cedric Kelly", "Senior Javascript Developer", "Edinburgh", "6224", "2012/03/29", "$433,060" ],
]


var tdata    = [ 
    {job_code: "1101-0-FS", job_type: "FS", scheduled_worker_code: "Duan", scheduled_start_datetime: "2019-11-01T09:52:00", 
     scheduled_start_minutes: 592,  
     scheduled_duration_minutes: 69,
     conflict_level: 0,
     scheduled_travel_minutes: 0
    }, 
    {job_code: "1101-4-N", job_type: "N", scheduled_worker_code: "Duan", scheduled_start_datetime: "2019-11-01T11:17:00", 
    scheduled_start_minutes: 677,
    scheduled_duration_minutes: 90,
    conflict_level: 0,
    scheduled_travel_minutes: 0
   }, 
]

*/

$(document).ready(function() {

    
    for (var key in job_types) {
        if (job_types.hasOwnProperty(key)) { 
            //console.log(key, job_types[key]);
            // check if the property/key is defined in the object itself, not in parent
            job_color = job_types[ key ]["color"]
            new_button_html = '<button id="legend_button_n_' + key +'"  class="btn btn-sm btn-default" type="button">'+job_types[ key ]["name"]+'</button>'

            $('#legend_buttons').append(new_button_html);
            $('#legend_button_n_' + key).css("background",job_types[ key ]["color"])   ; 
            
        } 
    }


    //$('#legend_button_FS').css("background",job_types[ 'FS' ]["color"])   ; 
    //$('#legend_button_N').css("background",job_types[ 'N' ]["color"])   ; 


    window.job_datatable = $('#jobs_datatable').DataTable( {
        //"ajax": "data/arrays.txt"
        data:  [],
        columns: [
            { "data": "job_code" },
            { "data": "job_type" }, 
            { "data": "scheduled_worker_code" },
            { "data": "scheduled_start_datetime" },
            { "data": "scheduled_duration_minutes" },
            { "data": "scheduled_travel_minutes_before" },
            { "data": "conflict_level" }, 
            null 
        ],
        "columnDefs": [ {
            "targets": -1,
            "data": null,
            "defaultContent": "<button>Plan it!</button>"
        } ],

        "deferRender": true
    } );
    /*


            "fnCreatedRow": function( nRow, aData, iDataIndex ) {
                $('td:eq(7)', nRow).append("<div class='col1d'><button class='editBut'>Plan it</button></div>");
            },
*/
    $('#jobs_datatable tbody').on( 'click', 'button', function () {
        var data = window.job_datatable.row( $(this).parents('tr') ).data();
        // alert( data["job_code"] +"'s travel is: "+ data[ "scheduled_travel_minutes_before" ] );
        /*
        $('#newJobPlanModal').text("Suggested Slots from Job (" + data["job_code"] + ")");
        $('#newJobPlanModal_job_type').value  =  data["job_type"] ;
        // $('#newJobPlanModal_scheduled_duration_minutes').value = data["scheduled_duration_minutes"]  ;
*/


        $('#newJobPlanModal_jobCode_label').text("Suggested Slots from Job (" + data["job_code"] + ")");
        $('#newJobPlanModal_scheduled_worker_code').val(data["scheduled_worker_code"])
        $('#newJobPlanModal_job_type').val(data["job_type"])
        $('#newJobPlanModal_scheduled_start_datetime').val(data["scheduled_start_datetime"])

        $('#newJobPlanModal').modal('show')
        console.log(data,data["scheduled_worker_code"] , $('#newJobPlanModal_scheduled_worker_code').val()  )
        // $('#newJobPlanModal_tableBody').empty()
        for (var i = 2; i < 4; i++) { 
            $('#newJobPlanModal_tableBody').append(`
                <tr id="row_${i}" > 
                    <td>  ${i}.   </td>
                    <td>  ${data["scheduled_worker_code"]}   </td>
                    <td>  ${data["scheduled_start_datetime"]}   </td>
                    <td><span class="badge bg-red">15%</span></td>
                </tr>
            ` )
            
        }


    } );

    myChart.showLoading();
    load_Data_and_Draw() ;
    myChart.hideLoading();


} );
 
