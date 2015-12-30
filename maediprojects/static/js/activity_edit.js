function resetFormGroup(input) {
  $(input).parent().removeClass("has-success has-error has-feedback");
  $(input).parent().find(".form-control-feedback").remove();
  $(input).parent().find(".form-control-status").remove();
}
function successFormGroup(input) {
  $(input).parent().addClass("has-success has-feedback");
  $(input).after('<span class="glyphicon glyphicon-ok form-control-feedback" aria-hidden="true"></span> \
  <span class="sr-only form-control-status">(success)</span>');
}
function errorFormGroup(input) {
  $(input).parent().addClass("has-error has-feedback");
  $(input).after('<span class="glyphicon glyphicon-remove form-control-feedback" aria-hidden="true"></span> \
  <span class="sr-only form-control-status">(error)</span>');
}
$(document).on("focus", "#activity-form input, #activity-form textarea, \
#form-result input, #form-result textarea, #form-indicator input, \
#form-indicator textarea, #form-period input, #form-period \
textarea", function(e) {
  resetFormGroup(this);
});
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
$(document).on("change", "#activity-form input[type=text], #activity-form textarea", function(e) {
  var data = {
    'attr': this.name,
    'value': this.value,
  }
  var input = this;
  resetFormGroup(input);
  $.post("update_activity/", data, function(resultdata) {
    successFormGroup(input);
  }).fail(function(){
    errorFormGroup(input);
  });  
});
$(document).on("change", ".result-data-form input[type=text], \
.result-data-form textarea", function(e) {
  form_type = $(this).closest("form").attr("data-result-form");
  parent_id = $(this).closest("form").attr("data-id");
  var data = {
    'attr': this.name,
    'value': this.value,
    'id': parent_id
  }
  var input = this;
  resetFormGroup(input);
  $.post("update_" + form_type + "/", data, function(resultdata) {
    successFormGroup(input);
  }).fail(function(){
    errorFormGroup(input);
  });  
});

