

ingentaCMSApp.displayGraphOrTable = function($dataTable, graphType, graphId, graphTitle, eMsg) {
        var lineData = this.extractDataFromTable($dataTable);
        try {
            this.plotGraph(graphType, graphId, lineData);
        } catch (e) {
            if (this.consoleOK) {console.log(graphId + " failed with: " + e.message);}
            this.displayTabularMetrics(graphTitle, graphId, eMsg);
        }
    };
    /**
     * Extracts data from the table of data
     *
     * @param {jQuery object} table     Table containing relevant data
     */
ingentaCMSApp.extractDataFromTable = function(table) {
        var lineData = [];
        table.find("tbody tr").each(function(index) {
            var $row = $(this),
                rowData = [];
            
            // APPEND the individual pieces of data
            var datePart = $row.find(":nth-child(1)").text();
            datePart = datePart.substr(0, datePart.indexOf(' '));

            rowData.push(datePart);
            rowData.push(+$row.find(":nth-child(2)").text());
            // PREPEND each set of data...
            lineData.unshift(rowData);
        });
        return lineData;
    };
ingentaCMSApp.pendingPlots = [];
    /**
     * Plots graphs for metrics (pie and line only)
     *
     * @param {string} gtype graph type: pie|other (actually 'line')
     * @param {string} target id to which to attach output
     * @param {object} data data to graph
     */
