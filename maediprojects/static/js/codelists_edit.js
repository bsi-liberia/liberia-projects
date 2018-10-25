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


$("#confirm-delete").on('click', '.btn-ok', function(e) {
  $modalDiv = $(e.delegateTarget);
  var code_id = $(this).data("code_id");
  var codelist = $(this).data("codelist");
  deleteCode(code_id, codelist);
  $modalDiv.modal("hide");
});

$("#confirm-delete").on('show.bs.modal', function(e) {
  var code_id = $(e.relatedTarget).closest("tr").attr("data-id");
  var codelist = $(e.relatedTarget).closest("table").attr("data-codelist");
  $(".btn-ok", this).data("code_id", code_id);
  $(".btn-ok", this).data("codelist", codelist);
});

function deleteCode(code_id, codelist) {
  var data = {
    'codelist_code': codelist,
    'id': code_id,
    "action": "delete"
  }
  $.post("/api/codelists/delete/", data, 
    function(returndata){
      if (returndata == 'ERROR'){
          alert("There was an error deleting that code.");
      } else {
        $("tr#"+codelist+"-"+code_id).fadeOut();
      }
    }
  );
}

$(document).on("click", ".addCode", function(e) {
  e.preventDefault();
  var codelist = $(this).attr("data-codelist");
  var data = {
    "codelist_code": codelist,
    "code": "CODE",
    "name": ""
  }
  $.post("/api/codelists/new/", data, 
    function(returndata){
      if (returndata == 'ERROR'){
          alert("There was an error creating that code.");
      } else {
        if (codelist == "organisation") {
          var row_codelist_template = $('#row-organisation-template').html();
        } else {
          var row_codelist_template = $('#row-codelist-template').html();
        }
        var data = {
          "id": returndata,
          "codelist_code": codelist,
          "code": "CODE",
          "name": ""
        }
        var rendered_row = Mustache.render(row_codelist_template, data);
        $('#table-' + codelist + ' tbody').append(rendered_row);
      }
    }
  );
});

$(document).on("change", ".codelists-data input[type=text], .codelists-data select", function(e) {
  var data = {
    'codelist_code': $(this).closest("table").attr("data-codelist"),
    'id': $(this).closest("tr").attr("data-id"),
    'attr': this.name,
    'value': this.value,
  }
  var input = this;
  resetFormGroup(input);
  $.post("/api/codelists/update/", data, function(resultdata) {
    successFormGroup(input);
  }).fail(function(){
    errorFormGroup(input);
  });  
});