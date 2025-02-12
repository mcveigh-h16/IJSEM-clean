$(document).ready(function(){

    $('.js-related-content-load').click(function()  {
    	var parentContainer = $(this).closest('li');
          
    	
    	    if (!$(this).hasClass('opened')) {
    	        $(this).addClass('opened');   
    	        
    	        returnRelatedContent(parentContainer);
    	    }
    });


    if ($('#js-recommend-load').length > 0) {
        function removeSidebarContainer() {
                //no recommended data returned remove the sidebar content from the DOM!
                $('#js-recommend-load').closest('.sidebar-pub2web-element').remove();
        }
        // pass optional function in. 
         returnRelatedContent($('#js-recommend-load'), removeSidebarContainer);
  
     
    }

});
   
   
function returnRelatedContent(parentContainer, noResultsReturnedFunctionToBeRun){
    
    
    var moreLikeThisContainer = parentContainer.find('.morelikethiscontainer');
    
     var morelikethisurl = $("#hiddenContext").text() + '/search/morelikethis';
     
     var pubrelatedcontentids = moreLikeThisContainer.children(".hiddenmorelikethisids").text();
     var webid = moreLikeThisContainer.children(".hiddenmorelikethiswebid").text();
     var fields = moreLikeThisContainer.children(".hiddenmorelikethisfields").text();
     var restrictions = moreLikeThisContainer.children(".hiddenmorelikethisrestrictions").text();
     var number = moreLikeThisContainer.children(".hiddenmorelikethisnumber").text();
     var numbershown = moreLikeThisContainer.children(".hiddenmorelikethisnumbershown").text();

     var data = {'pubrelatedcontentids': pubrelatedcontentids, 'webid': webid, 'fields': fields, 'restrictions': restrictions, 'number': number, 'numbershown': numbershown, 'fmt' : 'ahah'};
     
     
     if (fields && webid && number && numbershown){
        moreLikeThisContainer.append('<img id="loader" src="/images/jp/spinner.gif" alt="Loading" width="21">');
         $.post(morelikethisurl, data, function(resp) {
            moreLikeThisContainer.html(resp);

            ingentaCMSApp.displayElipsisDescription();

               moreLikeThisContainer.siblings(".tocitem").show();
               
            //inclusion of the class js-articleMetadata should give us a indication of data being returned!
            if (moreLikeThisContainer.find(".js-articleMetadata").length === 0 
                && noResultsReturnedFunctionToBeRun) {
                noResultsReturnedFunctionToBeRun();
            } 
     }); 
         
     }

}