ingentaCMSApp.plotGraph = function(gType, target, data) {
        function canvasSupported() {
            var canvas = document.createElement('canvas');
            return (canvas.getContext && canvas.getContext('2d'));
        }
        // Because of crossmark we have to look in both places
        if ($ != jQuery) {
            jQuery = $;
        }
        if (typeof $.jqplot === "undefined") {
            ingentaCMSApp.pendingPlots.push({
                "gType": gType,
                "target": target,
                "data": data});
            if (ingentaCMSApp.pendingPlots.length == 1) {
                var url = canvasSupported() ? 
                            "/js/" + ingentaCMSApp.instanceprefix + "/jquery.jqplot." + ingentaCMSApp.instanceprefix +".js" 
                            : "/js/" + ingentaCMSApp.instanceprefix + "/jquery.jqplot." + ingentaCMSApp.instanceprefix + ".ie8.js";
                $.ajax({
                    dataType: "script",
                    cache: true,
                    url: url,
                    success: function () {
                        for (var i = 0 ; i < ingentaCMSApp.pendingPlots.length ; i++) {
                            ingentaCMSApp.plotGraphWithJqplot($.jqplot, ingentaCMSApp.pendingPlots[i].gType, ingentaCMSApp.pendingPlots[i].target, ingentaCMSApp.pendingPlots[i].data);
                           
                        }
                        
                        
                    }
                });
            }
        } else {
            ingentaCMSApp.plotGraphWithJqplot($.jqplot, gType, target, data);
        }
    };
    /**
     * Plots graphs with jqplot for metrics (pie and line only)
     *
     * @param {object} jqplot itself
     * @param {string} gtype graph type: line|pie
     * @param {string} target id to which to attach output
     * @param {object} data data to graph
     */
    ingentaCMSApp.plotGraphWithJqplot = function(jqplot, gType, target, data) {
        var pieLabels = [],
            seriesColours = ["#1a6594", "#f0bd68", "#d6caa5"],
            total = 0,
            PLOT_MSG1 = "Unable to plot metrics: no HTML target given...";
        
        var plotOptions = function() { return {}; };
        switch (gType) {
        case "pie":
            total = 0;
            $(data).map(function() {
                total += this[1];
            });
            pieLabels = $.makeArray($(data).map(function() {
                return this[0] + " (" + Math.round((this[1] * 100) / total) + "%)";
            }));

            plotOptions = function() { return {
                // Define colours to use...
                seriesColors: seriesColours,
                // Define various overall defaults
                seriesDefaults: {
                    renderer: jqplot.PieRenderer,
                    rendererOptions: {
                        dataLabels: pieLabels,
                        dataLabelPositionFactor: 0.75,
                        highlightMouseDown: false,
                        highlightMouseOver: false,
                        showDataLabels: true,
                        sliceMargin: 10
                    }
                }
            };};
            break;
             default:
                 // OK this is to get the max date we only want to plot up to the maximum date 
                 // since the data array is not ordered chronologically we have to do some Javascript work ....
                 var dateArray = [];
                 var newData = [];
                 data.forEach( function(d) { 
                     var datePart = d[0];
                     dateArray.push(new Date(datePart));
                   
                 });
              // For a single point graph place in centrally
                 if (dateArray.length == 1) {
                    var date = dateArray[0];
                    var newLow = new Date(date.getMonth() == 0 ? (date.getFullYear() - 1) + "-12-01" : date.getFullYear() + "-" + (date.getMonth() > 10 ? date.getMonth() : "0" + date.getMonth()) + "-01");
                    var newHigh = new Date(date.getMonth() == 11 ? (date.getFullYear() + 1) + "-01-01" : date.getFullYear() + "-" + (date.getMonth() > 8 ? (date.getMonth() + 2) : "0" + (date.getMonth() + 2)) + "-01");
                    dateArray.push(newHigh);
                    dateArray.unshift(newLow);
                 }
                 
                 var maxDate=new Date(Math.max.apply(null,dateArray));
                 var minDate=new Date(Math.min.apply(null,dateArray));
                 
                 var tickInterval = function() {
                     var w = $("#" + target).width();
                     var l = dateArray.length;
                     var i = 1;
                     // This 13 is just based on observation - no science
                     while (l > 0 && (w/l) < 13) {
                        i *= 2;
                        w *= 2;
                     }
                     return i + ' month';
                  };
              
                 
            plotOptions = function() { return {
                // Define colours to use...
                seriesColors: seriesColours,
                // Define various other overall defaults
                seriesDefaults: {
                    shadow: false,
                    showMarker: true
                },
                // Define the defaults for both axes
                axesDefaults: {
                    tickRenderer: $.jqplot.CanvasAxisTickRenderer,
                    tickOptions: {
                        fontSize: "10pt"
                    }
                },
                // Define specific properties for the X axis
                axes: {
                    xaxis: {
                        renderer: jqplot.DateAxisRenderer,
                        pad: 0,
                        min: minDate,
                        max: maxDate,
                        tickOptions: {
                            angle: -90,
                            formatString: "%b - %Y  "
                        },
                        tickInterval:tickInterval()
                    },
                    yaxis: {
                        min: 0,
                        tickOptions: {
                            formatString: "%7d  "
                        }
                    }
                },
                highlighter: {
                    show: true,
                    sizeAdjust: 10
                },
                cursor: {
                    show: false
                }
            };};
            break;
        }
        if (target) {
            var plot = jqplot(target, [data], plotOptions());
            
            $(window).resize(function() {
                plot.replot( plotOptions() );
                });
        } else {
            alert(PLOT_MSG1);
        }
    };
    /**
     * Display metrics data as a table (normally following a failure with plotting)
     *
     * @param {string}  tableName
     * @param {string}  graphName
     * @param {string}  eMsg
     */
    ingentaCMSApp.displayTabularMetrics = function(tableName, graphName, eMsg) {
        var currTable = $("#" + tableName);
        currTable.before(eMsg);
        currTable.find("tbody .metricDate").each(function(index) {
            var currItem = $(this),
                dateStr = currItem.text(),
                mDate = new Date(dateStr.substr(0, 10));
            currItem.text(mDate.toDateString());
        });
        currTable.find(".metricDate, .totalCount").addClass("metricsErrorDesc");
        currTable.find(".metricCount").addClass("metricsErrorCount");
        currTable.addClass("metricsErrorTable");
        $("#" + graphName).addClass("hideMe");
    };
