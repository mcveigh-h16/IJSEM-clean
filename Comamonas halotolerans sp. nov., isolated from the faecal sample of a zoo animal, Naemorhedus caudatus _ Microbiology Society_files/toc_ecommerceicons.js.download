$(document).ready(function() {
    // Display a single description...
    $(document).on("expanded", ".js-showhide", function(e) {
        
        var ahahUrl = $("#hiddenContext").text() + "/content/ahahbrowse",
        here = $(this).find('.js-plus'),
        target = "js-articleMetadataInner",
        itemid = here.closest(".js-browse-item").find(".js-access-determined, .js-access-in-the-process-of-being-determined").data("itemid"),
        title = "js-articleTitle";
        
        
        e.preventDefault();
        if (itemid) {
            // Pass in where we are first...
            ECApp.showDescription(this, target, ahahUrl, title);
        
            eventLogUrl = $("meta[name='stats-meta']").data("logstatisticsurl"); 
            eventData = {
                "eventType": "INVESTIGATION",
                "eventProperties.ITEM_ID": itemid,
                "eventProperties.SOURCE": "BROWSE",
            };
            $.ajax({
                url: eventLogUrl,
                type: "GET",
                data: eventData,
                success: function(resp, statusText) {
                },
                error: function(req, statusText, errorThrown) {
                }
           });
        }
    });
});