$(document).on("click", "#deleteResultBtn, #deleteIndicatorBtn, \
#deletePeriodBtn", function(e) {
  e.preventDefault();
  form_type = $(this).attr("data-result-type");
  data_id = $(this).attr("data-id");

  var data = {
    'id': data_id,
    'result_type': form_type,
  }
  var input = this;
  resetFormGroup(input);

  $.post("delete_result_data/", data, function(resultdata) {
    $('#' + form_type + '-elements-' + data_id).fadeOut().remove();
  }).fail(function(){
    alert("Sorry, something went wrong and it wasn't possible to delete.")
  });
});
$('#addIndicatorModal, #addPeriodModal').on(
  'show.bs.modal', function (event) {
  var button = $(event.relatedTarget); // Button that triggered the modal
  var recipient = button.data('parent-id');
  var modal = $(this);
  modal.find('.modal-body #parent_id').val(recipient);
});
function add_result_data(data, id) {
  var d = {};
  $.map(data, function(item) {
      d[item.name] = item.value;
  });
  if (d['type'] == "result") {
    $("<div />", { id : 'result-elements-' + id })
    .append(' \
    <div class="pull-right"> \
      <a href="" id="deleteResultBtn" class="btn btn-danger" \
      data-id="' + id + '" data-result-type="result"> \
        <span class="glyphicon glyphicon-trash"></span> Delete result \
      </a> \
    </div> \
    <h3>Result</h3> \
    <form class="form-horizontal from-result result-data-form"  \
      id="result-' + id + '" data-id="' + id + '" \
      data-result-form="result"> \
      <div class="form-group"> \
        <label for="result_title" class="col-sm-2 control-label">Title</label> \
        <div class="col-sm-10"> \
          <input type="text" name="result_title" id="result_title" \
          placeholder="title" class="form-control" value="' + d['result_title'] + '"> \
        </div> \
      </div> \
      <div class="form-group"> \
        <label for="result_description" class="col-sm-2 control-label">Description</label> \
        <div class="col-sm-10"> \
          <textarea name="result_description" id="result_description"  \
          class="form-control" placeholder="description">' + d['result_description'] + '</textarea> \
        </div> \
      </div> \
      <div class="form-group"> \
        <label for="result_type" class="col-sm-2 control-label">Type</label> \
        <div class="col-sm-10"> \
          <input type="text" name="result_type" id="result_type" \
          placeholder="result type" class="form-control"  \
          value="' + d['result_type'] + '"> \
        </div> \
      </div> \
    </form> \
    <a href="" id="addIndicatorModalBtn" class="btn btn-success" \
      data-toggle="modal" data-target="#addIndicatorModal" \
      data-parent-id="' + id + '"> \
      <span class="glyphicon glyphicon-plus"></span> Add indicator \
    </a> \
    <hr /> \
  </div> \
    ').appendTo("#results");
    
  } else if (d['type'] == "indicator") {
    $("<div />", { id : 'indicator-elements-' + id })
      .append(' \
  <div id="indicator-elements-' + id + '"> \
    <div class="col-sm-11 col-sm-offset-1"> \
      <div class="pull-right"> \
        <a href="" id="deleteIndicatorBtn" class="btn btn-danger" \
        data-id="' + id + '" data-result-type="indicator"> \
          <span class="glyphicon glyphicon-trash"></span> Delete indicator \
        </a> \
      </div> \
      <h3>Indicator</h3> \
      <form class="form-horizontal form-indicator result-data-form"  \
      id="indicator-' + id + '"  \
      data-id="' + id + '" data-result-form="indicator"> \
        <div class="form-group"> \
          <label for="indicator_title" class="col-sm-2 control-label">Title</label> \
          <div class="col-sm-10"> \
            <input type="text" name="indicator_title" id="indicator_title" \
            class="form-control" placeholder="title"  \
            value="' + d['indicator_title'] + '"> \
          </div> \
        </div> \
        <div class="form-group"> \
          <label for="indicator_description" class="col-sm-2 control-label">Description</label> \
          <div class="col-sm-10"> \
            <textarea name="indicator_description" id="indicator_description"  \
            class="form-control"  \
            placeholder="description">' + d['indicator_description'] + '</textarea> \
          </div> \
        </div> \
        <div class="form-group"> \
          <label for="baseline_year" class="col-sm-2 control-label">Baseline year</label> \
          <div class="col-sm-10"> \
            <input type="text" name="baseline_year" id="baseline_year"  \
            class="form-control" placeholder="yyyy"  \
            value="' + d['baseline_year'] + '" /> \
          </div> \
        </div> \
        <div class="form-group"> \
          <label for="baseline_value" class="col-sm-2 control-label">Baseline value</label> \
          <div class="col-sm-10"> \
            <input type="text" name="baseline_value" id="baseline_value"  \
            class="form-control" placeholder="baseline value"  \
            value="' + d['baseline_value'] + '"  /> \
          </div> \
        </div> \
        <div class="form-group"> \
          <label for="baseline_comment" class="col-sm-2 control-label">Baseline comment</label> \
          <div class="col-sm-10"> \
            <textarea name="baseline_comment" id="baseline_comment"  \
            class="form-control" placeholder="comments...">' + d['baseline_comment'] + '</textarea> \
          </div> \
        </div> \
      </form> \
    <a href="" id="addPeriodModalBtn" class="btn btn-success" \
    data-toggle="modal" data-target="#addPeriodModal" \
    data-parent-id="' + id + '"> \
      <span class="glyphicon glyphicon-plus"></span> Add period \
    </a> \
    </div> \
  </div> \
    ')
    .appendTo("#result-elements-" + d['result_id']);
    
  } else if (d['type'] == "period") {
    $("<div />", { id : 'period-elements-' + id })
      .append(' \
        <div class="col-sm-10 col-sm-offset-2"> \
          <div class="pull-right"> \
            <a href="" id="deletePeriodBtn" class="btn btn-danger" \
            data-id="' + id + '" data-result-type="period"> \
              <span class="glyphicon glyphicon-trash"></span> Delete period \
            </a> \
          </div> \
          <h3>Period</h3> \
          <form class="form-horizontal form-period result-data-form"  \
          id="period-' + id + '" data-id="' + id + '"  \
          data-result-form="period"> \
            <div class="form-group"> \
              <label for="period_start" class="col-sm-2 control-label">Period start</label> \
              <div class="col-sm-10"> \
                <input type="text" name="period_start" id="period_start" \
                class="form-control" placeholder="yyyy-mm-dd"  \
                value="' + d['period_start'] + '"> \
              </div> \
            </div> \
            <div class="form-group"> \
              <label for="period_end" class="col-sm-2 control-label">Period end</label> \
              <div class="col-sm-10"> \
                <input type="text" name="period_end" id="period_end" \
                class="form-control" placeholder="yyyy-mm-dd"  \
                value="' + d['period_end'] + '"> \
              </div> \
            </div> \
            <div class="form-group"> \
              <label for="target_value" class="col-sm-2 control-label">Target value</label> \
              <div class="col-sm-10"> \
                <input type="text" name="target_value" id="target_value"  \
                class="form-control" placeholder="value" \
                 value="' + d['target_value'] + '" /> \
              </div> \
            </div> \
            <div class="form-group"> \
              <label for="target_comment" class="col-sm-2 control-label">Target comment</label> \
              <div class="col-sm-10"> \
                <textarea name="target_comment" id="target_comment"  \
                class="form-control" placeholder="comments...">' + d['target_comment'] + '</textarea> \
              </div> \
            </div> \
            <div class="form-group"> \
              <label for="actual_value" class="col-sm-2 control-label">Actual value</label> \
              <div class="col-sm-10"> \
                <input type="text" name="actual_value" id="actual_value"  \
                class="form-control" placeholder="value" value="' + d['actual_value'] + '" /> \
              </div> \
            </div> \
            <div class="form-group"> \
              <label for="actual_comment" class="col-sm-2 control-label">Actual comment</label> \
              <div class="col-sm-10"> \
                <textarea name="actual_comment" id="actual_comment"  \
                class="form-control" placeholder="comments...">' + d['actual_comment'] + '</textarea> \
              </div> \
            </div> \
          </form> \
        </div> \
    ')
    .appendTo("#indicator-elements-" + d['indicator_id']);
    
  }
}

