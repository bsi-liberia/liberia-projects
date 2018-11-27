$("#change_password").change(function(e){
  var checked = $(this).prop('checked'); // is it checked?
  if ( checked ){
      $("#password").removeAttr('disabled',''); // enable
  } else {
      $("#password").attr('disabled','disabled'); // disable
  }
})
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

$('#confirm-delete').on('click', '.btn-ok', function(e) {
  var $modalDiv = $(e.delegateTarget);
  var permission_id = $(this).data('permission-id');
  deletePermission(permission_id);
  $modalDiv.modal('hide');
});

$("#confirm-delete").on('show.bs.modal', function(e) {
  var target = $(e.relatedTarget).closest("tr").attr("data-permission-id");
  $('.btn-ok', this).data("permission-id", target);
});

function deletePermission(permission_id) {
  var data = {
    "id": permission_id,
    "action": "delete"
  }
  $.post(api_user_permissions, data,
    function(returndata){
      if (returndata == 'False'){
          alert("There was an error deleting that permission.");
      } else {
        $("tr#permission-" + data["id"]).fadeOut();
      }
    }
  );
}
$(document).on("click", ".addPermission", function(e) {
  e.preventDefault();
  var permission_name = "view";
  var data = {
    "permission_name": "view_edit",
    "permission_value": "view",
    "action": "add"
  }
  $.post(api_user_permissions, data,
    function(returndata){
      if (returndata == 'False'){
          alert("There was an error updating that permission.");
      } else {
        var permissionsTemplate = $('#row-user-permissions-template').html();
        console.log(returndata)
        var rendered_P = Mustache.render(permissionsTemplate, returndata);
        $('#user-permissions-tbody').append(rendered_P);
      }
    }
   );
});
var updatePermissions = function(permissions) {
  // Render finances template
	var user_permissions_template = $('#user-permissions-template').html();
	Mustache.parse(user_permissions_template);
	partials = {"row-user-permissions-template": $('#row-user-permissions-template').html()};
	var rendered_P = Mustache.render(user_permissions_template, permissions, partials);
	$('#user-permissions-tbody').html(rendered_P);
}
var permissions_template;
var permissionsData;
var setupPermissions = function() {
	$.getJSON(api_user_permissions, function(permissions) {
      updatePermissions(permissions);
	});
};
setupPermissions()

$(document).on("change", "#user-permissions-tbody select", function(e) {
  var data = {
    'id': $(this).closest("tr").attr("data-permission-id"),
    'action': 'edit',
    'attr': this.name,
    'value': this.value
  }
  var input = this;
  resetFormGroup(input);
  $.post(api_user_permissions, data, function(resultdata) {
    successFormGroup(input);
  }).fail(function(){
    errorFormGroup(input);
  });
});
