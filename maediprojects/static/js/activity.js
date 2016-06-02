$('#datetimepicker_start').datetimepicker({
    format: 'YYYY-MM-DD'
});
$('#datetimepicker_end').datetimepicker({
    format: 'YYYY-MM-DD'
});
function resetFormGroup(input) {
  $(input).parent().parent().removeClass("has-success has-error has-feedback");
  $(input).parent().find(".form-control-feedback").remove();
  $(input).parent().find(".form-control-status").remove();
  $(input).parent().parent().find(".help-block").remove();
}
function successFormGroup(input) {
  $(input).parent().parent().addClass("has-success has-feedback");
  $(input).after('<span class="glyphicon glyphicon-floppy-saved form-control-feedback" aria-hidden="true"></span> \
  <span class="sr-only form-control-status">(success)</span>');
}
function errorFormGroup(input, optional_text) {
  $(input).parent().parent().addClass("has-error has-feedback");
  if (optional_text) {
    $(input).parent().after('<span class="help-block">' + optional_text + '</span>');
  }
  $(input).after('<span class="glyphicon glyphicon-floppy-remove form-control-feedback" aria-hidden="true"></span> \
  <span class="sr-only form-control-status">(error)</span>');
}
$(document).on("change", "#total_disbursements, #total_commitments", function (e) {
  resetFormGroup(this);
  if ((isNaN($(this).val() / 1) == true)) {
    errorFormGroup(this, "Ce champ doit respecter un pattern numérique - par exemple : 1000.00 - les virgules ne sont pas permis.");
    e.preventDefault();
  }
});
