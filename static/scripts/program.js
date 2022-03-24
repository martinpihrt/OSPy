
function check_repeat() {
    if (jQuery("#simple_repeat").prop('checked')) {
        jQuery(".repeat").show()
    } else {
        jQuery(".repeat").hide()
    }
}

function create_delay_selector(dayInterval, delayInterval) {
    jQuery("#intervalDelaySelector").html("");
    for (var i=0; i<dayInterval; i++) {
        jQuery("#intervalDelaySelector").append(
                jQuery("<span class='intervalSelect'>" + i + "</span>")
                    .on("click", intervalSelectClick)
                    .on("mouseover", intervalSelectMouseover)
                    .on("mouseout", intervalSelectMouseout)
        );
        if (i == 16) {
            jQuery("#intervalDelaySelector").append("<br/>");
        }
    }
    jQuery("#intervalDelaySelector .intervalSelect").each(function() {
        if (jQuery(this).text() == delayInterval) {
            jQuery(this).trigger("click");
        }
    });
}

function create_custom_schedule(dayInterval) {
    var sched = jQuery("#custom_schedule");
    sched.find("tr:not(:first-child)").remove();

    for (var i=0; i < dayInterval; i++) {
        var html = '<tr class="daySchedule ' + ((i%2)==0?'odd':'even') + '" id="custom_schedule' + i + '">';
        html += '<td class="station_name" style="border-right: solid">Day ' + (i+1) + ':</td>';
        for (var tick=0; tick < 24; tick++)
            html += '<td class="scheduleTick" data="' + tick + '"></td>';
        html += '</tr>';

        sched.append(jQuery(html));
    }

    sched.find("tr.daySchedule td.scheduleTick")
        .mousemove(addScheduleMouseover)
        .mouseout(addScheduleMouseout)
        .click(addScheduleClick);
    update_schedule("custom_schedule");
}

function update_schedules() {
    update_schedule("advanced_schedule");
    update_schedule("weekly_schedule");
    update_schedule("custom_schedule");
}

function deleteScheduleClick(e) {
    var info = jQuery(this).parent().attr("data").split(',');
    var name = info[0];
    var interval = [info[1], info[2]];

    var data = JSON.parse(jQuery("#" + name + "_data").val());
    var result = [];
    for (var i = 0; i < data.length; i++) {
        if (data[i][0] != interval[0] || data[i][1] != interval[1]) {
            result.push(data[i]);
        }
    }
    jQuery("#" + name + "_data").val(JSON.stringify(result));

    update_schedule(name);
    return false;
}

function update_schedule(name) {
    jQuery(".addStartMarker").remove();
    jQuery(".newStart").remove();
    jQuery(".addStopMarker").remove();
    var sched = jQuery("#" + name);
    var data = JSON.parse(jQuery("#" + name + "_data").val());

    sched.find("tr:not(:first-child)").find(".scheduleTick").html("");

    for (var i=0; i < data.length; i++) {
        var start = data[i][0];
        var end = data[i][1] - 1;

        var start_day = Math.floor(start / 1440);
        var start_hour = Math.floor((start % 1440) / 60);
        var start_min = start % 60;

        var end_day = Math.floor(end / 1440);
        var end_hour = Math.floor((end % 1440) / 60);
        var end_min = end % 60;

        for (var day=start_day; day <= end_day; day++) {
            for (var hour=start_hour; hour <= (day == end_day ? end_hour : 24); hour++) {
                if (hour == 24) { hour = 0; day++; }

                var slice_start = (day == start_day && hour == start_hour ? start_min : 0);
                var slice_end = (day == end_day && hour == end_hour ? end_min : 60);
                var el = sched.find("#" + name + day).find(".scheduleTick[data='" + hour + "']");

                var cross = (day == end_day && hour == end_hour ? jQuery('<div class="deleteProgram"></div>').click(deleteScheduleClick) : '');

                el.append(jQuery('<div class="existingProgram" style="left:'+(slice_start / .6)+'%;width:'+((slice_end-slice_start) / .6)+'%" data="'+name+','+data[i][0]+','+data[i][1]+'"></div>')
                        .append(cross));
            }
        }
    }
}


function pad(num, size) {
    var s = num+"";
    while (s.length < size) s = "0" + s;
    return s;
}
function x_to_min(x, width) {
    var max_steps = Math.max(1, width / 4);
    var step_options = [12, 6, 4, 2, 1];
    var steps = step_options.filter(function (x) {return x < max_steps})[0];
    return Math.min(steps-1, Math.floor(x / width * steps)) * Math.round(60/steps);
}

