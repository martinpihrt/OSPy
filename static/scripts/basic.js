// Set up a live clock based on device time

function dateString(d) {
    var dateString = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][d.getDay()];
    dateString += " " + d.getDate() + " ";
    dateString += ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][d.getMonth()];
    return dateString;
}

function toXSDate(d) {
    var r = d.getFullYear() + "-" +
            (d.getMonth() < 9 ? "0" : "") + (d.getMonth()+1) + "-" +
            (d.getDate() < 10 ? "0" : "") + d.getDate();
    return r;
}

function toClock(duration, tf) {
    var h = Math.floor(duration/60);
    var m = Math.floor(duration - (h*60));
    if (tf == 0) {
        return (h>12 ? h-12 : h) + ":" + (m<10 ? "0" : "") + m + (h<12 ? "am" : "pm");
    } else {
        return (h<10 ? "0" : "") + h + ":" + (m<10 ? "0" : "") + m;
    }
}

function fromClock(clock) {
    var components = clock.split(":");
    var duration = 0;
    for (var c in components) {
        duration = duration*60 + parseInt(components[c], 10);
    }
    return duration;
}

function updateClock() {
    var now = new Date((new Date()).getTime() + to_device_time);
    if (timeFormat) {
        jQuery("#deviceTime span.hour").text((now.getHours() < 10 ? "0" : "") + now.getHours());
        jQuery("#deviceTime span.ampm").text("");
    } else {
        jQuery("#deviceTime span.hour").text(now.getHours()%12 == 0 ? "12" : now.getHours() % 12);
        jQuery("#deviceTime span.ampm").text((now.getHours() > 12 ? "pm" : "am"));
    }
    jQuery("#deviceTime span.minute").text((now.getMinutes() < 10 ? "0" : "") + now.getMinutes());
    jQuery("#deviceTime span.second").text(":" + (now.getSeconds() < 10 ? "0" : "") + now.getSeconds());

    jQuery("#deviceDate").text(dateString(now));

    setTimeout(updateClock, 500);
}

jQuery(document).ready(function(){

    jQuery("#bPlugins").click(function(e) {
        var btn = jQuery("#bPlugins");
        jQuery("#pluginMenu").css({
            position: 'absolute',
            top: btn.offset().top + btn.outerHeight() + 10,
            left: btn.offset().left
        }).slideToggle();
        e.stopPropagation();
    });
    jQuery(document).click(function(){
        jQuery("#pluginMenu").slideUp();
    });

    updateClock();
});
