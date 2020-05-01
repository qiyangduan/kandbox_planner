// 初始化echarts实例
var myChart = echarts.init(document.getElementById('jobs_timeline'), null, { renderer: 'svg' });
//
var global_loaded_data = {};
var global_job_dict = {};
var global_planner_game_list = {}
var globalRecommendedSlotsData = {}


var HEIGHT_RATIO = 0.6;


/*
var POS_INDEX_node_type = 1
    //var POS_WORKER_INDEX_node_type = 7
    // var POS_WORKING_TIME_INDEX_node_type = 3

var VALUE_JOB_INDEX_node_type = 0
var VALUE_WORKER_INDEX_node_type = 1
var VALUE_WORKING_TIME_INDEX_node_type = 2
*/


var POS_JOB_INDEX_worker_index = 0
var POS_JOB_INDEX_start_datetime = 1
var POS_JOB_INDEX_end_datetime = 2
var POS_JOB_INDEX_job_code = 3 + 0
var POS_JOB_INDEX_job_type = 4 + 0
var POS_JOB_INDEX_travel_minutes_before = 5 + 0
var POS_JOB_INDEX_travel_prev_code = 6 + 0
var POS_JOB_INDEX_conflict_level = 7 + 0
var POS_JOB_INDEX_worker_code = 8
var POS_JOB_INDEX_geo_longitude = 9 + 0
var POS_JOB_INDEX_geo_latitude = 10 + 0
var POS_JOB_INDEX_changed_flag = 11 + 0


var POS_WORKER_INDEX_worker_index = 0
var POS_WORKER_INDEX_worker_code = 3
var POS_WORKER_INDEX_skills = 1 + 0
var POS_WORKER_INDEX_max_conflict_level = 2 + 0
var POS_WORKER_INDEX_geo_longitude = 4 + 0
var POS_WORKER_INDEX_geo_latitude = 5 + 0
var POS_WORKER_INDEX_weekly_working_minutes = 6 + 0

var POS_WORKER_INDEX_selected = 7


var POS_WORKING_TIME_INDEX_worker_index = 0
var POS_WORKING_TIME_INDEX_start_ms = 1 + 0
var POS_WORKING_TIME_INDEX_end_ms = 2 + 0

// 放弃，用adminlte的color： https://adminlte.io/themes/AdminLTE/pages/calendar.html
// https://adminlte.io/themes/AdminLTE/pages/UI/general.html

//https://www.datafocus.ai/wp-content/uploads/2018/10/word-image.png
//https://www.datafocus.ai/14461.html
//#37A2DA #67E0E3 #FFDB5C #FF9F7F #E062AE #EA6A6A #97C979 #FB8D34 #FEE BAE #FDC F 84 #48B788 #9F4EF4 #7894EA

var job_types = {
    'FS': { name: 'Fixed Schedule', color: '#7b9ce1', zlevel: 10 },
    'FD': { name: 'Fixed Day', color: 'rgb(111, 160, 199)', zlevel: 10 },
    'N': { name: 'Normal', color: '#72b362', zlevel: 10 },
    'NN': { name: 'Night Service', color: '#ffff00', zlevel: 10 },
    'NA': { name: 'Need Appointment', color: '#e0bc78', zlevel: 10 },
    'EVT': { name: 'Diary Event', color: '#d9d9d9', zlevel: 5 },
    'CFLT': { name: 'Conflicted', color: '#ff0000', zlevel: 100 }, // #bd6d6c
    'NEW': { name: 'New-Not saved', color: '#dc77dc', zlevel: 200 }, // #bd6d6c
    //'nan': { name: 'Unknown', color: '#D2A8A8' },

};

var dropJobStyleDict = {
    'OK': { lineWidth: 2, fill: 'rgba(0,255,0,0.1)', stroke: 'rgba(0,255,0,0.8)', lineDash: [6, 3] },
    'Warning': { lineWidth: 2, fill: 'rgba(255, 193, 7, 0.3)', stroke: 'rgba(255, 193, 7, 0.9)', lineDash: [6, 3] },
    'Error': { lineWidth: 2, fill: 'rgba(255,0,0,0.5)', stroke: 'rgba(255,0,0,1)', lineDash: [6, 3] },
};

function getNodeItemStyle(job) {
    var jobType = job[POS_JOB_INDEX_job_type]
    var conflict_level = job[POS_JOB_INDEX_conflict_level]

    var jobServiceType = jobType.split("_")[0];
    var sharedStatus = jobType.split("_")[5];
    var node_color = job_types[jobServiceType]["color"]
    var node_itemStyle = {
        normal: {
            color: node_color,
            borderWidth: 1,
            borderColor: node_color,
            opacity: 0.6,
        }
    }

    if (conflict_level > 0) {
        node_itemStyle = {
            normal: {
                color: node_color,
                borderWidth: 1,
                borderColor: job_types["CFLT"]["color"],
                opacity: 0.6,
                borderType: 'solid'

            }
        }
    }

    if (sharedStatus != 'N') {
        if (sharedStatus == 'P') {
            node_itemStyle.normal.borderColor = '#000000'
            node_itemStyle.normal.borderWidth = 3
            node_itemStyle.normal.opacity = 1
        } else if (sharedStatus == 'S') {
            node_itemStyle.normal.borderWidth = 1
            node_itemStyle.normal.borderColor = '#dc77dc'
            node_itemStyle.normal.borderType = 'dashed'
        } else {
            console.log("Unkown sharedStatus code", sharedStatus)
        }

    }

    return node_itemStyle

}


function renderWorker(params, api) {
    var workerIndex = api.value(POS_WORKER_INDEX_worker_index);
    var y = api.coord([0, workerIndex - 0.45])[1];
    if (y < params.coordSys.y + 3) {
        return;
    }
    var selectedIndicator = api.value(POS_WORKER_INDEX_selected);
    var selectedFill = '#ff0000'
    if (selectedIndicator == 0) {
        selectedFill = '#368c6c'
    }
    return {
        type: 'group',
        position: [10, y],
        children: [{
            type: 'rect',
            shape: {
                x: 0,
                y: -20,
                width: 90,
                height: 20,
            },
            style: {
                fill: selectedFill
            }
        }, {
            type: 'text',
            style: {
                x: 24,
                y: -3,
                text: api.value(POS_WORKER_INDEX_worker_code),
                textVerticalAlign: 'bottom',
                textAlign: 'center',
                textFill: '#000'
            }
        }, {
            type: 'text',
            style: {
                x: 75,
                y: -2,
                textVerticalAlign: 'bottom',
                textAlign: 'center',
                text: api.value(POS_WORKER_INDEX_max_conflict_level),
                textFill: '#000'
            }
        }]
    };
}