function addScheduleMouseover(e) {
    var hour = parseInt(jQuery(this).attr("data"));
    var x = e.pageX - this.offsetLeft;
    var width = jQuery(this).width();
    var minute = x_to_min(x, width);
    var left = x-30;

    jQuery(".newDetails").remove();
    if (jQuery(".newStart").length) {
        if (jQuery(".newStart").closest("tr").attr("id") == jQuery(this).closest("tr").attr("id")) {
            var marker = jQuery(".addStartMarker:first");
            var marker_width = e.pageX - marker.offset().left;
            marker.width(Math.max(0, marker_width));
            jQuery(".addStopMarker").remove();
            if (x >= 0 && x <= width && marker_width > 0) {
                jQuery(this).append('<span class="newDetails programStop" style="left: ' + left.toString() + 'px;">' + pad(hour, 2) + ':' + pad(minute, 2) + '</span>');
                jQuery(this).append('<div class="addStopMarker" style="left: '+ x.toString() +'px;"></div>');
                jQuery(this).children(".newDetails").mousemove(function(){ return false; });
                jQuery(this).children(".newDetails").mouseout(function(){ return false; });
            }
        }
    } else {
        jQuery(".addStartMarker").remove();
        if (x >= 0 && x <= width) {
            jQuery(this).append('<span class="newDetails programStart" style="left: ' + left.toString() + 'px;">' + pad(hour, 2) + ':' + pad(minute, 2) + '</span>');
            jQuery(this).append('<div class="addStartMarker" style="left: '+ x.toString() +'px;"></div>');
            jQuery(this).children(".newDetails").mousemove(function(){ return false; });
            jQuery(this).children(".newDetails").mouseout(function(){ return false; });
        }
    }

}
function addScheduleMouseout(e) {
    jQuery(this).children(".newDetails").remove();
}
function addScheduleClick(e) {
    var hour = parseInt(jQuery(this).attr("data"));
    var x = e.pageX - this.offsetLeft;
    var width = jQuery(this).width();
    var minute = x_to_min(x, width);
    var left = x-30;
    var start_el = jQuery(".newStart");

    jQuery(".newDetails").remove();
    if (start_el.length) {
        var current_row = jQuery(this).closest("tr");
        if (jQuery(".newStart").closest("tr").attr("id") == current_row.attr("id")) {
            var name = start_el.closest("table").attr("id");
            var day = parseInt(current_row.attr("id").replace(current_row.closest("table").attr("id"), ""));
            var start_parts = start_el.text().split(':');
            var start_min = day * 1440 + parseInt(start_parts[0]) * 60 + parseInt(start_parts[1]);
            var stop_min = day * 1440 + hour * 60 + minute;

            var data = JSON.parse(jQuery("#" + name + "_data").val());
            data.push([start_min, stop_min]);
            jQuery("#" + name + "_data").val(JSON.stringify(data));
            update_schedule(name);
        }
        jQuery(".addStartMarker").remove();
        start_el.remove();
        jQuery(".addStopMarker").remove();
    } else {
        jQuery(this).append('<span class="newStart programStart" style="left: ' + left.toString() + 'px;">' + pad(hour, 2) + ':' + pad(minute, 2) + '</span>');
        jQuery(this).append('<div class="addStartMarker" style="left: '+ x.toString() +'px;"></div>');
        jQuery(this).children(".newStart").mousemove(function(){ return false; });
        jQuery(this).children(".newStart").mouseout(function(){ return false; });
    }
}

function check_type() {
    var schedule_type = jQuery("#schedule_type").val();
    if (schedule_type == DAYS_SIMPLE || schedule_type == DAYS_ADVANCED) {
        jQuery("#days_controls").show()
    } else {
        jQuery("#days_controls").hide()
    }
    if (schedule_type == REPEAT_SIMPLE || schedule_type == REPEAT_ADVANCED || schedule_type == CUSTOM) {
        jQuery("#repeat_controls").show()
    } else {
        jQuery("#repeat_controls").hide()
    }
    if (schedule_type == REPEAT_SIMPLE || schedule_type == DAYS_SIMPLE) {
        jQuery("#simple_controls").show()
    } else {
        jQuery("#simple_controls").hide()
    }
    if (schedule_type == REPEAT_ADVANCED || schedule_type == DAYS_ADVANCED) {
        jQuery("#advanced_controls").show()
    } else {
        jQuery("#advanced_controls").hide()
    }
    if (schedule_type == WEEKLY_ADVANCED) {
        jQuery("#weekly_controls").show()
    } else {
        jQuery("#weekly_controls").hide()
    }
    if (schedule_type == CUSTOM) {
        jQuery("#custom_controls").show()
    } else {
        jQuery("#custom_controls").hide()
    }
    if (schedule_type == WEEKLY_WEATHER) {
        jQuery("#weather_controls").show()
        jQuery("#weather_pems").show()
        jQuery("#adjustment_controls").hide()
    } else {
        jQuery("#weather_controls").hide()
        jQuery("#weather_pems").hide()
        jQuery("#adjustment_controls").show()
    }
    jQuery(".addStartMarker, .newStart").remove();
}

