
jQuery(document).ready(function(){

    jQuery("#cSubmit").click(function() {
        var hours = jQuery("input[id^='mm']").map(function() {
            return jQuery(this).attr("id");
        }).get();
        var minutes = jQuery("input[id^='ss']").map(function() {
            return jQuery(this).attr("id");
        }).get();
        for (var i = 0; i < hours.length; i++) {
            var hour = parseInt(jQuery('#' + hours[i]).val());
            var minute = parseInt(jQuery('#' + minutes[i]).val());
            hour = (isNaN(hour) ? 0 : hour);
            minute = (isNaN(minute) ? 0 : minute);
            if (hour < 0 || minute < 0 || minute > 59) {
                alert("All values should be positive and seconds should not exceed 59.");
                return false;
            }
            if (hour > 0 || minute > 0) anything = true;
        }
        jQuery("#runonceForm").submit();
    });

    jQuery("#cResetTime").click(function(){
        jQuery("input[type='number']").val(0);
    });

});