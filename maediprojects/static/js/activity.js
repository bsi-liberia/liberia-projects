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