function renderWorkerSplitLine(params, api) {
    var workerIndex = api.value(POS_WORKER_INDEX_worker_index);

    //var x_max = myChart.getModel().getComponent('xAxis').axis.extent

    var y = api.coord([0, workerIndex + HEIGHT_RATIO - 0.1])[1];
    if (y < params.coordSys.y + 3) {
        return;
    }

    return {
        type: 'group',
        children: [{
                type: 'line',
                shape: {
                    x1: params.coordSys.x,
                    y1: y,
                    x2: params.coordSys.x + params.coordSys.width,
                    y2: y,
                },

                style: {
                    "opacity": 0.2,
                    /*
                                       "fill": "#7b9ce1",
                                       "textPosition": "inside",
                                       "textDistance": 5,
                                       "textFill": "#fff",
                                       "textStroke": "#c23531",
                                       "textStrokeWidth": 2,
                                       "insideRollbackOpt": {
                                           "autoColor": "#c23531",
                                           "isRectText": true
                                       },
                                       "insideRollback": {},
                                       "fontStyle": "normal",
                                       "fontWeight": "normal",
                                       "fontSize": 12,
                                       "fontFamily": "sans-serif",
                                       "text": null, */

                    /*               
                    lineWidth: 1,
                    fill: 'rgba(0,255,0,0.1)',
                    stroke: 'rgba(0,255,0,0.8)',
                    lineDash: [6, 3]
                    */

                    "stroke": "#008000"
                }
            },
            {
                type: 'rect',
                shape: {
                    x: params.coordSys.x + 100,
                    y: y,
                    width: 0,
                    height: 10
                },
                style:
                /* api.style() */
                {
                    normal: {

                        color: "#fff",
                        borderWidth: 1,
                        borderColor: 'rgba(53, 54, 38, 0.3)',
                        opacity: 0.6,
                        borderType: 'dashed'
                    }
                }
            }
        ]
    };
}


