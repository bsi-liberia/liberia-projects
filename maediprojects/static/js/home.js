
  $(document).on("change", "#select-fy", function(){
    var year = $(this).val();
    pieOptions["cuts"]["fy"] = year;
    thisPieChart.setData(pieOptions);
  });
  
  var makeTitle = function(str) {
    return str.charAt(0).toUpperCase() + str.substr(1);
  }

  d3.json("/api/sectors_C_D.json", function(error, data) {
    data.sectors = data.sectors.filter(function(d) {
          return (d.fy > 2012) && (d.fy < 2020);
        })
    // LINE CHART
    lineOptions = {
      "data": {
        "sectors": data.sectors.filter(function(d) {
          return (d.fy > 2012) && (d.fy < 2019);
        })
      },
      "drilldown": "name",
      "values": ["Disbursements", "Disbursement Projection","Commitments"]
    }
    thisLineChart = new lineChart("#line-chart", lineOptions);
    // END LINE CHART

    // C/D by sector
    var optionsCDC = {
      'data': d3.nest()
        .key(function(d) { return d.name; })
        .rollup(function(v) { return {
          "Commitments": d3.sum(v, function(d) { return d.Commitments; }), 
          "Disbursements": d3.sum(v, function(d) { return d.Disbursements; }), 
          "Disbursement Projection": d3.sum(v, function(d) { return d["Disbursement Projection"]; })
        }; })
        .entries(data.sectors)
        .map(
          function(d) {
            return { name: d.key,
                     "New Commitments": d.value.Commitments,
                     "Disbursements": d.value.Disbursements,
                     "Disbursement Projection": d.value["Disbursement Projection"],
                     //"Balance (Commitments - Disbursements)": d.value.Commitments - d.value.Disbursements
                   }
         }).sort(function(x, y){
           return d3.ascending(x.name, y.name);
         }),
       'keys': ["Disbursement Projection", "Disbursements", "New Commitments"],
       'colours': ["#1f77b4", "#2ca02c", "#ff7f0e"]
    }
    $(".loading-bar-chart").fadeOut();
    cdBarChart = new barChart("#commitments-disbursements-chart", optionsCDC);

    years = (d3.map(data.sectors, function(d){return d.fy;}).keys().sort(function(x, y){
        return d3.descending(x, y);
      }))
    years.unshift("All years")

    yearsControlD = d3.select("#commitments-disbursements-chart-controls")
      .append("div")
      .attr("class", "form-group")
      .append("form")
      .attr("class","form-horizontal");

    yearsControlD
      .append("label")
      .attr("class", "control-label col-sm-2")
      .text("Fiscal Year");

    yearsControl = yearsControlD
      .append("div")
      .attr("class", "col-sm-3")
      .append("select")
      .on("change", function() { changeChart(this)} )

    function changeChart(obj) {
      _entries = function() { 
        if (obj.value.length == 4) {
          return data.sectors.filter(function(d) {
            return (d.fy == obj.value);
          })
        } else {
          return data.sectors;
        }
      } 
      optionsCDC['data'] = d3.nest()
        .key(function(d) { return d.name; })
        .rollup(function(v) { return {
          Commitments: d3.sum(v, function(d) { return d.Commitments; }), 
          Disbursements: d3.sum(v, function(d) { return d.Disbursements; }), 
          "Disbursement Projection": d3.sum(v, function(d) { return d["Disbursement Projection"]; })
        }; })
        .entries(_entries())
        .map(
          function(d) {
            return { name: d.key,
                     "New Commitments": d.value.Commitments,
                     "Disbursements": d.value.Disbursements,
                     "Disbursement Projection": d.value["Disbursement Projection"],
                     //"Balance (Commitments - Disbursements)": d.value.Commitments - d.value.Disbursements
                   }
         }).sort(function(x, y){
           return d3.ascending(x.name, y.name);
         })
      cdBarChart.setData(optionsCDC)
    }
    var years = yearsControl
      .attr("class", "form-control")
      .selectAll("option")
      .data(years)

    years.enter()
      .append("option")
      .attr("value", function(d) { return d })
      .text(function(d) { return d })

    if (permissions_domestic_external == "both") {
      var options = {
        'data': d3.nest()
          .key(function(d) { return d.name; })
          .key(function(d) { return d.domestic_external; })
          .rollup(function(v) { return {
            Commitments: d3.sum(v, function(d) { return Math.max(d.Commitments, 0); }), 
            Disbursements: d3.sum(v, function(d) { return Math.max(d.Disbursements, 0); })
          }; })
          .entries(data.sectors)
          .map(
            function(d) {
              t = {
                name: d.key
              }
              d.values.map(function(dv) {
                t[makeTitle(dv.key)+" Commitments"] = dv.value.Commitments;
                t[makeTitle(dv.key)+" Disbursements"] = dv.value.Disbursements;
              });
              return t;
           }).sort(function(x, y){
             return d3.ascending(x.name, y.name);
           }),
         'keys': ["External Commitments", "External Disbursements", "Domestic Commitments", "Domestic Disbursements"],
         'colours': ["#98abc5", "#8a89a6", "#d0743c", "#ff8c00"]
      }
      cdSourceBarChart = new barChart("#commitments-disbursements-source-chart", options);

      // C/D, domestic
      var options = {
      'data': d3.nest()
        .key(function(d) { return d.name; })
        .rollup(function(v) { return {
          Commitments: d3.sum(v, function(d) { return d.Commitments; }),
          Disbursements: d3.sum(v, function(d) { return d.Disbursements; })
        }; })
        .entries(data.sectors
          .filter(function(d) { return d.domestic_external == "domestic";}))
        .map(
          function(d) {
            return { name: d.key,
                     Commitments: d.value.Commitments,
                     Disbursements: d.value.Disbursements,
                     "Balance (Commitments - Disbursements)": d.value.Commitments - d.value.Disbursements}
         }).sort(function(x, y){
           return d3.ascending(x.name, y.name);
         }),
       'keys': ["Commitments", "Disbursements", "Balance (Commitments - Disbursements)"],
       'colours': ["#d0743c", "#ff8c00", "#a05d56"]
      }
      cdDomesticBarChart = new barChart("#commitments-disbursements-domestic-chart", options);

      var pieOptions, thisPieChart, cdBarChart, cdSourceBarChart;
      d3.json("/api/sectors.json", function(error, data) {
        pieOptions = {
          "records": data["sectors"],
          "drilldown": "name",
          "cuts": {
                    "fy": "2017"
                  }
        }
        thisPieChart = new pieChart("#sectors-pie", pieOptions);
      });
    }
  });
  
  // LOCATIONS
  var locationsMap;

  $(function() {
    locationsMap = new MAEDImap("locationMap", {"all_projects": true});
    $.getJSON(api_activity_locations_url, function(data) {
        existingLocations = data;
        var markerLayer = L.markerClusterGroup({showCoverageOnHover:false});
        for (i in data["locations"]) {
          var l = data["locations"][i]["locations"];
          var toggle = locationsMap.addLocation(l, markerLayer, data["locations"][i]);
        }
        $(".loading-map").hide();
        locationsMap.addLayer(markerLayer);
        locationsMap.resize();
        locationsMap.fitBounds([
            [4.3833, -11.3242],
            [8.37583, -7.56658]
        ]);
    });
  });