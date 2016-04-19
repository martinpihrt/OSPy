
jQuery(document).ready(function(){

    jQuery("button#tooltips").click(function(){
        var visible = jQuery(this).text() == "Hide Tooltips";
        jQuery(this).text(visible ? "Show Tooltips" : "Hide Tooltips");
        jQuery(".tooltip").toggle();
    });

    jQuery("#cSubmit").click(function() {
        jQuery("#optionsForm").submit();
    });

     jQuery("#cUpload").click(function() {
        jQuery("#uploadForm").submit();
    });

    jQuery(".collapsible h4").click(function(event){
        jQuery(this).parent(".category").toggleClass("expanded").toggleClass("collapsed");
    });

         
    switch (errorCode) {
        case "pw_wrong":
            jQuery("#erroropw").text("The password given was incorrect.");
            jQuery("#erroropw").parents(".collapsible").toggleClass("expanded").toggleClass("collapsed");
            break;
        case "pw_blank":
            jQuery("#errornpw").text("Please enter a password.");
            jQuery("#errornpw").parents(".collapsible").toggleClass("expanded").toggleClass("collapsed");
            break;
        case "pw_mismatch":
            jQuery("#errorcpw").text("Passwords done't match, please re-enter.");
            jQuery("#errorcpw").parents(".collapsible").toggleClass("expanded").toggleClass("collapsed");
            break;
    }

    jQuery(".collapsible h4").first().parent(".category").toggleClass("expanded").toggleClass("collapsed");

});