function renderWorkingTime(params, api) {
    //console.log(api.value(0), api.value(1), api.value(2)) // worker, start, end
    var workerIndex = api.value(POS_WORKING_TIME_INDEX_worker_index);
    var jobStartTimeMS = api.value(POS_WORKING_TIME_INDEX_start_ms);
    var jobEndTimeMS = api.value(POS_WORKING_TIME_INDEX_end_ms);

    var start = api.coord([jobStartTimeMS, workerIndex]);
    var end = api.coord([jobEndTimeMS, workerIndex]);

    var worker_timeline_height = api.size([0, 1])[1]
    var height = (worker_timeline_height * 0.05);
    if (height < 2) {
        height = 2
    }

    //var start_y = (api.size([0, 1])[1] * 0);

    new_style = api.style();

    var rectShape = echarts.graphic.clipRectByRect({
        x: start[0],
        y: start[1] - (worker_timeline_height * 0.5) - 1, //- 1 to overwrite the normal dashed splitline
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
}


// "R_nan_0_0_0"

function renderJob(params, api) {
    //console.log(api.value(POS_JOB_INDEX_job_code), api.value(POS_JOB_INDEX_changed_flag));

    //console.log(api.value(0), api.value(1), api.value(2)) // worker, start, end
    var workerIndex = api.value(POS_JOB_INDEX_worker_index);
    var jobStartTimeMS = api.value(POS_JOB_INDEX_start_datetime);
    var jobEndTimeMS = api.value(POS_JOB_INDEX_end_datetime);
    var travelTimeMS = api.value(POS_JOB_INDEX_travel_minutes_before) * 1000 * 60

    var jobType = api.value(POS_JOB_INDEX_job_type);
    var start = api.coord([jobStartTimeMS, workerIndex]);
    var end = api.coord([jobEndTimeMS, workerIndex]);
    var conflict_level = 0; //api.value(7); //0; // 
    if (workerIndex >= global_loaded_data.workers_data.length) {
        console.log(workerIndex, api.value(POS_JOB_INDEX_job_code))
    }
    var nbr_conflicts = global_loaded_data.workers_data[workerIndex][POS_WORKER_INDEX_max_conflict_level] + 1; //api.value(5) + 1; //1; // 

    // api.value(8) -> workerIndex


    var height = (api.size([0, 1])[1] * HEIGHT_RATIO) / nbr_conflicts;
    var start_y = (api.size([0, 1])[1] * 0.2);
    // console.log(conflict_level, nbr_conflicts, height, start_y)

    var travelTimeStartXY = api.coord([jobStartTimeMS - travelTimeMS, workerIndex])
    var travelTime = start[0] - travelTimeStartXY[0]


    if (start[0] > params.coordSys.x + params.coordSys.width || start[0] + params.coordSys.width < params.coordSys.x) {
        return
    }
    if (!(api.value(POS_JOB_INDEX_job_code) in global_job_dict)) {
        return
    }


    var jobServiceType = jobType.split("_")[0];
    //var sharedStatus = jobType.split("_")[5];
    var node_z = job_types[jobServiceType]["zlevel"]


    new_style = api.style();
    to_add_style = global_job_dict[api.value(POS_JOB_INDEX_job_code)]['node_item_style'];
    new_style.fill = to_add_style.normal.color
    new_style.stroke = to_add_style.normal.borderColor

    var rectShape = echarts.graphic.clipRectByRect({
        x: start[0],
        y: (start[1] - start_y) + (height * conflict_level),
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

    var newJobWhiteRect = null;
    if ((api.value(POS_JOB_INDEX_job_code) == "0423-1-N")) {
        // pause for debug
        console.log("0423-1-N -- ", api.value(POS_JOB_INDEX_job_code), api.value(POS_JOB_INDEX_changed_flag))
    }
    if (rectShape) {
        if (api.value(POS_JOB_INDEX_changed_flag) == 1) { //&& (jobServiceType != 'EVT')
            // var whiteRectStyle = 
            newJobWhiteRect = {
                type: 'rect',
                shape: {
                    x: rectShape.x + (rectShape.width / 4),
                    y: rectShape.y + (rectShape.height / 4),
                    width: rectShape.width / 2,
                    height: rectShape.height / 2,
                },
                style: {
                    fill: job_types['NEW']["color"] //'#FFFFFF'
                }
            }
        } else {
            newJobWhiteRect = {
                type: 'rect',
                shape: {
                    x: rectShape.x + (rectShape.width / 4),
                    y: rectShape.y + (rectShape.height / 4),
                    width: rectShape.width / 2,
                    height: rectShape.height / 2,
                },
                style: {
                    fill: 'rgba(255, 255, 255, 0)'
                }
            }

        }

    }
    var jobCodeText = null;
    if (jobServiceType != 'EVT') {
        jobCodeText = {
            type: 'text',
            style: {
                x: rectShape.x,
                y: rectShape.y + height,
                text: api.value(POS_JOB_INDEX_job_code),
                textVerticalAlign: 'bottom',
                textAlign: 'left',
                textFill: 'rgba(255, 255, 255, 0.1)'
            }
        }
    }

    //var groupShape = {}
    if (start[0] - travelTime < params.coordSys.x) {
        //This travel time line should be reduced and restricted to xAxis at zero
        var line_end = start[0]
        if (line_end < params.coordSys.x) {
            line_end = params.coordSys.x
        }
        return {
            type: 'group',
            z: node_z,
            children: [{
                    type: 'circle',
                    shape: {
                        cx: params.coordSys.x,
                        cy: (start[1] - start_y) + (height * (conflict_level + 0.5)),
                        r: height / 6
                    },
                    style: new_style
                },
                {
                    type: 'line',
                    shape: {
                        x1: params.coordSys.x,
                        y1: (start[1] - start_y) + (height * (conflict_level + 0.5)),
                        x2: line_end,
                        y2: (start[1] - start_y) + (height * (conflict_level + 0.5)),
                    },
                    style: new_style
                },
                childRectShape,
                newJobWhiteRect,
                jobCodeText
            ]
        }
    } else {
        //This travel time line is full.
        return {
            type: 'group',
            z: node_z,
            children: [{
                    type: 'circle',
                    shape: {
                        cx: start[0] - travelTime,
                        cy: (start[1] - start_y) + (height * (conflict_level + 0.5)),
                        r: height / 6
                    },
                    style: new_style
                },
                {
                    type: 'line',
                    shape: {
                        x1: start[0] - travelTime,
                        y1: (start[1] - start_y) + (height * (conflict_level + 0.5)),
                        x2: start[0],
                        y2: (start[1] - start_y) + (height * (conflict_level + 0.5)),
                    },
                    style: new_style
                },
                childRectShape,
                newJobWhiteRect,
                jobCodeText
            ]
        }
    }

    //return groupShape;
}

function drawJobTimelineChart(loaded_data) { // draw_chart
    var categories = [];
    // var timeline_data = []

    // var startTime = new Date('2019-01-01T00:00:00').getTime();
    // var endTime   = startTime + (24*60*60*1000);
    var startTime = new Date(loaded_data["start_time"]).getTime();
    var endTime = new Date(loaded_data["end_time"]).getTime();


    // workers_list = []
    //jobs_list = []

    //console.log(data);
    workers_data = loaded_data["workers_data"]

    var working_timeslot_data = []

    currentWorkerList = $('#worker_list').val().split(',')

    //reset global job dict 
    global_worker_dict = {}

    workers_data.forEach(function(w) {
        //for (var key in workers_dict){
        //console.log( key, workers_dict[key] );
        // w.splice(POS_INDEX_node_type, 0, VALUE_WORKER_INDEX_node_type);
        //w[POS_WORKER_INDEX_node_type] = VALUE_WORKER_INDEX_node_type
        worker_index = w[POS_WORKER_INDEX_worker_index]


        global_worker_dict[w[POS_WORKER_INDEX_worker_code]] = worker_index

        if (currentWorkerList.includes(worker_index)) {
            w[POS_WORKER_INDEX_selected] = 1
        } else {
            w[POS_WORKER_INDEX_selected] = 0
        }

        categories.push(worker_index);

        currentDate = new Date(loaded_data["start_time"])

        while (currentDate < new Date(loaded_data["end_time"])) {
            weekDayIndex = currentDate.getDay()
            day_timeslot = JSON.parse(w[POS_WORKER_INDEX_weekly_working_minutes])[weekDayIndex]
            working_timeslot_data.push([
                    worker_index,
                    //VALUE_WORKING_TIME_INDEX_node_type,
                    currentDate.getTime() + day_timeslot[0] * 60000,
                    currentDate.getTime() + day_timeslot[1] * 60000

                    //new Date(currentDate.getTime() + day_timeslot[0]*60000), new Date(currentDate.getTime() + day_timeslot[1]*60000),
                ])
                //console.log(currentDate, weekDayIndex)
            currentDate.setDate(currentDate.getDate() + 1);
        }
        //console.log('loaded worker data: ', working_timeslot_data)

    })

    planned_jobs_data = loaded_data["planned_jobs_data"]
    if (planned_jobs_data.length < 1) {
        alert("No planned jobs are found!")
            //Do not return, I still draw workers.
    }
    //planned_jobs_data
    //reset global job dict 
    global_job_dict = {}
    planned_jobs_data.forEach(function(job, index, array) {
        //job.splice(POS_INDEX_node_type, 0, VALUE_JOB_INDEX_node_type);

        //job[POS_JOB_INDEX_node_type] = VALUE_JOB_INDEX_node_type
        if ((job[POS_JOB_INDEX_job_code] == "1016439_1_TRBSB_2_13")) {
            // console.log(job)
        }

        global_job_dict[job[POS_JOB_INDEX_job_code]] = {
            data_latlng: [job[POS_JOB_INDEX_geo_latitude], job[POS_JOB_INDEX_geo_longitude]],
            job_index: index
        }



        var jobType = job[POS_JOB_INDEX_job_type];
        // var jobServiceType = itemTypeStr.split("_")[0];
        var conflict_level = job[POS_JOB_INDEX_conflict_level]

        node_itemStyle = getNodeItemStyle(job) //Type, conflict_level
        global_job_dict[job[POS_JOB_INDEX_job_code]]['node_item_style'] = node_itemStyle


    });

    // 使用刚指定的配置项和数据显示图表。
    // console.log("show list of workers: ", categories)

    var chartHeight = 3 * 40

    if (categories.length > 250) {
        chartHeight = 250 * 15
    } else {
        chartHeight = categories.length * 25
    }


    var local_option = {
        tooltip: {
            enterable: true,
            hideDelay: 800,
            formatter: function(params) {
                // console.log(params.seriesId)
                switch (params.seriesId) {
                    case 'jobsSeries':
                        var jobInfo = params.marker + params.value[POS_JOB_INDEX_job_code] + '( ' +
                            params.value[POS_JOB_INDEX_worker_code] + ', time: ' +
                            date_formatter_hhmm(params.value[POS_JOB_INDEX_start_datetime]) + '-' +
                            date_formatter_hhmm(params.value[POS_JOB_INDEX_end_datetime]) + ' , travel: ' +
                            Math.ceil(parseFloat(params.value[POS_JOB_INDEX_travel_minutes_before])) +
                            ' min)';

                        var tooltip_str = [
                            "<div contenteditable=\"true\">",
                            // '<button onclick="console.log(\'click\');">click me</button>',
                            jobInfo,
                            "</div>"
                        ].join(' ')

                        return tooltip_str
                        break;
                    case 'workersSeries':
                        //console.log(params)
                        var jobInfo = params.marker + params.value[POS_WORKER_INDEX_worker_code] // + ' (Working hours:  10 hours)';

                        var tooltip_str = [
                            "<div contenteditable=\"true\">",
                            // '<button onclick="console.log(\'click\');">click me</button>',
                            jobInfo,
                            "</div>"
                        ].join(' ')
                        return tooltip_str
                        break;
                    default:
                        return null
                }

            }
        },
        grid: {
            //height: (chartHeight + 50) + 'px',
            //width: ( window.innerWidth - 100) +'px'
            show: true,
            top: 30,
            bottom: 60,
            left: 100,
            right: 20,
            backgroundColor: '#fff',
            borderWidth: 0
        },

        dataZoom: [{
                type: 'slider',
                filterMode: 'weakFilter',
                showDataShadow: false,
                top: chartHeight + 180,
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
            },
            /*{
                       type: 'inside',
                       filterMode: 'weakFilter',
                       zoomOnMouseWheel: false,
                       moveOnMouseMove: false
                   }*/
        ],
        xAxis: {
            min: startTime,
            max: endTime,
            type: "time",
            axisLine: { show: false },
            scale: true,
            axisLabel: {
                formatter: date_formatter_mmdd_hhmm
            }
        },
        yAxis: {
            // https://github.com/apache/incubator-echarts/issues/2943
            // silent: false, //does not work! 2020-03-16 08:57:26
            axisTick: { show: false },
            axisLine: { show: false },
            axisLabel: { show: false },
            min: -1,
            max: global_loaded_data.workers_data.length,
            splitLine: {
                show: false,
                interval: 0,
                lineStyle: {
                    color: ['rgba(53, 54, 38, 0.3)'],
                    type: 'dashed'
                }
            },

            /*
                type: 'category',
            data: categories,
            axisLine: { show: true },
            //https://github.com/apache/incubator-echarts/issues/3485
            axisLabel: { interval: 0 },
            */
        },
        series: [{
                id: 'jobsSeries',
                //name: "jobs_boxes",
                type: 'custom',
                renderItem: renderJob,
                dimensions: global_loaded_data.jobs_dimensions,
                itemStyle: {
                    normal: {
                        opacity: 0.8
                    }
                },
                encode: {
                    x: [1, 2],
                    y: 0
                },
                data: global_loaded_data.planned_jobs_data //timeline_data
            },
            { //worker
                id: 'workersSeries',
                type: 'custom',
                renderItem: renderWorker,
                //dimensions: global_loaded_data.worker_dimensions,
                encode: {
                    x: -1, // Then this series will not controlled by x.
                    y: 0
                },
                data: global_loaded_data.workers_data,
                /*echarts.util.map(_rawData.parkingApron.data, function(item, index) {
                    return [index].concat(item);
                })*/
            },

            { //worker
                id: 'workersSplitLineSeries',
                type: 'custom',
                renderItem: renderWorkerSplitLine,
                //dimensions: global_loaded_data.worker_dimensions,
                encode: {
                    x: -1, // Then this series will not controlled by x.
                    y: 0
                },
                data: echarts.util.map(global_loaded_data.workers_data, function(item, index) {
                    return [index].concat(item);
                })
            },
            { //working_timeslot_data
                name: "workingTimeSeries",
                type: 'custom',
                renderItem: renderWorkingTime,
                itemStyle: {
                    normal: {
                        opacity: 0.6,
                        color: '#72b362',
                        borderWidth: 1,
                        borderType: 'solid'
                    }
                },
                encode: {
                    x: [1, 2],
                    y: 0
                },
                data: working_timeslot_data
            }
        ]
    };
    /*
    var tmp = myChart.getOption(); //获取所有当前属性和数据
    if (tmp) {
        tmp.series.splice(0, 4); //删除数据中2~5的数据
        myChart.clear(); //清空所有属性和数据
        myChart.setOption(tmp); //删除后的数据重新绘制
    }
    myChart.clear()
    myChart.setOption({}, true);
    */
    myChart.setOption(local_option, true);

    $('#jobs_timeline').css("height", chartHeight + 200);
    myChart.resize();

    /*
    setTimeout(() => {
            myChart.setOption(option, true)
        }, 500)
        //

    */
    //根据窗口的大小变动图表 
    //https://blog.csdn.net/qq_38382380/article/details/80460729
    window.onresize = function() {
        //myChartContainer();
        myChart.resize();
        //myChart1.resize();    //若有多个图表变动，可多写

    }
    myChart.on('click', onJobTimelineChartClick_all);


}



function load_Data_and_Draw_for_Query_Data(query_data, msg) {


    //Not necessary, but works: https://docs.djangoproject.com/en/3.0/ref/csrf/
    //I followed this script: https://gist.github.com/alanhamlett/6316427
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (settings.type == 'POST' || settings.type == 'PUT' || settings.type == 'DELETE') {
                function getCookie(name) {
                    var cookieValue = null;
                    if (document.cookie && document.cookie != '') {
                        var cookies = document.cookie.split(';');
                        for (var i = 0; i < cookies.length; i++) {
                            var cookie = jQuery.trim(cookies[i]);
                            // Does this cookie string begin with the name we want?
                            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                                break;
                            }
                        }
                    }
                    return cookieValue;
                }
                if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                    // Only send the token to relative URLs i.e. locally.
                    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                }
            }
        }
    });
    $.ajax({
        url: '/kpdata/worker_job_dataset.json', //
        //url: '/static/orig_static/kpdatajs/fake_jobs.json', //  src/kpdjango/static/orig_static/kpdatajs/fake_jobs.json
        dataType: 'json',
        type: 'post',
        contentType: 'application/json',
        data: JSON.stringify(query_data),
        processData: false,
        success: function(data, textStatus, jQxhr) {
            //$('#response pre').html( JSON.stringify( data ) );
            console.log("Loaded worker_job_dataset: ", data)
            global_loaded_data.planned_jobs_data = null
            global_loaded_data.workers_data = null
            global_loaded_data = null
            global_job_dict = {}
            global_loaded_data = data
            drawJobTimelineChart(loaded_data = global_loaded_data)

            initDrag()

            //$('#jobs_datatable').DataTable().clear().draw();
            datatable = window.job_datatable
            datatable.clear().draw();
            datatable.rows.add(convertUnplannedJob2Datatable(global_loaded_data.not_planned_jobs_data)); // Add new data
            datatable.columns.adjust().draw(); // Redraw the DataTable

            myChart.hideLoading();
            if (msg) {
                msg.close()
            }

        },
        error: function(jqXhr, textStatus, errorThrown) {
            console.log(errorThrown);
        }
    });

}

