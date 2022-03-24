// Global vars
var displayScheduleDate = new Date(device_time); // dk
var displayScheduleTimeout;
var graph_text;

function displaySchedule(schedule) {
    if (displayScheduleTimeout != null) {
        clearTimeout(displayScheduleTimeout);
    }
    var now = new Date((new Date()).getTime() + to_device_time);
    var nowMark = now.getHours()*60 + now.getMinutes();
    var isToday = toXSDate(displayScheduleDate) == toXSDate(now);
    var programClassesUsed = {};
    jQuery(".stationSchedule .scheduleTick").each(function() {
        jQuery(this).empty();
        var sid = jQuery(this).parent().attr("data");
        var slice = parseInt(jQuery(this).attr("data"))*60;
        var boxes = jQuery("<div class='scheduleMarkerContainer'></div>");
        for (var s in schedule) {
            if (schedule[s].station == parseInt(sid, 10)) {
                if (!(isToday && schedule[s].date == undefined && schedule[s].start + schedule[s].duration/60 < nowMark)) {
                    var relativeStart = schedule[s].start - slice;
                    var relativeEnd = schedule[s].start + schedule[s].duration/60 - slice;
                    if (0 <= relativeStart && relativeStart < 60 ||
                        0.05 < relativeEnd && relativeEnd <= 60 ||
                        relativeStart < 0 && relativeEnd >= 60) {
                        var barStart = Math.max(0,relativeStart)/60;
                        var barWidth = Math.max(0.05,Math.min(relativeEnd, 60)/60 - barStart);
                        var programClass;
                        if (schedule[s].manual) {
                            programClass = "programManual";
                        } else {
							programClass = "program" + (parseInt(schedule[s].program)+1)%10;
                        }
                        programClassesUsed[schedule[s].program_name] = programClass;
                        var markerClass = (schedule[s].active == null ? "schedule" : "history");
                        if (schedule[s].blocked) {
                            markerClass = 'blocked'
                        }
                        boxes.append("<div class='scheduleMarker " + programClass + " " + markerClass + "' style='left:" + barStart*100 + "%;width:" + barWidth*100 + "%' data='" + schedule[s].program_name + ": " + schedule[s].label + "'></div>");
                    }
                }
            }
        }
        if (isToday && slice <= nowMark && nowMark < slice+60) {
            var stationOn = jQuery(this).parent().children(".stationStatus").hasClass("station_on");
            boxes.append("<div class='nowMarker" + (stationOn?" on":"")+ "' style='width:2px;left:"+ (nowMark-slice)/60*100 + "%;'>");
        }
        if (boxes.children().length > 0) {
            jQuery(this).append(boxes);
        }
    });
    jQuery("#legend").empty();
    for (var p in programClassesUsed) {
        jQuery("#legend").append("<span class='" + programClassesUsed[p] + "'>" + p + "</span>");
    }
    jQuery(".scheduleMarker").mouseover(scheduleMarkerMouseover);
    jQuery(".scheduleMarker").mouseout(scheduleMarkerMouseout);

    jQuery("#displayScheduleDate").text(dateString(displayScheduleDate) + (displayScheduleDate.getFullYear() == now.getFullYear() ? "" : ", " + displayScheduleDate.getFullYear()));
    if (isToday) {
        displayScheduleTimeout = setTimeout(displayProgram, 60*1000);  // every minute
    }
}

function displayProgram() {
    var visibleDate = toXSDate(displayScheduleDate);
    jQuery.getJSON("/log.json?date=" + visibleDate, function(log) {
        for (var l in log) {
            log[l].duration = fromClock(log[l].duration);
            log[l].start = fromClock(log[l].start)/60;
            if (log[l].date != visibleDate) {
                log[l].start -= 24*60;
            }
            if (log[l].blocked) {
                log[l].label = toClock(log[l].start, timeFormat) + " (blocked by " + log[l].blocked + ")";
            } else {
                log[l].label = toClock(log[l].start, timeFormat) + " for " + toClock(log[l].duration, 1);
            }
        }
        displaySchedule(log);
    })
}

