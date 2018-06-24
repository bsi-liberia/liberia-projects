$(document).on("click", "#search_iati",
    function(e) {
  e.preventDefault();
  var title = $("#title").val();
  var reporting_org_code = $("#funding_org_code").val();
  console.log(reporting_org_code);
  var data = {
    "title": title,
    "reporting_org_code": reporting_org_code
  }
  $.post(api_iati_search_url, data, 
    function(returndata){
      if (returndata["count"] == '0'){
          alert("No activities found from IATI. Try adjusting the title or funding organisation code.");
      } else {
        $('#iati-search-results-modal').modal();
        // Render locations selector
      	var iati_results_template = $('#iati-search-results-template').html();
      	Mustache.parse(iati_results_template);
      	var rendered_search_results = Mustache.render(iati_results_template, {"title": title, "results": returndata["results"]});
      	$('#iati-search-results-area').html(rendered_search_results);
      }
    }
  );
});
$(document).on("click", "#iati-search-results-area .import a",
  function(e) {
  e.preventDefault();
  tr = $(this).closest("tr")
  iati_identifier = tr.find("td.iati_identifier a").html();
  description = tr.find("td.description").html();
  $("#code").val(iati_identifier);
  //$("#description").val(description);
  $('#iati-search-results-modal').modal('hide');
  $("#code").trigger("change");
  //$("#description").trigger("change");
});

// LOCATIONS
var locationsMap;

$(function() {
  locationsMap = new MAEDImap("locationMap");
	$.getJSON(api_activity_locations_url, function(data) {
      existingLocations = data;
      for (i in data["locations"]) {
        var l = data["locations"][i]["locations"];
        var toggle = locationsMap.toggleLocation(l);
      }
      locationsMap.resize();
      locationsMap.fitBounds([
          [4.3833, -11.3242],
          [8.37583, -7.56658]
      ]);
	});
});

// FINANCES
var updateFinances = function(finances) {
  // Render finances template
	var financial_template = $('#financial-template').html();
	Mustache.parse(financial_template);   // optional, speeds up future uses
  
	partials = {"row-financial-template": $('#row-financial-template').html()};
  
  function isC(finance) {
    return finance["transaction_type"] == "C";
  } 
  function isD(finance) {
    return finance["transaction_type"] == "D";
  }
  finances_C = {"finances": financialData["finances"].filter(isC),
                "transaction_type": "C"}
  finances_D = {"finances": financialData["finances"].filter(isD),
                "transaction_type": "D"}
  
	var rendered_C = Mustache.render(financial_template, finances_C, partials);
	$('#financial-data-C').html(rendered_C);
  
	var rendered_D = Mustache.render(financial_template, finances_D, partials);
	$('#financial-data-D').html(rendered_D);
  
}

var setupFinancesForm = function(finances) {
  updateFinances(finances);
};
var financial_template;
var financialData;
var setupFinances = function() {
	$.getJSON(api_activity_finances_url, function(data) {
      financialData = data;
      setupFinancesForm(data);
	});
};
setupFinances()

var setupForwardSpendForm = function(forwardspends) {
	var forward_spend_template = $('#forward-spend-template').html();
	Mustache.parse(forward_spend_template);
  
	partials = {"row-forward-spend-template": $('#row-forward-spend-template').html()};
  
	var rendered_FS = Mustache.render(forward_spend_template, forwardspends, partials);
	$('#financial-data-FS').html(rendered_FS);
}
var setupForwardSpend = function() {
	$.getJSON(api_activity_forwardspends_url, function(data) {
      setupForwardSpendForm(data);
	});
};
setupForwardSpend()