$(".call_alert").on("click", function() {
    alert($(this).data("msg")); // ★★★ Dose not!!! ★★★
});

function load_Data_and_Draw() {

    query_data = {
        "start_date": $('#start_date').val(),
        "end_date": $('#end_date').val(),
        "source_system_code": $('#source_system_code').val(),
        /*
        "planner_code": 'opti1day', //$('#planner_code').val(), 
        "game_code": 'opti1day-20191102', //$('#game_code').val() ,
        "worker_list": '', //$('#worker_list').val() ,
        */
        "planner_code": $('#planner_code').val(),
        "game_code": $('#game_code').val(),
        "worker_list": $('#worker_list').val(),
    }
    load_Data_and_Draw_for_Query_Data(query_data, null)



}
/*
//myChart.showLoading();

*/

$(document).ready(function() {



    var today = new Date();
    var new_day_ms = new Date(new Date().getTime() + (86400000 * 2));
    var today_str = today.toISOString().substr(0, 10).replace("-", "").replace("-", "") //(today.getFullYear() + '-' + (today.getMonth() + 1) + '-' + today.getDate() );
    var new_day_str = new_day_ms.toISOString().substr(0, 10).replace("-", "").replace("-", "")

    $("#start_date").val(today_str);
    $("#end_date").val(new_day_str);

    for (var key in job_types) {
        if (job_types.hasOwnProperty(key)) {
            //console.log(key, job_types[key]);
            // check if the property/key is defined in the object itself, not in parent
            job_color = job_types[key]["color"]

            // job_types[key]["name"], now i use key for shorter, 2020-03-29 09:21:27, duan
            new_button_html = '<button id="legend_button_n_' + key + '"  class="btn btn-sm btn-default" type="button">' + key + '</button>'

            $('#legend_buttons').append(new_button_html);
            $('#legend_button_n_' + key).css("background", job_types[key]["color"]);

        }
    }

    window.job_datatable = $('#jobs_datatable').DataTable({
        //"ajax": "data/arrays.txt"
        data: [],
        columns: [
            { title: "job_code" },
            { title: "job_type" },
            { title: "Default Tech" },
            { title: "Start" },
            { title: "End" },
            //{ title: "travel_minutes" },
            { title: "Longitude" },
            { title: "Latitude" },
            { title: "Action" },
            //{ title: "Action 2" },
        ],

        "columnDefs": [{
            "targets": -1,
            "data": null,
            "defaultContent": "<button>Plan it!</button>"
        }],

        "deferRender": true
    });
    $('#jobs_datatable tbody').on('click', 'button', function() {
        var data = window.job_datatable.row($(this).parents('tr')).data();
        // alert( data["job_code"] +"'s travel is: "+ data[ "scheduled_travel_minutes_before" ] );
        /*
        $('#newJobPlanModal').text("Suggested Slots from Job (" + data["job_code"] + ")");
        $('#newJobPlanModal_job_type').value  =  data["job_type"] ;
        // $('#newJobPlanModal_scheduled_duration_minutes').value = data["scheduled_duration_minutes"]  ;
*/
        jobCode = data[0];
        //day5 = new Date(new Date().getTime() + (1000 * 60 * 60 * 24 * 5)).toISOString().substr(5, 11).replace("T", " ");
        //day0 = new Date(new Date().getTime() + (1000 * 60 * 60 * 24 * 0)).toISOString().substr(5, 11).replace("T", " ");

        day0 = global_loaded_data.start_time.substr(5, 11).replace("T", " ");
        day5 = new Date(Date.parse(global_loaded_data.start_time) + (1000 * 60 * 60 * 24 * 5)).toISOString().substr(5, 11).replace("T", " ");



        //if (global_job_dict[jobCode][POS_JOB_INDEX_start_datetime] > ) {
        if (data[3] > day5) {
            alert("only 5 days are allowed for planning")
            return
        };
        if (data[3] < day0) {
            alert("Can not plan past jobs")
            return
        };

        $('#newJobPlanModal_jobCode_label').text("Suggested Slots from Job (" + jobCode + ")");

        $('#newJobPlanModal_job_type').val(data[1])
        $('#newJobPlanModal_scheduled_worker_code').val(data[2]); // "scheduled_worker_code"
        // $('#newJobPlanModal_scheduled_start_datetime').val(new Date(data[1]).toISOString()) //"scheduled_start_datetime"
        $('#newJobPlanModal_scheduled_start_datetime').val(data[3]) //"scheduled_start_datetime"


        // console.log(data,data["scheduled_worker_code"] , $('#newJobPlanModal_scheduled_worker_code').val()  )


        $.ajax({
            url: '/kpdata/get_slots_single_job.json',
            dataType: 'json',
            type: 'post',
            contentType: 'application/json',
            data: JSON.stringify({
                jobCode: data[0],
                startDay: $('#start_date').val()
            }),
            processData: false,

            success: function(slots_data, textStatus, jQxhr) {
                console.log("Loaded single job slots by ajax: ", slots_data)

                globalRecommendedSlotsData['slots_data'] = slots_data
                globalRecommendedSlotsData['jobCode'] = data[0]

                $('#newJobPlanModal_tableBody').empty()
                for (var i = 0; i < slots_data.length; i++) {
                    $('#newJobPlanModal_tableBody').append(`
                        <tr id="row_${i}" > 
                            <td>  ${i}.   </td>
                            <td>  ${slots_data[i]['scheduled_worker_code']}   </td>
                            <td>  ${new Date(slots_data[i]['js_start_time']).toISOString() }   </td>
                            <td><span class="badge bg-red" onclick="addJobSelectedSlot(${i})">${slots_data[i]['score']*10}%</span></td>
                        </tr>
                    `)
                }
                $('#newJobPlanModal').modal('show')

            },
            error: function(jqXhr, textStatus, errorThrown) {
                console.log(errorThrown);
            }
        });




    });

    $.ajax({
        url: '/kpdata/games',
        dataType: 'json',
        type: 'get',
        processData: false,
        success: function(data, textStatus, jQxhr) {
            //$('#response pre').html( JSON.stringify( data ) );
            console.log("Loaded game codes by ajax: ", data)
                // https://stackoverflow.com/questions/47824/how-do-you-remove-all-the-options-of-a-select-box-and-then-add-one-option-and-se
                // $('#game_code') .find('option')  .remove()
            global_planner_game_list['latest'] = ['latest']
            $('#game_code').value = 'latest';


            for (var i = 0; i < data.length; i++) {
                if (!(data[i]['planner_code'] in global_planner_game_list)) {
                    global_planner_game_list[data[i]['planner_code']] = [data[i]['game_code']]
                    jQuery('<option/>', {
                        value: data[i]['planner_code'],
                        html: data[i]['planner_code']
                    }).appendTo('#planner_code'); //appends to select if parent div has id dropdown

                } else {
                    global_planner_game_list[data[i]['planner_code']].push(data[i]['game_code'])
                }
                //creates option tag
                jQuery('<option/>', {
                    value: data[i]['game_code'],
                    html: data[i]['game_code']
                }).appendTo('#game_code'); //appends to select if parent div has id dropdown
            }

        },
        error: function(jqXhr, textStatus, errorThrown) {
            console.log(errorThrown);
        }
    });

    myChart.showLoading();
    load_Data_and_Draw();
    //myChart.hideLoading();


});