function scheduleMarkerMouseover() {
    var description = jQuery(this).attr("data");
    var markerClass = jQuery(this).attr("class");
    markerClass = markerClass.substring(markerClass.indexOf("program"));
    markerClass = markerClass.substring(0,markerClass.indexOf(" "));
    jQuery(this).append('<span class="showDetails ' + markerClass + '">' + description + '</span>');
    jQuery(this).children(".showDetails").mouseover(function(){ return false; });
    jQuery(this).children(".showDetails").mouseout(function(){ return false; });
}
function scheduleMarkerMouseout() {
    jQuery(this).children(".showDetails").remove();
}

function updateStatus(status) {
    var display, updateInterval = 30000;
    for (var s=0; s<status.length; s++) {
        var station = status[s];
        var classes = "stationStatus station_" + station.status;
        switch (station.reason) {
            case "program" :
                var minutes = Math.floor(station.remaining/60);
                var seconds = Math.floor(station.remaining - 60*minutes);
                if (minutes < 10) {minutes = "0"+minutes;}
                if (seconds < 10) {seconds = "0"+seconds;}
                if (station.status == "on") {
                    display = minutes+":"+seconds;
                }
                updateInterval = 1000;
                break;
            case "master" :
                classes += " master";
                if (station.status == "on") {
                    display = "Master On";
                } else {
                    display = "Master Off";
                    classes += " strike";
                }
                break;
            case "rain_delay" :
                display = "Rain Delay";
                break;
            case "rain_sensed" :
                display = "Rain Sensor";
                break;
            case "system_off" :
                display = "Disabled";
                break;
            default:
                display = station.status;
        }
        jQuery("td#status" + station.station)
            .text(display)
            .removeClass()
            .addClass(classes);
    }
    setTimeout(statusTimer, updateInterval);
}

function statusTimer() {
    jQuery.getJSON("/status.json", updateStatus)
}

function water_level_prompt(current){
    if (current != 1.0) {
        var w = 100;
    } else {
        var w = prompt("Enter adjustment (%)", current*100);
    }
    if (w != null) {
        window.location="/action?level_adjustment=" + w;
    }
}

function rain_delay_prompt(current){
    if (current != 0) {
        var h = 0;
    } else {
        var h = prompt("Enter hours to delay", "0");
    }
    if (h != null) {
        window.location="/action?rain_block=" + h;
    }
}

function countdownTimer(timerId) {
    var timerElement = jQuery("#" + timerId);
    var remaining = parseFloat(timerElement.attr("data"));
    timerElement.attr("data", remaining - 1)
    var rHours = Math.floor(remaining/3600);
    var rMinutes = Math.floor((remaining%3600)/60);
    var rSeconds = Math.floor(remaining%60);
    timerElement.text((rHours<10 ? "0" : "") + rHours + ":" + (rMinutes<10 ? "0" : "") + rMinutes + ":" + (rSeconds<10 ? "0" : "") + rSeconds);
    if (rHours <=0 && rMinutes <=0 && rSeconds <=0) {
        setTimeout("location.reload()", 1000);
    } else {
        setTimeout("countdownTimer('" + timerId + "')", 1000);
    }
}

function draw_graph(result) {
    var data = [];
    graph_text = [];
    var legend_items = jQuery('#legend-visible').find('.legendColorBox');

    for (var i = 0; i < result.length; i++) {
        var balances = [];
        var texts = [];
        var txt_header = "<table class=\"balanceList\"><tr><th>Reason</th><th>(mm)</th></tr>";
        var txt_body = "";
        var txt_footer = "</table>";
        for (timestamp in result[i]['balances']) {
            var balance = result[i]['balances'][timestamp];
            balances.push([1000*parseInt(timestamp), balance['total']]);
            txt_body += "<tr><td>ETo</td><td class=\"balValue\">-" + balance['eto'].toFixed(1) + "</td></tr>";
            txt_body += "<tr><td>Rain</td><td class=\"balValue\">+" + balance['rain'].toFixed(1) + "</td></tr>";

            for (var j = 0; j < balance['intervals'].length; j++) {
                var interval = balance['intervals'][j]
                txt_body += "<tr><td>" + interval['program_name'] + "</td><td class=\"balValue\">+" + interval['irrigation'].toFixed(1) + "</td></tr>";
            }

            txt_body += "<tr><th>Total</th><th class=\"balValue\">" + balance['total'].toFixed(1) + "</th></tr>";
            texts.push(result[i]['station'] + " @ " + toXSDate(new Date(1000*parseInt(timestamp))) + "<br>" + txt_header + txt_body + txt_footer);

            txt_body = "<tr><td>Previous</td><td class=\"balValue\">" + balance['total'].toFixed(1) + "</td></tr>";
        }

        if (i >= legend_items.length || legend_items.eq(i).children().children().attr("data") == 1)
        {
            data.push({
                data: balances,
                label: result[i]['station'],
                color: i
            })
            graph_text.push(texts);
        }
    }

    return jQuery.plot("#graph-placeholder", data, {
        series: {
            lines: {
                show: true
            },
            points: {
                show: true
            }
        },
        grid: {
            hoverable: true
        },
        xaxis: {
            mode: "time",
            timeformat: "%Y-%m-%d"
        },
        legend: {
            show: true,
            container: jQuery("#legend-placeholder")
        },
        axisLabels: {
            show: true
        },
        yaxes: [{
            position: 'left',
            axisLabel: 'Water balance (mm)'
        }]
    });
}

