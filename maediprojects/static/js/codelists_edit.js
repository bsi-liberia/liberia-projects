function resetFormGroup(input) {
  $(input).parent().removeClass("has-success has-error has-feedback");
  $(input).parent().find(".form-control-feedback").remove();
  $(input).parent().find(".form-control-status").remove();
}
function successFormGroup(input) {
  $(input).parent().addClass("has-success has-feedback");
  $(input).after('<span class="glyphicon glyphicon-floppy-saved form-control-feedback" aria-hidden="true"></span> \
  <span class="sr-only form-control-status">(success)</span>');
}
function errorFormGroup(input) {
  $(input).parent().addClass("has-error has-feedback");
  $(input).after('<span class="glyphicon glyphicon-floppy-remove form-control-feedback" aria-hidden="true"></span> \
  <span class="sr-only form-control-status">(error)</span>');
}
$(document).on("focus", "#codelists-data input", function(e) {
  resetFormGroup(this);
});
$("#confirm-delete").on('show.bs.modal', function(e) {
  $(this).find(".btn-ok").on("click", function(f) {
    deleteCode(e.relatedTarget);
    $("#confirm-delete").modal("hide");
  });
});

function deleteCode(target) {
  var data = {
    'codelist_code': $(target).closest("table").attr("data-codelist"),
    'code': $(target).closest("tr").attr("data-code"),
    "action": "delete"
  }
  var deleteButton = target;
  $.post("/api/codelists/delete/", data, 
    function(returndata){
      if (returndata == 'ERROR'){
          alert("There was an error deleting that code.");
      } else {
        $(deleteButton).closest("tr").fadeOut();
      }
    }
  );
}

$(document).on("click", ".addCode", function(e) {
  e.preventDefault();
  var codelist = $(this).attr("data-codelist");
  var data = {
    "codelist_code": codelist,
    "code": "",
    "name": ""
  }
  $.post("/api/codelists/new/", data, 
    function(returndata){
      if (returndata == 'ERROR'){
          alert("There was an error creating that code.");
      } else {
        var row_codelist_template = $('#row-codelist-template').html();
        var data = {
          "code": "",
          "name": ""
        }
      	var rendered_row = Mustache.render(row_codelist_template, data);
      	$('#table-' + codelist + ' tbody').append(rendered_row);
      }
    }
  );
});

$(document).on("change", ".codelists-data input[type=text]", function(e) {
  var data = {
    'codelist_code': $(this).closest("table").attr("data-codelist"),
    'code': $(this).closest("tr").attr("data-code"),
    'attr': this.name,
    'value': this.value,
  }
  var input = this;
  resetFormGroup(input);
  $.post("/api/codelists/update/", data, function(resultdata) {
    successFormGroup(input);
    if (data['attr'] == "code") {
      // We have to update the tr code if it gets adjusted in the UI
      $(input).closest("tr").attr("data-code", data["value"]);
    }
  }).fail(function(){
    errorFormGroup(input);
  });  
});