// ----------------------------------------------------
// --  Enable Dragging
// ----------------------------------------------------




var _draggable = false;
var _draggingEl;
var _dropShadow;
var _draggingCursorOffset = [0, 0];
var _draggingTimeLength;
var _draggingRecord;
var _dropRecord;
var _cartesianXBounds = [];
var _cartesianYBounds = [];
var _rawData;
var _autoDataZoomAnimator;


var _single_job_drop_check_ajay_lock = false

function onDragSwitchClick(model, api, type) {
    _draggable = !_draggable;

}

function onChangeDragBehaviour() {
    //return
    //
    myChart.off('click');
    var dragBehaviorCode = $('#click_behaviour').val()
    if (dragBehaviorCode == 'drag_n_drop') {
        _draggable = true;

    } else {
        _draggable = false;
        myChart.on('click', onJobTimelineChartClick_all);
        /*
        if (dragBehaviorCode == 'check_map') {
            myChart.on('click', onChartClick_ShowMap);
        } else { //  (dragBehaviorCode == 'show_job') 
            myChart.on('click', onChartClick_ShowJobAdmin);
        }
        */
    }
}
//: idea is that i have have a single "onclick" entry. 
function onJobTimelineChartClick_all(params) {
    var dragBehaviorCode = $('#click_behaviour').val()
    if (dragBehaviorCode == 'check_map') {
        onChartClick_ShowMap(params);
    } else if (dragBehaviorCode == 'show_job') { //  
        onChartClick_ShowJobAdmin(params);
    } else {
        console.log("I do nothing")
    }
}

