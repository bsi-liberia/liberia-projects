
$(document).on("change", "#activity-form input[type=checkbox]", function(e) {
  var data = {
    'attr': this.name,
    'value': this.checked ? 1 : 0,
  }
  var activates = $(this).attr("data-activates");
  $("#"+activates).prop("disabled", !(this.checked));
    
  var input = this;
  resetFormGroup(input);
  $.post("update_activity/", data, function(resultdata) {
    successFormGroup(input);
  }).fail(function(){
    errorFormGroup(input);
  });  
});

function saveChangedFormValue(formField) {
  var data = {
    'attr': formField.name,
    'value': formField.value,
  }
  var input = formField;
  resetFormGroup(input);
  $.post("update_activity/", data, function(resultdata) {
    successFormGroup(input);
  }).fail(function(){
    errorFormGroup(input);
  });  
}

$(document).on("change", "#activity-form input[type=text], #activity-form input[type=number], #activity-form textarea, #activity-form select", function(e) {
  saveChangedFormValue(this);
});

// We have to handle datetimepickers slightly differently from other form
// inputs.
$('#datetimepicker_start, #datetimepicker_end')
.on("dp.change", function(e) {
  var data = {
    'attr': e.target.firstElementChild.name,
    'value': e.target.firstElementChild.value,
  }
  var input = e.target.firstElementChild;
  resetFormGroup(input);
  $.post("update_activity/", data, function(resultdata) {
    successFormGroup(input);
  }).fail(function(){
    errorFormGroup(input);
  });  
});
    
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
	});
  
  $("body").on("shown.bs.tab", "#locationTab", function() {
    setupLocations()
  });
});

$(document).on("click", "#locationSelector .list-group-item",
  function(e) {
    e.preventDefault();
    var location = {
      "name": $(this).text(),
      "id": $(this).attr("data-id"),
      "longitude": $(this).attr("data-longitude"),
      "latitude": $(this).attr("data-latitude")
    }
    var toggle = locationsMap.toggleLocation(location);
    if (toggle == "added") {
      $(this).addClass("active");
      var data = {
        "action": "add",
        "location_id": location["id"]
      }
    } else {
      $(this).removeClass("active");
      var data = {
        "action": "delete",
        "location_id": location["id"]
      }
    }
    $.post(api_activity_locations_url, data, 
      function(returndata){
        if (returndata == 'False'){
            alert("There was an error updating that location.");
        }
      }
    );
});

var updateLocationsMarkers = function(locations) {
  for (i = 0; i < locations["locations"].length; i++) {
    if (locations["locations"][i]["id"] in markers) {
      locations["locations"][i]["active"] = "active";
    } else {
      locations["locations"][i]["active"] = "";      
    }
  }
  return locations;
}

var updateLocationsSelector = function(locations) {
  // Render locations selector
	var locations_selector_template = $('#locations-selector-template').html();
	Mustache.parse(locations_selector_template);   // optional, speeds up future uses
	var rendered_locations_selector = Mustache.render(locations_selector_template, locations);
	$('#locations-selector').html(rendered_locations_selector);
}

var updateLocationsList = function(locations) {
  // Render locations template
	locations_template = $('#locations-template').html();
	Mustache.parse(locations_template);   // optional, speeds up future uses
  
  // Check location markers and make sure we're highlighting things nicely
  locations = updateLocationsMarkers(locations);
	var rendered_locations = Mustache.render(locations_template, locations);
	$('#location-data').html(rendered_locations);
}

var setupLocationsForm = function(locations) {
  /* ON LOAD. Add some nicer error handling here at some point... */
  
  function isADM1(location) {
    return location["feature_code"] == "ADM1";
  }
  locations_adm1 = {"locations": locationsData["locations"].filter(isADM1)}
  
  updateLocationsSelector(locations_adm1);
  updateLocationsList(locations_adm1);
};
$(document).on("change", "#selectLocationType", function(e) {
  var adm1 = this.value;
  if (adm1 == "all") {
    updateLocationsList(locationsData);
  } else if (adm1 == "regions") {
    function isRelevant(location) {
        return location["feature_code"] == "ADM1";
    }
    var relevantLocations = {"locations": locationsData["locations"].filter(isRelevant) }
    updateLocationsList(relevantLocations);
  } else {
    function isRelevant(location) {
        return location["admin1_code"] == adm1;
    }
    var relevantLocations = {"locations": locationsData["locations"].filter(isRelevant) }
    updateLocationsList(relevantLocations);
  }
});