$(document).on("click", "#addResultBtn, #addIndicatorBtn, #addPeriodBtn",
function(e) {
  e.preventDefault();
  form = "#" + $(this).data("form");
  data = $( form ).serializeArray();
  $.post("add_result_data/", data, function(resultdata) {
    $("#addResultModal, #addIndicatorModal, #addPeriodModal").modal('hide');
    id = resultdata['id'];
    add_result_data(data, id);
  }).fail(function(){
    alert("Sorry, something went wrong and it wasn't possible to add.")
  });
});
var locationsMap;
$(document).on("click", "#locationSelector .list-group-item",
  function(e) {
    e.preventDefault();
    if ($(this).hasClass("active")) {
      $(this).removeClass("active");
      if ($(this).attr("data-geonamesid")) {
        var newLocation = {
          "geonamesid": $(this).attr("data-geonamesid")
        }
        locationsMap.removeLocation(newLocation);
      }
    } else {
      $(this).addClass("active");
      if ($(this).attr("data-geonamesid")) {
        var newLocation = {
          "name": $(this).text(),
          "geonamesid": $(this).attr("data-geonamesid"),
          "longitude": $(this).attr("data-longitude"),
          "latitude": $(this).attr("data-latitude")
        }
        locationsMap.addLocation(newLocation);
      }
    }
});
$(function() {
  locationsMap = new MAEDImap("locationMap");
  $("body").on("shown.bs.tab", "#locationTab", function() {
    locationsMap.resize();
  });
});