function onChartClick_ShowMap(params) {
    //console.log("to show job route, from: ", params.value[6], global_job_dict[params.value[6]]['data_latlng'], " to job: ",
    //    params.value[3], global_job_dict[params.value[3]]['data_latlng'] )
    switch (params.seriesId) {
        case 'jobsSeries':
            if (params.value[POS_JOB_INDEX_travel_prev_code] in global_job_dict) {
                $('#myModalLabel').text("Routing path from Job (" + params.value[POS_JOB_INDEX_travel_prev_code] + ") to (" + params.value[POS_JOB_INDEX_job_code] + ")"); //params.name 
                show_job_route(global_job_dict[params.value[POS_JOB_INDEX_travel_prev_code]]['data_latlng'], global_job_dict[params.value[POS_JOB_INDEX_job_code]]['data_latlng'])
            } else {
                alert("Sorry, this visit has no previous visit in the same day, and I don't know home GPS.");
            }

            break;
        case 'workersSeries':
            workerIndex = params.value[POS_WORKER_INDEX_worker_index]
            workerCode = params.value[POS_WORKER_INDEX_worker_code]

            currentWorkerList = $('#worker_list').val().split(',')
            const listWorkerIndex = currentWorkerList.indexOf(workerCode);
            if (listWorkerIndex > -1) { // currentWorkerList.includes(worker_code)
                global_loaded_data.workers_data[workerIndex][POS_WORKER_INDEX_selected] = 0
                currentWorkerList.splice(listWorkerIndex, 1);
            } else {
                global_loaded_data.workers_data[workerIndex][POS_WORKER_INDEX_selected] = 1
                currentWorkerList.splice(listWorkerIndex, 0, workerCode);

            }
            $('#worker_list').val(currentWorkerList.join(','))
            myChart.setOption({
                series: {
                    id: 'workersSeries',
                    data: global_loaded_data.workers_data
                }
            });


            break;
        default:
            return null
    }

}

function onChartClick_ShowJobAdmin(params) {
    switch (params.seriesId) {
        case 'jobsSeries':
            window.open(`/kpdata/job/${params.value[POS_JOB_INDEX_job_code]}/change/`)

            break;
        case 'workersSeries':
            window.open(`/kpdata/worker/${params.value[POS_WORKER_INDEX_worker_code]}/change/`)
            break;
        default:
            return null
    }

}

