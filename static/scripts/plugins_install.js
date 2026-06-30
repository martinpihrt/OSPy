
jQuery(document).ready(function(){
    jQuery(".collapsible h4").click(function(event){
        jQuery(this).parent(".category").toggleClass("expanded").toggleClass("collapsed");
    });

    jQuery(".collapsible h4").first().parent(".category").toggleClass("expanded").toggleClass("collapsed");
    jQuery(".collapsible h5").click(function(event){
        jQuery(this).parent(".category").toggleClass("expanded").toggleClass("collapsed");
    });

    $(".collapsible a").click(function(e) { e.stopPropagation(); });

    jQuery(".plugin-install-form").submit(function(){
        var plugin = jQuery(this).data("plugin") || "";
        var repo = jQuery(this).data("repo") || "";
        var message = "Install or update plugin from this source?\n\n" + plugin + "\n" + repo;
        if (!confirm(message)) {
            return false;
        }
        jQuery(this).find("button[type='submit']").prop("disabled", true).text("Working...");
        return true;
    });

    jQuery(".plugin-custom-install-form").submit(function(){
        if (!confirm("Install uploaded custom ZIP plugin?")) {
            return false;
        }
        jQuery(this).find("button[type='submit']").prop("disabled", true).text("Working...");
        return true;
    });
});
