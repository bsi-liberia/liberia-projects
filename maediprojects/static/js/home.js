// PROJECTS
var updateProjects = function(projects) {
  // Render projects template
	var projects_template = $('#projects-template').html();
	Mustache.parse(projects_template);
	var rendered = Mustache.render(projects_template, projects);
	$('#projects-data').html(rendered);
  $("#projectsList").tablesorter( {sortList: [[0,0]]} );
}
var setupProjectsForm = function(projects) {
  updateProjects(projects);
};
var projects_template;
var projectData;
var setupProjects = function() {
	$.getJSON("/api/activities/", function(data) {
      projectData = data;
      setupProjectsForm(data);
	});
  $("#selectCountry").val("all").change();
};
setupProjects()
$(document).on("change", "#selectCountry", function(e) {
  if (e.currentTarget.value == "all") {
    var data = {}
  }
  else {
    var data = {
      'country_code': e.currentTarget.value
    }    
  }
  $.post("/api/activities/", data, function(resultdata) {
    setupProjectsForm(resultdata);
  });  
});