function initDrag() {

    myChart.on('mousedown', function(param) {
        if (!_draggable || !param || param.seriesIndex == null) {
            return;
        }
        _single_job_drop_check_ajay_lock = false

        // Drag start
        _draggingRecord = {
            dataIndex: param.dataIndex,
            categoryIndex: param.value[POS_JOB_INDEX_worker_index],
            timeArrival: param.value[POS_JOB_INDEX_start_datetime],
            timeDeparture: param.value[POS_JOB_INDEX_end_datetime]
        };
        var style = { fill: 'rgba(0,0,0,0.4)' };

        _draggingEl = addOrUpdateBar(_draggingEl, _draggingRecord, style, 100);
        _draggingCursorOffset = [
            _draggingEl.position[0] - param.event.offsetX,
            _draggingEl.position[1] - param.event.offsetY
        ];
        _draggingTimeLength = _draggingRecord.timeDeparture - _draggingRecord.timeArrival;
    });

    myChart.getZr().on('mousemove', function(event) {
        //console.log(event)
        if (!_draggingEl) {
            return;
        }

        var cursorX = event.offsetX;
        var cursorY = event.offsetY;

        // Move _draggingEl.
        _draggingEl.attr('position', [
            _draggingCursorOffset[0] + cursorX,
            _draggingCursorOffset[1] + cursorY,
        ]);

        prepareDrop();

        //autoDataZoomWhenDraggingOutside(cursorX, cursorY);
    });

    myChart.getZr().on('mouseup', function() {
        // Drop
        // console.log('mouseup updateRawData, duan 2020-02-19 18:42:23')

        if (_draggingEl && _dropRecord) {

            updateRawData() // && 
        }
        dragRelease();
    });
    myChart.getZr().on('globalout', dragRelease);

    function dragRelease() {
        //_autoDataZoomAnimator.stop();

        if (_draggingEl) {
            myChart.getZr().remove(_draggingEl);
            _draggingEl = null;
        }
        if (_dropShadow) {
            myChart.getZr().remove(_dropShadow);
            _dropShadow = null;
        }
        _dropRecord = _draggingRecord = null;
        myChart.setOption({
            title: {
                text: '', //'0.3, Conflict',
                //position: ''
            }
        });
    }

    function addOrUpdateBar(el, itemData, style, z) {
        var pointArrival = myChart.convertToPixel('grid', [itemData.timeArrival, itemData.categoryIndex]);
        var pointDeparture = myChart.convertToPixel('grid', [itemData.timeDeparture, itemData.categoryIndex]);

        var barLength = pointDeparture[0] - pointArrival[0];
        var barHeight = Math.abs(
            myChart.convertToPixel('grid', [0, 0])[1] - myChart.convertToPixel('grid', [0, 1])[1]
        ) * HEIGHT_RATIO;

        if (!el) {
            el = new echarts.graphic.Rect({
                shape: { x: 0, y: 0, width: 0, height: 0 },
                style: style,
                z: z
            });
            myChart.getZr().add(el);
        }
        el.attr({
            shape: { x: 0, y: 0, width: barLength, height: barHeight },
            position: [pointArrival[0], pointArrival[1] - barHeight + (barHeight / 2)]
        });
        return el;
    }


    function addOrUpdateDroppingJob() {

        if (_single_job_drop_check_ajay_lock) {
            // Last api call is not finished yet.

            //console.log("Last api call is not finished yet, not to check: ", _dropRecord)
            return
        }
        var z = 99




        console.log("to check: ", _dropRecord)
        _single_job_drop_check_ajay_lock = true
        $.ajax({
            url: '/kpdata/single_job_drop_check.json',
            dataType: 'json',
            type: 'post',
            contentType: 'application/json',
            data: JSON.stringify(_dropRecord),
            processData: false,
            success: function(data, textStatus, jQxhr) {

                flag = data['result']

                travelTimeMS = data['travel_time'] * 60 * 1000
                var style = dropJobStyleDict[flag];

                console.log("single_job_drop_check result: ", data)

                var pointArrival = myChart.convertToPixel('grid', [_dropRecord.timeArrival, _dropRecord.categoryIndex]);
                var pointDeparture = myChart.convertToPixel('grid', [_dropRecord.timeDeparture, _dropRecord.categoryIndex]);

                var pointArrivalWithTravelTime = myChart.convertToPixel('grid', [_dropRecord.timeArrival - travelTimeMS, _dropRecord.categoryIndex]);
                var travelTime = pointArrival[0] - pointArrivalWithTravelTime[0]



                var barLength = pointDeparture[0] - pointArrival[0];
                var barHeight = Math.abs(
                    myChart.convertToPixel('grid', [0, 0])[1] - myChart.convertToPixel('grid', [0, 1])[1]
                ) * HEIGHT_RATIO;


                if (_dropShadow) {
                    myChart.getZr().remove(_dropShadow);
                    _dropShadow = null;
                }

                _dropShadow = new echarts.graphic.Group()

                jobRect = new echarts.graphic.Rect({
                    shape: { x: pointArrival[0], y: pointArrival[1] - barHeight + (barHeight / 2), width: barLength, height: barHeight },
                    style: style,
                    z: z
                });
                _dropShadow.add(jobRect)

                var travelLineStartY = pointArrival[1] + (barHeight * (-0));

                jobStartCircle = new echarts.graphic.Circle({
                    shape: {
                        cx: pointArrival[0] - travelTime,
                        cy: travelLineStartY,
                        r: barHeight / 3
                    },
                    style: style,
                    z: z
                });
                _dropShadow.add(jobStartCircle)

                jobStartLine = new echarts.graphic.Line({
                    shape: {
                        x1: pointArrival[0] - travelTime,
                        y1: travelLineStartY,
                        x2: pointArrival[0],
                        y2: travelLineStartY,
                    },
                    style: style,
                    z: z
                });
                _dropShadow.add(jobStartLine)

                console.log("single job result, query (", date_formatter_hhmm(_dropRecord.timeArrival), "), result: ", flag, "minutes:", data['travel_time'])

                var overallJobMessage = 'Error'; // '<font color="red">Error</font>';
                if (data['score'] == 1) {
                    overallJobMessage = 'OK'; // '<font color="green">OK</font>';
                } else {
                    overallJobMessage = 'Warning'; // '<font color="yellow">Warning</font>';
                }

                var messageTextArray = [
                    overallJobMessage + '|' + _dropRecord.workerCode + ` (start: ${date_formatter_hhmm(_dropRecord.timeArrival)}) }`,
                ]
                var messageText = ''
                var messageHead = '{' + flag + '|' + _dropRecord.workerCode + '-->'
                for (var i = 0; i < data['messages'].length; i++) {
                    messageText = messageText + ` \n (${data['messages'][i][0]}: ${data['messages'][i][1][0].message})`
                    messageTextArray.push(`(${data['messages'][i][0]}: ${data['messages'][i][1][0].message})`)
                }



                jobDropCheckResultText = new echarts.graphic.Text({
                    style: {
                        x: pointArrival[0] - 100,
                        y: travelLineStartY + 20,
                        text: messageHead + ` (start: ${date_formatter_hhmm(_dropRecord.timeArrival)}) } ${messageText} `, //messageTextArray.join('\n'),
                        //textVerticalAlign: 'bottom',
                        //textAlign: 'left',
                        //fill: '#FFFFFF',
                        //textFill: '#333', //rgba(255, 255, 255, 0.1)

                        rich: {
                            OK: {
                                fontSize: 12,
                                color: 'green'
                            },
                            Warning: {
                                fontSize: 12,
                                color: 'rgba(255, 193, 7, 1)'
                            },
                            Error: {
                                fontSize: 12,
                                color: 'red'
                            },
                        }
                    },
                    z: z
                });
                _dropShadow.add(jobDropCheckResultText)

                myChart.getZr().add(_dropShadow);
                /*
                myChart.setOption({
                    title: {
                        text: messageHead + ` (start: ${date_formatter_hhmm(_dropRecord.timeArrival)}) } ${messageText} `, //'0.3, Conflict',
                        //position: ''  {Warning| }
                        //https://github.com/apache/incubator-echarts/issues/8388

                        textStyle: {
                            //https://blog.csdn.net/zhaoxiang66/article/details/73574620
                            top: 0,
                            //color: '#e4393c', //京东红
                            //fontStyle: 'normal', //主标题文字字体风格，默认normal，有italic(斜体),oblique(斜体)
                            //fontWeight: "lighter", //可选normal(正常)，bold(加粗)，bolder(加粗)，lighter(变细)，100|200|300|400|500...
                            //fontSize: 12, //主题文字字体大小，默认为18px 

                            rich: {
                                OK: {
                                    fontSize: 12,
                                    color: 'green'
                                },
                                Warning: {
                                    fontSize: 12,
                                    color: 'rgba(255, 193, 7, 1)'
                                },
                                Error: {
                                    fontSize: 12,
                                    color: 'red'
                                },
                            }
                        }
                    }
                }); */

                //Manual throttling, wait x ms.
                setTimeout(function() {
                    _single_job_drop_check_ajay_lock = false
                }, 200);

            },
            error: function(jqXhr, textStatus, errorThrown) {
                console.log(errorThrown);
                _single_job_drop_check_ajay_lock = false
            }
        });

        //_dropShadow =  _dropShadow;
    }

    function prepareDrop() {
        // Check droppable place.
        var xPixel = _draggingEl.shape.x + _draggingEl.position[0];
        var yPixel = _draggingEl.shape.y + _draggingEl.position[1];
        var cursorData = myChart.convertFromPixel('grid', [xPixel, yPixel]);
        workerIndex = Math.floor(cursorData[1])

        if ((workerIndex >= global_loaded_data.workers_data.length) || (workerIndex < 0)) {
            console.log('Out of Workers Boundary!', workerIndex)
            return
        }

        currWorkerCode = global_loaded_data.workers_data[workerIndex][POS_WORKER_INDEX_worker_code]



        if (cursorData) {
            // Make drop shadow and _dropRecord
            _dropRecord = {
                categoryIndex: workerIndex,
                workerCode: currWorkerCode,
                timeArrival: cursorData[0],
                timeDeparture: cursorData[0] + _draggingTimeLength,
                travelMinutes: 0,
                jobCode: global_loaded_data.planned_jobs_data[_draggingRecord.dataIndex][POS_JOB_INDEX_job_code]
            };

            addOrUpdateDroppingJob();
        }
        // console.log('prepareDrop:', _draggingEl, _dropRecord, cursorData)
    }

    // Business logic to 
    function updateRawData() {

        //var flightData = ;
        //var movingItem = global_loaded_data.planned_jobs_data.pop(_draggingRecord.dataIndex);
        var movingItem = global_loaded_data.planned_jobs_data[_draggingRecord.dataIndex];

        // I simply drop it .
        movingItem[POS_JOB_INDEX_worker_index] = global_loaded_data.workers_data[_dropRecord.categoryIndex][0];
        movingItem[POS_JOB_INDEX_start_datetime] = _dropRecord.timeArrival;
        movingItem[POS_JOB_INDEX_end_datetime] = _dropRecord.timeDeparture;
        movingItem[POS_JOB_INDEX_changed_flag] = 1;

        global_job_dict[movingItem[POS_JOB_INDEX_job_code]]['node_item_style'] = node_itemStyle;

        //newIndex = global_loaded_data.planned_jobs_data.push(movingItem) - 1;
        //global_job_dict[movingItem[POS_JOB_INDEX_job_code]]['job_index'] = newIndex

        //global_loaded_data.planned_jobs_data.splice(_draggingRecord.dataIndex, 0, movingItem);


        myChart.setOption({
            series: {
                id: 'jobsSeries',
                data: global_loaded_data.planned_jobs_data
            }
        });
        return true;
    }

}