function create_graph(result) {
    plot = draw_graph(result);

    jQuery('#legend-visible').html(jQuery('#legend-placeholder').html());
    plot.resize();
    plot.setupGrid();
    plot.draw();

    jQuery('#legend-visible').find('.legendColorBox').children().children().css({
        color: "#ddd"
    }).attr("data", 1);

    jQuery('#legend-visible').on('click', 'tr', function(){
        var colorbox = jQuery(this).find('.legendColorBox').children().children();
        colorbox.css({
            "border-color": colorbox.css("color"),
            "color": colorbox.css("border-left-color")
        });
        colorbox.attr("data", 1 - colorbox.attr("data"));
        draw_graph(result);
    });

    jQuery("<div id='tooltip'></div>").css({
        position: "absolute",
        display: "none",
        "min-width": "120px",
        "background-color": "#eee",
        padding: "5px",
        "border-radius": "5px"
    }).appendTo("body");

    jQuery("#graph-placeholder").bind("plothover", function (event, pos, item) {
        if (item) {
            jQuery("#tooltip").html(graph_text[item.seriesIndex][item.dataIndex]);
            var x = item.pageX+5;
            if (item.pageX + jQuery("#tooltip").width() > jQuery(document).width() - 100)
            {
                x = item.pageX-jQuery("#tooltip").width()-10;
            }
            var y = item.pageY+5;
            if (item.pageY + jQuery("#tooltip").height() > jQuery(document).height() - 20)
            {
                y = item.pageY-jQuery("#tooltip").height()-10;
            }
            jQuery("#tooltip").css({top: y, left: x}).fadeIn(200);
        } else {
            jQuery("#tooltip").hide();
        }
    });
}

jQuery(document).ready(function(){
    if (manual_mode) {
        jQuery("button.manual").click(function () {
            sid = parseInt(jQuery(this).attr("id"));
            sbit = jQuery(this).hasClass("on");
            if (sbit) {
                window.location = "/action?sid="+(sid+1)+"&set_to=0"; // turn off station
            } else {
                var strmm = jQuery("#mm"+sid).val();
                var strss = jQuery("#ss"+sid).val();
                var mm = (strmm == "" ? 0 : parseInt(strmm));
                var ss = (strss == "" ? 0 : parseInt(strss));
                if (!(mm >= 0 && ss >= 0 && ss < 60)) {
                    alert("Timer values wrong: " + strmm + ":" + strss);
                    return;
                }
                window.location = "/action?sid=" + (sid+1) + "&set_to=1" + "&set_time=" + (mm*60+ss);  // turn it off with timer
            }
        });
    } else {
        displayProgram()
        setTimeout(statusTimer, 1000);

        jQuery(".button#pPrev").click(function() {
            displayScheduleDate.setDate(displayScheduleDate.getDate() - 1);
            displayProgram();
        });
        jQuery(".button#pToday").click(function() {
            var day = new Date()//dk
            displayScheduleDate.setDate(day.getDate());
            displayScheduleDate.setMonth(day.getMonth()); //dk
            displayProgram();
        });
        jQuery(".button#pNext").click(function() {
            displayScheduleDate.setDate(displayScheduleDate.getDate() + 1);
            displayProgram();
        });
    }

    jQuery(".countdown").each(function() {
        countdownTimer(jQuery(this).attr('id'));
    });
    if (jQuery("#graph-placeholder").length > 0) {
        setTimeout(function() {jQuery.getJSON("/balance.json", create_graph)}, 500);
    }
});