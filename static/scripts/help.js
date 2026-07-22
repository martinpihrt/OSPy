
function load_doc(e) {
    if(window.location.hash) {
        jQuery("#help_contents").load("/help?id=" + window.location.hash.substring(1));
    } else {
        jQuery("#help_contents").load("/help?id=1");
    }
}

jQuery(document).ready(load_doc);
jQuery(window).bind('hashchange', load_doc);

jQuery(document).ready(function() {
    jQuery('#helpPdfExport').on('click', function() {
        var articleId = window.location.hash ? window.location.hash.substring(1) : '1';
        if (!/^\d+$/.test(articleId)) articleId = '1';
        window.open('/help?pdf=' + encodeURIComponent(articleId), '_blank');
    });
});