/*
{ title: "job_code" },
{ title: "job_type" },
{ title: "Requested Worker" },
{ title: "Start" },
{ title: "End" },
//{ title: "travel_minutes" },
{ title: "Longitude" },
{ title: "Latitude" },
{ title: "Action" },
*/

function convertUnplannedJob2Datatable(inputPlannedJob) {
    outputDatatable = []
    inputPlannedJob.forEach(function(job) {

        outputDatatable.push([
                job[POS_JOB_INDEX_job_code],
                job[POS_JOB_INDEX_job_type],
                job[POS_JOB_INDEX_worker_code],
                new Date(job[POS_JOB_INDEX_start_datetime]).toISOString().substr(5, 11).replace("T", " "),
                new Date(job[POS_JOB_INDEX_end_datetime]).toISOString().substr(5, 11).replace("T", " "),
                job[POS_JOB_INDEX_geo_longitude],
                job[POS_JOB_INDEX_geo_latitude],
            ])
            //job.splice(POS_INDEX_node_type, 0, VALUE_JOB_INDEX_node_type);
            //job[POS_JOB_INDEX_node_type] = VALUE_JOB_INDEX_node_type

    });
    return outputDatatable
}
// This is some business logic, don't care about it.
function addJobSelectedSlot(slot_i) {
    // console.log('selected.')
    // var newJobIndex = global_job_dict[ globalRecommendedSlotsData['jobCode']]['job_index'];
    var selectedSlot = globalRecommendedSlotsData['slots_data'][slot_i];
    // Check conflict  flightData.length
    // ['job_index']

    // const array = [2, 5, 9];

    // console.log(array);

    var newJobIndex = -1;
    var movedJob = [];


    for (var i = 0; i < global_loaded_data.not_planned_jobs_data.length; i++) {
        if (global_loaded_data.not_planned_jobs_data[i][3] == globalRecommendedSlotsData['jobCode']) {
            newJobIndex = i

            break
        }
    }
    if (newJobIndex > -1) {
        movedJob = global_loaded_data.not_planned_jobs_data[newJobIndex]
        global_loaded_data.not_planned_jobs_data.splice(newJobIndex, 1);
    } else {
        console.log('error, I lost my job. :( ')
        return
    }

    // array = [2, 9]
    // console.log(array); 


    movedJob[POS_JOB_INDEX_worker_index] = global_worker_dict[selectedSlot['scheduled_worker_code']]

    movedJob[POS_JOB_INDEX_worker_code] = selectedSlot['scheduled_worker_code']
    originalDuration = movedJob[POS_JOB_INDEX_end_datetime] - movedJob[POS_JOB_INDEX_start_datetime]
    movedJob[POS_JOB_INDEX_start_datetime] = selectedSlot['js_start_time']
    movedJob[POS_JOB_INDEX_end_datetime] = selectedSlot['js_start_time'] + originalDuration //(selectedSlot['scheduled_duration_minutes']*60*1000)
        // movedJob[POS_JOB_INDEX_job_type] = 'NEW_R_0_1_0_N'
    movedJob[POS_JOB_INDEX_changed_flag] = 1

    console.log(movedJob)

    node_itemStyle = getNodeItemStyle(movedJob) //[POS_JOB_INDEX_job_type], 0

    global_job_dict[movedJob[POS_JOB_INDEX_job_code]] = { data_latlng: [movedJob[POS_JOB_INDEX_geo_latitude], movedJob[POS_JOB_INDEX_geo_longitude]] }
    global_job_dict[movedJob[POS_JOB_INDEX_job_code]]['node_item_style'] = node_itemStyle

    global_loaded_data.planned_jobs_data.push(movedJob);
    myChart.setOption({
        series: {
            id: 'jobsSeries',
            data: global_loaded_data.planned_jobs_data
        }
    });

    datatable = window.job_datatable
    datatable.clear().draw();
    datatable.rows.add(convertUnplannedJob2Datatable(global_loaded_data.not_planned_jobs_data)); // Add new data
    datatable.columns.adjust().draw(); // Redraw the DataTable

    $('#newJobPlanModal').modal('hide')

    return true;
}



// ----------------------------------------------------
// --  Enable UI other than timeline
// ----------------------------------------------------



function download_as_image() {
    var img = ($('canvas')[0]).toDataURL('image/png')
    document.write('<img src="' + img + '"/>')
}

function changeGameListByPlanner() {
    var plannerCode = $('#planner_code').val()
    $('#game_code')
        .find('option')
        .remove()

    data = global_planner_game_list[plannerCode]
    for (var i = 0; i < data.length; i++) {
        //creates option tag
        jQuery('<option/>', {
            value: data[i],
            html: data[i]
        }).appendTo('#game_code'); //appends to select if parent div has id dropdown
    }


}


// ----------------------------------------------------
// -- Kandbox Time Utilities
// ----------------------------------------------------





function lpad(num, size) {
    var s = num + "";
    while (s.length < size) s = "0" + s;
    return s;
}

function date_formatter_hhmm(val) {
    //console.log("axis", new Date(val) )  
    var vdate = new Date(val)
    var texts = [lpad(vdate.getHours(), 2), lpad(vdate.getMinutes(), 2)]
    return texts.join(":")

}

function date_formatter_mmdd_hhmm(val) {
    //console.log("axis", new Date(val) ) 
    vdate = new Date(val)
    mmdd = [(vdate.getMonth() + 1), vdate.getDate()].join('-');
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