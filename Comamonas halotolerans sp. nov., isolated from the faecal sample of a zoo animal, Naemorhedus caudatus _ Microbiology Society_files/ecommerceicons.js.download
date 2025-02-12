var ECApp = ECApp || {
    stdTimeout: 60000,
    displayAccessIconsAjaxUrl: $("#hiddenContext").text() + "/content/ahahbrowse",
    /**
     * Displays the access icons ahead of the article name
     *  
     * @param {string} containerOuter   The outer containing class
     * @param {string} containerInner   The inner containing class
     * @param {string} target           The target class
     * @param {string} url              The url for the AHAH call
     * @param {string} title            The title class
     * @param {string} callback         An additional function to be executed upon AHAH success
     *  
     */ 
    displayAccessIcons: function() {
        
        var elementWhosAccessNeedsToBeDetermined = $('.js-access-to-be-determined'),
            uriList = "";
        
        if (elementWhosAccessNeedsToBeDetermined.length > 0){
            elementWhosAccessNeedsToBeDetermined.each(function( index ) {
                var eachElement = $(this),
                    accessIconAppendPoint = eachElement.closest('.js-accessIcons');
                
                if (!accessIconAppendPoint) {
                    console.log('append point for ' + eachElement.data('itemid') + 'not found!');
                }
                
                    uriList = uriList + (index > 0 ? ',':'') + eachElement.data('itemid');
                
                    eachElement.removeClass('js-access-to-be-determined').addClass('js-access-in-the-process-of-being-determined');
                    accessIconAppendPoint.prepend('<i class="fa fa-spinner fa-pulse fa-fw"></i>');
            });
            
     
            if (uriList) { 
                $.ajax({
                    url: ECApp.displayAccessIconsAjaxUrl,
                    timeout: ECApp.stdTimeout,
                    type: "POST",
                    data:   {'articleIds' : uriList,
                             'fmt' : 'ahah',
                             'ahahcontent' : 'toc' },
                    success: function(resp, statusText) {
                        var responseObj = $(resp);
                        elementWhosAccessNeedsToBeDetermined.each(function( index ) {
                            var eachElement = $(this),
                                eachItem = eachElement.data('itemid'),
                                responseItem = $(responseObj).children('a').eq(index),
                                responseObjImage = responseItem.children('.js-keyicon'),
                                responseItemURL = $.trim(responseItem.attr('href')),
                                accessIconAppendPoint = eachElement.closest('.js-accessIcons');
                            
                                //console.log('responseItemURL:' + responseItemURL );
                                //console.log('eachItem: ' + eachItem );
                                 //remove loader icon
                                accessIconAppendPoint.children('.fa-spinner').remove();
                                
                                //check itemid (uri) in response matches up with itemid in data attribute
                                if (responseItemURL == eachItem) {
                                    
                                    eachElement.removeClass('js-access-in-the-process-of-being-determined').addClass('js-access-determined');
                                    if ($.trim(responseItem.text()) != 'EMPTY') {
                                        accessIconAppendPoint.prepend(responseObjImage);
                                    }
                                    
                                } else {
                                    accessIconAppendPoint.children('.fa-spinner').remove();
                                    console.log('something went wrong the uri from the response item does not match the item data id!');
                                    console.log('responseItemURI:' + responseItemURL );
                                    console.log('pageItemURI: ' + eachItem );
                                }
                            
                        });
                    },
                    error: function(req, statusText) {
                        var cMsg = "showAllDescriptions() AHAH POST request failed due to: " + req.status + " (" + statusText + ")";
                        if (ingentaCMSApp.consoleOK) {console.warn(cMsg);}
                        $('.fa-spinner').remove();
                        elementWhosAccessNeedsToBeDetermined.removeClass('js-access-in-the-process-of-being-determined').addClass('js-access-determiniation-failed');
                    }
                });
            }
            
        } else {
           console.log('No items found in which access is needed to be determined.');     
        }
       
    },
    /**
     * Shows e-commerce and other details in the description
     *  
     * @param {obj}    here      Current location (this)
     * @param {string} container The containing class
     * @param {string} ahahurl   The url for the AHAH call
     * @param {string} title     The title class
     *
     */
    showDescription: function(here, container, ahahUrl, title) {
         //if (ingentaCMSApp.consoleOK) {console.info("showDescription() parameters:\n1. Here     : " + here + "\n2. Container: " + container + "\n3. AHAHUrl  : " + ahahUrl + "\n4. Title    : " + title);}
        var accessIcon,
            appendPoint,
            $currentLoc,
            deepDyveRequired,
            itemUrl,
            postdata,
            selectedObjContainer,
            signalClass,
            spinnerImageObj;

        $currentLoc = $(here);
        //$currentLoc.parent().find(".js-minus").show();
        //$currentLoc.hide();

        deepDyveRequired = true;
        signalClass = "descriptionOpened";
        selectedObjContainer = $currentLoc.closest("." + container);
        accessIcon = selectedObjContainer.siblings(".js-accessIcons").find("span");

        // Check for a key icon...
        if (accessIcon.hasClass("keyicon")) {
            deepDyveRequired = false;
        }

        // we dont need to do this there should alredy be a function that does this.
        // $(selectedObjContainer).find(".js-description").slideDown();

        // Append and test for a class to determine if items description has already been opened notice the NOT
        if (!$(selectedObjContainer).hasClass(signalClass)) {
            $(selectedObjContainer).addClass(signalClass);

            // First things first lets get the URI of the Item (we can get this from the URL of the search listing title)
            itemUrl = $(selectedObjContainer).find("." + title).children("a").attr("href");
            
             //remove any parameter added to the URL hash and params we just want the webId
             if (itemUrl.indexOf('?') != -1){
                itemUrl = itemUrl.substring(0, itemUrl.indexOf('?'));
            }
            if (itemUrl.indexOf('#') != -1){
               itemUrl = itemUrl.substring(0, itemUrl.indexOf('#'));
            }
             
          

            // Let's now define the point in which the fulltext / price should be appended into the HTML
            appendPoint = $(selectedObjContainer).find(".description").children(".extraitems");

            // Let's append a temp spinner image while we wait on the ahah response
            // We only wish to append once before load
            if (appendPoint.not(".loading-fulltextorprice").length) {
                appendPoint.prepend('<img src="/images/admin/spinner.gif" alt="" class="loading-fulltextorprice" style="float:left;" />');
            }
            spinnerImageObj = appendPoint.children("img.loading-fulltextorprice");

            // We now need to create the data for the AHAH page
            postdata = {
                fmt: "ahah",
                ahahcontent: "itemaccess",
                ahahitem: itemUrl
            };
            
            // OK this is where the fun begins now we add Ajax
            if (itemUrl) {
                $.ajax({
                    url: ahahUrl,
                    data: postdata,
                    timeout: ECApp.stdTimeout,
                    type: "POST",
                    success: function(resp, statusText) {
                        // We just need to append the response and remove the spinner image
                        spinnerImageObj.remove();
                        appendPoint.prepend(resp);
                        ingentaCMSApp.addPdfMessageLogging(appendPoint);
                        ingentaCMSApp.appendCSRFHiddenToken();
                     /*   if (deepDyveRequired) {
                            var deepDyveInsertion = $(appendPoint).find(".deepdyve");
                            if ((deepDyveInsertion.length > 0) ) {
                               // ingentaCMSApp.insertDeepDyveLink("button", deepDyveInsertion);
                            }
                        }*/
                    },
                    error: function(req, statusText) {
                        var cMsg = "showDescription() AHAH POST request failed due to: " + req.status + " (" + req.statusText + ")";
                        spinnerImageObj.remove();
                        if (ingentaCMSApp.consoleOK) {console.warn(cMsg);}
                    },
                    complete: function(req, statusText) {
                        spinnerImageObj.remove();
                    }
                });
            }
        }
    },
    /**
     * Shows e-commerce and other details in all the descriptions
     *  
     * @param {string} containerOuter   The outer containing class
     * @param {string} containerInner   The inner containing class
     * @param {string} ahahurl          The url for the AHAH call
     * @param {string} title            The title class
     *
     */
    showAllDescriptions: function(containerOuter, containerInner, ahahUrl) {
        // if (ingentaCMSApp.consoleOK) {console.info("showAllDescriptions() parameters:\n1. Outer Container: " + containerOuter + "\n2. Inner container: " + containerInner + "\n3. AHAHUrl  : " + ahahUrl);}
        var itemList,
            postdata,
            postSelector,
            resultItemHeadingContainer,
            signalClass,
            target;

        // Construct a jQuery selector...
        if (containerOuter) {
            itemList = $("." + containerOuter + " ." + containerInner);
            postSelector = "." + containerOuter + " ";
        } else {
            itemList = $("." + containerInner + " ");
            postSelector = "";
        }
        
        signalClass = "descriptionOpened";
        
        // Toggle all individual SHOW/HIDE...
        itemList.find(".showhide").find("span.plus").hide();
        itemList.find(".showhide").find("span.minus").show();
        
        // Slide down all descriptions...
        itemList.find(".description").slideDown();

        target = itemList.find(".itemDescription").not("." + signalClass).find(".description").find(".extraitems");
     
        // Add a spinner to indicate more work...
        if (!target.hasClass("spinner")) {
            target.addClass("spinner");
            target.prepend('<img src="/images/admin/spinner.gif" alt="loading" class="loading-fulltextorprice" style="float:left;" />');
        }
        
        // Grab the ids
        postdata = $(postSelector + "form.ahahTocArticles").serialize();
        
        // Now update as needed...
        postdata = postdata.replace("ahahcontent=toc", "ahahcontent=allitemaccess");
        
        if (postdata) {
            $.ajax({
                url: ahahUrl,
                timeout: ECApp.stdTimeout,
                type: "POST",
                data: postdata,
                success: function(resp, statusText) {
                    var appendPoint,
                        currDesc,
                        currIcon,
                        currItem,
                        here;
                    // Loop through the response
                    $(".fulltextandtools", resp).each(function(index) {
                    	var seeMoreIndex = 0;
                    	if ($(".search-results-options-container .showAllDescriptions").css("display") == 'none') {
                    		seeMoreIndex = parseInt($("#currentPageNum").val() - 1) * parseInt($("#defaultPageSize").val());
                    	}
                        here = $(this);
                        currItem = itemList.eq(seeMoreIndex + index);
                        currDesc = currItem.find(".itemDescription");
                        currIcon = currItem.find(".js-accessIcons").find("span");
                        appendPoint = currItem.find(".description").find(".extraitems");
                        if (!currDesc.hasClass(signalClass)) {
                            currDesc.addClass(signalClass);
                            // We just need to append the response and remove the spinner image
                            appendPoint.find("img.loading-fulltextorprice").remove();
                            appendPoint.append(here);
                            ingentaCMSApp.addPdfMessageLogging(appendPoint);
                            ingentaCMSApp.appendCSRFHiddenToken();
                            // DeepDyve only needed if not otherwise available...
                           if (!currIcon.hasClass("keyicon")) {
                   
                            }
                        } else {
                            appendPoint.find("img.loading-fulltextorprice").remove();
                        }
                        
                    });
                },
                error: function(req, statusText) {
                    var cMsg = "showAllDescriptions() AHAH POST request failed due to: " + req.status + " (" + statusText + ")";
                    itemList.find("img.loading-fulltextorprice").remove();
                    if (ingentaCMSApp.consoleOK) {console.warn(cMsg);}
                }
            });
        }
    }
};

$(document).ready(function() {
    //run on load if there is anything that needs checking!
    if ($('.js-access-to-be-determined').length > 0){
        ECApp.displayAccessIcons();
        }
    
    $(document).ajaxSuccess(function( event, xhr, settings ) {
        if ($('.js-access-to-be-determined').length > 0){
            ECApp.displayAccessIcons();
        }
        
    });
   //call on page load this is now needed for e-commerce
    ingentaCMSApp.appendCSRFHiddenToken();

    $(".showDescriptions").click(function(e) {
        var $this = $(this);
        e.preventDefault();
        $this.next(".hideDescriptions").removeClass("inactive");
        $this.addClass("inactive");
        $(".resultItem .plus").each(function(index) {
            $(this).trigger("click");
        });
    });

    $(".hideDescriptions").click(function(e) {
        var $this = $(this);
        e.preventDefault();
        $this.prev(".showDescriptions").removeClass("inactive");
        $this.addClass("inactive");
        $(".resultItem .minus").trigger("click");
    });
    
});
