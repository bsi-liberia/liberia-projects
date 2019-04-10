
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

$(document).on("change", ".activity-form-save input[type=text], .activity-form-save input[type=number], .activity-form-save textarea, .activity-form-save select", function(e) {
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
    setupForwardSpend();
  }).fail(function(){
    errorFormGroup(input);
  });
});
$(document).on("click", "#search_iati",
    function(e) {
  e.preventDefault();
  var title = $("#title").val();
  var reporting_org_code = $("#reporting_org_id option:selected")[0].getAttribute("data-organisation-code");
  console.log(reporting_org_code);
  var data = {
    "title": title,
    "reporting_org_code": reporting_org_code
  }
  $.get(api_iati_search_url, data,
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
  if ($(e.relatedTarget).closest("tbody").attr("id") == "counterpart-funding-rows") {
    var target = $(e.relatedTarget).closest("tr").attr("data-counterpart-funding-id");
    $('.btn-ok', this).data("counterpart_funding_id", target);
    $('.btn-ok', this).data("delete_target", "counterpart_funding");
  } else {
    var target = $(e.relatedTarget).closest("tr").attr("data-financial-id");
    $('.btn-ok', this).data("transaction_id", target);
    $('.btn-ok', this).data("delete_target", "transaction");
  }
});

$('#confirm-delete').on('click', '.btn-ok', function(e) {
  var $modalDiv = $(e.delegateTarget);
  var delete_target = $(this).data('delete_target');
  if (delete_target == "counterpart_funding") {
    var counterpart_funding_id = $(this).data('counterpart_funding_id');
    deleteCounterpartFunding(counterpart_funding_id)
  } else if (delete_target == "transaction") {
    var transaction_id = $(this).data('transaction_id');
    deleteFinancial(transaction_id);
  }
  $modalDiv.modal('hide');
});

function deleteFinancial(transaction_id) {
  var data = {
    "transaction_id": transaction_id,
    "action": "delete"
  }
  $.post(api_activity_finances_url, data, 
    function(returndata){
      if (returndata == 'False'){
          alert("There was an error deleting that data.");
      } else {
        $("tr#financial-" + data["transaction_id"]).fadeOut();
      }
    }
  );
}

function deleteCounterpartFunding(counterpart_funding_id) {
  var data = {
    "id": counterpart_funding_id,
    "action": "delete"
  }
  $.post(api_activity_counterpart_funding_url, data,
    function(returndata){
      if (returndata == 'False'){
          alert("There was an error deleting that data.");
      } else {
        $("tr#counterpart-funding-" + data["id"]).fadeOut().remove();
      }
    }
  );
}

function last_quarter_transaction_date() {
  return moment().date(1).subtract(1, 'quarter').endOf('quarter').format('YYYY-MM-DD');
}

/* This is kind of a nasty hack… */
function setupCSSRules() {
  $.each($(".set-column-visibility li input"), function(i, checkbox) {
    target = $(checkbox).attr("data-target");
    //$("."+target).hide();
    $("head").append('<style id="style-'+target+'"></style>');
    addCSSRule(target, "display: none; width: 0%;");
  });
}
setupCSSRules()
function addCSSRule(target, style) {
  $('#style-'+target).html('th.'+target+', td.'+target+' {' + style + ';}');
}

$( '.set-column-visibility li' ).on( 'click', function( event ) {
    var $checkbox = $(this).find('input[type="checkbox"]');
    if (!$checkbox.length) {
        return;
    }
    var _target = $checkbox.attr("data-target");
    if ($checkbox.is(':checked')) { 
        $checkbox.prop('checked',false); 
        addCSSRule(_target, "display: none");
    } 
    else { 
      $checkbox.prop('checked',true); 
      addCSSRule(_target, "");
    }
    /*$("."+_target).toggle();*/
    return false;
});

/*  Financials */
$(document).on("click", ".addFinancial", function(e) {
  e.preventDefault();
  var transaction_type = $(this).attr("data-transaction-type");
  var transaction_date = last_quarter_transaction_date()
  var aid_type = $("#basic #aid_type option:selected")[0].value;
  var finance_type = $("#basic #finance_type option:selected")[0].value;
  var provider_org_id = $("#basic .organisations_select_1:first option:selected")[0].value;
  var receiver_org_id = $("#basic .organisations_select_4:first option:selected")[0].value;
  var mtef_sector = $("#sectors select.classification_mtef-sector:first option:selected")[0].value;
  var data = {
    "transaction_type": transaction_type,
    "transaction_date": transaction_date,
    "transaction_value": "0.00",
    "aid_type": aid_type,
    "finance_type": finance_type,
    "provider_org_id": provider_org_id,
    "receiver_org_id": receiver_org_id,
    "mtef_sector": mtef_sector,
    "action": "add"
  }
  $.post(api_activity_finances_url, data, 
    function(returndata){
      if (returndata == 'False'){
          alert("There was an error updating that financial data.");
      } else {
        var row_financial_template = $('#template-financial-row').html();
        data["id"] = returndata;
        var codelists = generateCodelists()
        var row = generateTransaction(data, codelists)
        partials = {"column-codelist-template": $('#column-codelist-template').html()};
        var rendered_row = Mustache.render(row_financial_template, row, partials);
        $('#financial-rows-' + transaction_type).append(rendered_row);
      }
    }
  );
});

var generateCodelists = function() {
  /* Generate list of aid types */
  codelists_aid_types = $.map($("#basic #aid_type option"), 
    function(d,i) { return {"code": d.value, 
                            "name": d.getAttribute("data-name") }});
  /* Generate list of finance types */
  codelists_finance_types = $.map($("#basic #finance_type option"), 
    function(d,i) { return {"code": d.value, 
                            "name": d.getAttribute("data-name") }});
  /* Generate list of mtef sectors */
  codelists_mtef_sectors = $.map($("#sectors select.classification_mtef-sector:first option"), 
    function(d,i) { return {"code": d.value, 
                            "name": d.getAttribute("data-name") }});
  /* Generate list of organisations */
  codelists_organisations = $.map($("#basic .organisations_select_1:first option"), 
    function(d,i) { return {"code": d.value, 
                            "name": d.getAttribute("data-name") }});
  return [
    { "attribute": "aid_type", "codes": codelists_aid_types,
      "name": "codelist_aid_types" },
    { "attribute":  "finance_type", "codes": codelists_finance_types,
      "name": "codelist_finance_types" },
    { "attribute":  "mtef_sector", "codes": codelists_mtef_sectors,
      "name": "codelist_mtef_sectors" },
    {"attribute": "provider_org_id", "codes": codelists_organisations,
      "name": "codelist_provider_orgs" },
    {"attribute": "receiver_org_id", "codes": codelists_organisations,
      "name": "codelist_receiver_orgs" }]
}

var generateTransaction = function(d, codelists) {
  $.map(codelists, function(cl, i) {
    d[cl.name] = $.map(cl.codes, function(c, ci) {
      if (d[cl.attribute] == c.code) { selected = " selected"; } 
      else { selected = ""; }
      return {"name": c.name, "code": c.code, "selected": selected};
    });
  });
  d["transaction_value_original"] = d["transaction_value"];
  d["transaction_value"] = d["transaction_value"].toLocaleString(
    undefined, {maximumFractionDigits:2, minimumFractionDigits:2});
  return d;
}

// FINANCES
var updateFinances = function(finances) {
  // Render finances template
	var financial_template = $('#template-financial').html();
	Mustache.parse(financial_template);   // optional, speeds up future uses
	partials = {"template-financial-row": $('#template-financial-row').html(),
              "column-codelist-template": $('#column-codelist-template').html()
            };
  function isC(finance) {
    return finance["transaction_type"] == "C";
  }
  function isD(finance) {
    return finance["transaction_type"] == "D";
  }
  var codelists = generateCodelists()
  function generateFinancialData(data) {
    return $.map(data, function(d,i) {
      return generateTransaction(d, codelists);
    });
  }
  financialDataC = generateFinancialData(financialData["finances"].filter(isC));
  financialDataD = generateFinancialData(financialData["finances"].filter(isD));
  finances_C = {"finances": financialDataC,
                "transaction_type": "C"}
  finances_D = {"finances": financialDataD,
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
$(document).on("change", ".finances-data input[type=text], #finances select, .finances-data input[type=hidden]", function(e) {
  var change_name = this.name;
  var change_value = this.value;
  var finances_id = $(this).closest("tr").attr("data-financial-id");
  var data = {
    'finances_id': $(this).closest("tr").attr("data-financial-id"),
    'attr': this.name,
    'value': this.value,
  }
  var input = this;
  resetFormGroup(input);
  $.post(api_update_activity_finances_url, data, function(resultdata) {
    successFormGroup(input);
    if ((input.name == 'currency_automatic') && (input.value == "1")) {
      $("#financial-" + finances_id + " input[name=currency_rate]").val(resultdata["currency_rate"]);
      $("#financial-" + finances_id + " input[name=currency_value_date]").val(resultdata["currency_value_date"]);
      $("#financial-" + finances_id + " input[name=currency_source]").val(resultdata["currency_source"]);
    }
  }).fail(function(){
    errorFormGroup(input);
  });  
});

var setupForwardSpendForm = function(forwardspends) {
	var forward_spend_template = $('#template-forward-spend').html();
	Mustache.parse(forward_spend_template);
	partials = {"template-forward-spend-row": $('#template-forward-spend-row').html()};
	var rendered_FS = Mustache.render(forward_spend_template, forwardspends, partials);
	$('#financial-data-FS').html(rendered_FS);
}
var setupForwardSpend = function() {
	$.getJSON(api_activity_forwardspends_url, function(data) {
      setupForwardSpendForm(data);
	});
};
setupForwardSpend()

$(document).on("change", ".forwardspends-data input[type=text]", function(e) {
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

/* Handle milestones */
$(document).on("change", "#milestones input[type=checkbox], #milestones textarea", function(e) {
  if ($(this).attr("data-milestone-attribute") == "achieved") {
    var value = this.checked;
  } else {
    var value = this.value;
  }
  var data = {
    'milestone_id': $(this).attr("data-milestone-id"),
    'attribute': $(this).attr("data-milestone-attribute"),
    'value': value,
  }
  var input = this;
  resetFormGroup(input);
  $.post(api_activity_milestones_url, data, function(resultdata) {
    successFormGroup(input);
  }).fail(function(){
    errorFormGroup(input);
  });
});

/* Counterpart Funding */
var updateCF = function(counterpart_funding_data) {
  // Render finances template
  var counterpart_funding_template = $('#template-counterpart-funding').html();
  Mustache.parse(counterpart_funding_template); // optional, speeds up future uses

  selected_val = {true:" selected", false: ""}
  $.map(counterpart_funding_data.counterpart_funding,
      function(d, i) {
      d['fiscal_years'] = $.map(counterpart_funding_data.fiscal_years,
            function(dfy, ify) {
              return {
                'text': "FY" + dfy + "/" + (parseInt(dfy)+1),
                'value': dfy,
                'selected': selected_val[d.required_fy==dfy]};
      });
    return d; });
  partials = {"template-counterpart-funding-row": $('#template-counterpart-funding-row').html()};
  var rendered = Mustache.render(counterpart_funding_template, counterpart_funding_data, partials);
  $('#counterpart-funding-data').html(rendered);
}
var counterpart_funding_template;
var counterpart_funding_data;
var setupCF = function() {
  $.getJSON(api_activity_counterpart_funding_url, function(data) {
      counterpart_funding_data = data;
      updateCF(counterpart_funding_data);
  });
};
setupCF()
$(document).on("change", ".table-counterpart-funding input[type=text], \
    .table-counterpart-funding input[type=checkbox], \
    .table-counterpart-funding select", function(e) {
      console.log(this.name);
  if (['budgeted', 'allotted', 'disbursed'].indexOf(this.name) >= 0) {
    if (this.checked) {
      value = true;
    } else {
      value = false;
    }
  } else {
    value = this.value;
  }
  var data = {
    'id': $(this).closest("tr").attr("data-counterpart-funding-id"),
    'attr': this.name,
    'value': value,
    'action': "update"
  }
  var input = this;
  resetFormGroup(input);
  $.post(api_activity_counterpart_funding_url, data, function(resultdata) {
    successFormGroup(input);
  }).fail(function(){
    errorFormGroup(input);
  });
});
/*  Add Counterpart Funding */
$(document).on("click", ".addCounterpartFunding", function(e) {
  e.preventDefault();
  var required_value = 0.0;
  var available_fys = $.map(
      $('#counterpart-funding-rows tr select[name="required_fy"]'), function(v, i) {
      console.log(v);
        return parseInt(v.value);
    });
  if (available_fys.length > 0) {
    var required_fy = Math.max.apply(Math, available_fys)+1;
  } else {
    var required_fy = moment().date(1).format('YYYY');
  }
  var data = {
    "required_value": required_value,
    "required_fy": required_fy,
    "action": "add"
  }
  $.post(api_activity_counterpart_funding_url, data,
    function(returndata){
      if (returndata == 'False'){
          alert("There was an error adding new counterpart funding.");
      } else {
        var template_counterpart_funding_row = $('#template-counterpart-funding-row').html();
        data["id"] = returndata;
        selected_val = {true:" selected", false: ""}
        data["fiscal_years"] = $.map(counterpart_funding_data.fiscal_years,
            function(dfy, ify) {
              console.log(dfy)
              console.log(required_fy)
              return {
                'text': "FY" + dfy + "/" + (parseInt(dfy)+1),
                'value': dfy,
                'selected': selected_val[required_fy==dfy]};
        });
        var rendered_row = Mustache.render(template_counterpart_funding_row, data);
        $('#counterpart-funding-rows').append(rendered_row);
      }
    }
  );
});

// Javascript to enable link to tab
var url = document.location.toString();
if (url.match('#')) {
    if (url.split('#')[1] == "location") {
      setupLocations();
    }
    $('.nav-tabs a[href="#' + url.split('#')[1] + '"]').tab('show');
    window.scrollTo(0, 0);
}
// Change hash for page-reload
$('.nav-tabs a').on('shown.bs.tab', function (e) {
    window.location.hash = e.target.hash;
    window.scrollTo(0, 0);
});
// Adjust currency popup
$("#adjustCurrency").on('show.bs.modal', function(e) {
  var target = $(e.relatedTarget).closest("tr").attr("data-financial-id");
  $(this).data("financial-id", target);
  var row_id = $(e.relatedTarget).closest("tr")[0].id;
  var row_data = {}
  $.each($("#" + row_id + " input, #" + row_id + " select").serializeArray(), function() {
    row_data[this.name] = this.value;
  });
  $("#adjustCurrency select[name='currency']").val([row_data['currency']]);
  $("#adjustCurrency input[name='currency_automatic']").val([row_data['currency_automatic']]);
  $("#adjustCurrency_currency_rate").val(row_data['currency_rate']);
  $("#adjustCurrency_currency_value_date").val(row_data['currency_value_date']);
  $("#adjustCurrency_currency_source").val(row_data['currency_source']);
});
$('#adjustCurrency').on('click', '.btn-ok', function(e) {
  var $modalDiv = $(e.delegateTarget);
  var tr_id = $modalDiv.data('financial-id');
  /* NB: if currency_automatic is 0 (manual), then disabled fields
  are NOT updated because they aren't returned in serializeArray() */
  $.each($("#adjustCurrency input, #adjustCurrency select").serializeArray(), function() {
    var changedName = this.name;
    var changedValue = this.value;
    $("tr#financial-" + tr_id + " input[name='" + changedName + "'], \
      tr#financial-" + tr_id + " select[name='" + changedName + "']").val(changedValue).trigger("change");
  });
  $modalDiv.modal('hide');
});
$("#adjustCurrency input[name='currency_automatic']").on("change", function(e) {
  if (this.value == "1") {
    $("#adjustCurrency_currency_rate, \
      #adjustCurrency_currency_value_date, \
      #adjustCurrency_currency_source").prop( "disabled", true );
  } else {
    $("#adjustCurrency_currency_rate, \
      #adjustCurrency_currency_value_date, \
      #adjustCurrency_currency_source").prop( "disabled", false );
  }
});
