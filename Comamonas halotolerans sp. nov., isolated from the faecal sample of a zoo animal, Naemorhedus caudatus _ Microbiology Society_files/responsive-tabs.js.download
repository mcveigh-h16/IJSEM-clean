$(document).ready(function() {
        //responsive tabs API code.
    
    var Tabs = {

          init: function() {
            this.bindUIfunctions();
            this.pageLoadCorrectTab();
          },

          bindUIfunctions: function() {

            // Delegation
            $(document)
              .on("click", ".js-transformer-tabs a[href^='#']:not('.active, .disabled')", function(event) {
                Tabs.changeTab(this.hash);
                event.preventDefault();
              })
              .on("click", ".js-transformer-tabs a.active, .js-transformer-tabs a.disabled", function(event) {
                //Tabs.toggleMobileMenu(event, this);
                event.preventDefault();
              })
             .on("click", ".js-textoptionsFulltext a.html:not('.disabled')", function(event) {      
                    //console.log("tab?" + this.hash);
                    event.preventBubble=true;
                     var anchorTab = Tabs.changeTab(this.hash);
                     anchorTab.trigger("click"); //trigger click event in this case it will be html fulltext.
                    //event.preventDefault();        
                }); 
                 //We also need to handle the back state by telling the browser to trigger the tab behaviour!   
            $(window).on('popstate', function(e) {
               anchor = $('[href="' + document.location.hash + '"]');
               if (anchor.length >  0) {
                   Tabs.displayTab(anchor);
               } else {
                  var defaultAnchor =  $('.js-transformer-tabs li.active a');
                  if (defaultAnchor) {
                      Tabs.displayTab(defaultAnchor)
                  }
               }
            });
          },

          changeTab: function(hash) {
             
            	var anchor = $(".js-transformer-tabs a[href='" + hash + "']");
            	var activeTab = anchor.find('span strong'); 
                Tabs.displayTab(anchor);
                
                //for mobile we want to hide all the tabs after  a tab.
                $(".js-dropdown li.tabIcon").hide();
                
                
                $(".js-mobile-tab").text($(activeTab).text());


            // update history stack adding additional history entries.
            // pushState is supported!
           history.pushState(null, null,  hash);

            // Close menu, in case mobile
            return anchor; // make property available outside the function

          },
          pageLoadCorrectTab: function() {
              //console.log("document.location.hash: " + document.location.hash);
            if   (document.location.hash.length > 0) {
                // If the page has a hash on load, go to that tab
                 var anchor = $(".js-transformer-tabs a[href='" + document.location.hash + "']");
                 if (!anchor.hasClass("disabled") && anchor.length > 0){
                     var anchorTab = this.changeTab(document.location.hash);
                     var divIDelement = $(document.location.hash);
                     
                  // this is a further amendment to allow the fulltext and 
                     //(any future event if its attached) to load when bookmarking a page with a particular tab. 
                     anchorTab.trigger("click");
                     
                     if (divIDelement.length) {
                         // 67 is a further offset to ensure the
                         // user can see the active tab that they have selected (not just its content)
                          ingentaCMSApp.goToHashAnchor(divIDelement, 67);
                     }
                 } else if ($(".js-transformer-tabs .active.tabIcon .active").length > 0) {
                     // go to which ever tab is defined as active in the HTML page and trigger a click on it 
                     // but, only when the hash id in the URL does not appear to exist in the page.
                     var activeTab = $(".js-transformer-tabs .active.tabIcon .active");  
                         activeTab.trigger("click"); //trigger click
                 }
              } else if ($(".js-transformer-tabs .active.tabIcon .active").length > 0) {
                  // go to which ever tab is defined as active in the JSP page and trigger a click on it 
                  // but, only when no hash in the url
                  var activeTab = $(".js-transformer-tabs .active.tabIcon .active");  
                      activeTab.trigger("click"); //trigger click
              }
          },
          displayTab: function(anchortab) {
                var url = anchortab.attr("href");
                   // console.log("url" + url);
                var divtabContent = $(url);
                
                // activate correct anchor (visually) both anchor link and its parent container 
                // should be marked with the css class active all other elements should not have this class
                anchortab.addClass("active").attr('aria-pressed','true')
                    .parent().addClass("active")
                    .siblings().removeClass("active")
                    .find("a").removeClass("active").attr('aria-pressed','false');
                
                
                // activate correct div (visually)
                divtabContent.addClass("active")
                	.siblings().removeClass("active");
                 
            }
          

    }

    Tabs.init();

    //end of responsive tabs API code.
    });


    $(".js-select").click(function(){
        $(this).closest('.js-transformer-tabs').find('.tabIcon').slideToggle();
    });