function create_weather_schedule() {
    var pems = jQuery("#pemList tbody tr.pemEntry").map(function() {
        var day = parseInt(jQuery(this).find('.weather_pem_day').first().val());
        var hour = parseInt(jQuery(this).find('.weather_pem_hour').first().val());
        var min = parseInt(jQuery(this).find('.weather_pem_min').first().val());
        var prio = parseInt(jQuery(this).find('.weather_pem_prio').first().val());
        return [[day*1440+hour*60+min, prio]];
    }).get();
    jQuery("#weather_pems_data").val(JSON.stringify(pems));
}

jQuery(document).ready(function(){
    jQuery("#cSubmit").click(function() {
        jQuery("#programForm").submit();
    });
    jQuery("button#cCancel").click(function(){
        window.location="/programs";
    });
    jQuery("button.station.toggle").click(function(){
        var id = jQuery(this).attr("id");
        var state = jQuery(this).hasClass("on");
        jQuery(this)
            .addClass(state ? "off": "on")
            .removeClass(state ? "on" : "off");
        var stations = jQuery(".station.on").map(function() {
            return parseInt(jQuery(this).attr("id").replace("station", ""));
        }).get();
        jQuery("#stations").val(JSON.stringify(stations));
        return false;
    });
    jQuery("button.weekday.pushon").click(function(){
        var id = jQuery(this).attr("id");
        var state = jQuery(this).hasClass("on");
        jQuery(this)
            .addClass(state ? "off": "on")
            .removeClass(state ? "on" : "off");
        var days = jQuery(".weekday.on").map(function() {
            return parseInt(jQuery(this).attr("id").replace("day", ""));
        }).get();
        jQuery("#days").val(JSON.stringify(days));
        return false;
    });
    jQuery("#schedule_type").change(check_type);
    check_type();
    jQuery("#simple_repeat").change(check_repeat);
    check_repeat();

    jQuery("#intervalSelector").click(function() {
        var dayInterval = parseInt(jQuery("#intervalSelector .intervalSelect.distance0").text());
        var delayInterval = parseInt(jQuery("#intervalDelaySelector .intervalSelect.distance0").text());
        if (isNaN(delayInterval)) {
            delayInterval = 0;
        } else if (delayInterval >= 1 && delayInterval >= dayInterval) {
            delayInterval = dayInterval - 1;
        }
        create_delay_selector(dayInterval, delayInterval);
        create_custom_schedule(dayInterval);
        jQuery("#interval").val(jQuery("#intervalSelector .intervalSelect.distance0").text());
        jQuery("#interval_delay").val(jQuery("#intervalDelaySelector .intervalSelect.distance0").text());
    });
    jQuery("#intervalDelaySelector").click(function() {
        jQuery("#interval_delay").val(jQuery("#intervalDelaySelector .intervalSelect.distance0").text());
    });
    jQuery("#intervalSelector .intervalSelect").each(function() {
        var thisValue = parseInt(jQuery(this).text());
        if (thisValue == repeat_days) {
            jQuery(this).trigger("click");
            jQuery("#intervalSelector").trigger("click");
        }
    });
    jQuery("#intervalDelaySelector .intervalSelect").each(function() {
        var thisValue = parseInt(jQuery(this).text());
        if (thisValue == program_delay) {
            jQuery(this).trigger("click");
            jQuery("#intervalSelector").trigger("click");
        }
    });

    jQuery("tr.daySchedule td.scheduleTick")
            .mousemove(addScheduleMouseover)
            .mouseout(addScheduleMouseout)
            .click(addScheduleClick);

    jQuery("button#weather_pem_add").click(function(){
        jQuery("#pemList tbody tr:first").clone().attr('style', '').attr('class', 'pemEntry').appendTo("#pemList tbody");
        create_weather_schedule();
        return false;
    });

    jQuery('#pemList').on('click', '.weather_pem_delete', function(){
        jQuery(this).closest('tr').remove();
        create_weather_schedule();
        return false;
    });

    jQuery('#pemList').on('change', 'select,input', function(){
        create_weather_schedule();
    });
});