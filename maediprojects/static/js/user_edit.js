$("#change_password").change(function(e){
  var checked = $(this).prop('checked'); // is it checked?
  if ( checked ){
      $("#password").removeAttr('disabled',''); // enable
  } else {
      $("#password").attr('disabled','disabled'); // disable
  }
})