var locations_template;
var locationsData;
var setupLocations = function() {
	$.getJSON(api_locations_url, function(data) {
      locationsData = data;
      setupLocationsForm(data);
      function getLats(location) {
        return parseFloat(location["latitude"]);
      }
      function getLongs(location) {
        return parseFloat(location["longitude"]);
      }
      var lats = data["locations"].map(getLats);
      var longs = data["locations"].map(getLongs);
      locationsMap.resize();
      locationsMap.fitBounds([
          [Math.min.apply(null, lats), Math.min.apply(null, longs)],
          [Math.max.apply(null, lats), Math.max.apply(null, longs)]
      ]);
	});
};

$("#confirm-delete").on('show.bs.modal', function(e) {
  $(this).find(".btn-ok").on("click", function(f) {
    deleteFinancial(e.relatedTarget);
    $("#confirm-delete").modal("hide");
  });
});

function deleteFinancial(target) {
  var data = {
    "transaction_id": $(target).closest("tr").attr("data-financial-id"),
    "action": "delete"
  }
  $.post(api_activity_finances_url, data, 
    function(returndata){
      if (returndata == 'False'){
          alert("There was an error updating that financial data.");
      } else {
        $("tr#financial-" + data["transaction_id"]).fadeOut();
      }
    }
  );
}

$(document).on("click", ".addFinancial", function(e) {
  e.preventDefault();
  var transaction_type = $(this).attr("data-transaction-type");
  var data = {
    "transaction_type": transaction_type,
    "action": "add"
  }
  $.post(api_activity_finances_url, data, 
    function(returndata){
      if (returndata == 'False'){
          alert("There was an error updating that financial data.");
      } else {
        var row_financial_template = $('#row-financial-template').html();
        var data = {
          "id": returndata,
          "transaction_type": transaction_type
        }
      	var rendered_row = Mustache.render(row_financial_template, data);
      	$('#financial-rows-' + transaction_type).append(rendered_row);
      }
    }
  );
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

$(document).on("change", "#financial-data-C input[type=text], #financial-data-D input[type=text]", function(e) {
  var data = {
    'finances_id': $(this).closest("tr").attr("data-financial-id"),
    'attr': this.name,
    'value': this.value,
  }
  var input = this;
  resetFormGroup(input);
  $.post(api_update_activity_finances_url, data, function(resultdata) {
    successFormGroup(input);
  }).fail(function(){
    errorFormGroup(input);
  });  
});

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

$(document).on("change", "#financial-data-FS input[type=text]", function(e) {
  if ($(this).attr("data-forwardspend-id")) {
    var data = {
      'id': $(this).attr("data-forwardspend-id"),
      'value': this.value,
    }
    var input = this;
    resetFormGroup(input);
    $.post(api_activity_forwardspends_url, data, function(resultdata) {
      successFormGroup(input);
    }).fail(function(){
      errorFormGroup(input);
    });
  } else {
    var input_fields = $(this).closest("tr").find("input[type=text].fs-quarter")
    var num_quarters = input_fields.length;
    var input_fields_value = this.value/input_fields.length;
    $.each(input_fields, function(i, this_field) {
      $(this_field).val(input_fields_value);
      $(this_field).trigger("change");
    });
  }

});



// We have to handle datetimepickers slightly differently from other form
// inputs.
$('#datetimepicker_start, #datetimepicker_end')
.on("dp.change", function(e) {
  var data = {
    'attr': e.target.firstElementChild.name,
    'value': e.target.firstElementChild.value,
  }
  var input = e.target.firstElementChild;
  resetFormGroup(input);
  $.post("update_activity/", data, function(resultdata) {
    successFormGroup(input);
  }).fail(function(){
    errorFormGroup(input);
  });  
});