var pieChart = {};
var pieChart = function(el, data) {
  this.$el = d3.select(el);
  var el_top = $(el).offset().top;
  var el_left = $(el).offset().left;
  var _width, _height, svg, pie, arc, arcOver, tip, years, yearsdiv, drilldown, cuts, legends;
  var margin = {top: 10, right: 32, bottom: 10, left: 32};

  // Calculate based on element (window) size
  this._calcSize = function() {
    _width = parseInt(this.$el.style('width'), 10) - margin.left - margin.right;
    _height = parseInt(this.$el.style('height'), 10) - margin.top - margin.bottom;
  };

  this._calcSize();
  var width = _width,
      height = _height,
      radius = Math.min(width, height),
      color = d3.scaleOrdinal(d3.schemeCategory20);

  this._init = function() {
      this._calcSize();
      svg = this.$el.html('').append('svg')
          .attr("width", width)
          .attr("height", height)
          .append("g")
          .attr("transform", "translate(" + (width / 1.5)  + "," + height + ")");

      // FIXME: generalise this to show any dimension
      yearsdiv = this.$el.append("div")
          .attr("class", "pie-years")
          .append("ul");

      // Make pie only 180 rather than 360 degrees, and rotate 90 deg CCW
      pie = d3.pie()
          .value(function(d) { return +d.value; })
          .startAngle(-90*(Math.PI/180))
          .endAngle(90*(Math.PI/180))
          .sort(null);

      // Create arcs: one for normal, and one if selected
      arc = d3.arc()
          .outerRadius(radius - 30)
          .innerRadius(radius - 100);
      arcOver = d3.arc()
            .outerRadius(radius)
            .innerRadius(radius - 90);

      this.$el.on("mouseleave", mouseleave);
      // Create legend
      legends = svg.append("g")
    			.attr("class", "legend");
      this.setData(data);
  }

  this.setData = function(data) {
      this.data = data.records;
      this.drilldown = data.drilldown;
      this.cuts = data.cuts;
      cuts = this.cuts;
      // Cuts should look like e.g. {"year": "2013"}
      function filterByCut(obj) {
        for (var key in cuts) {
          if (obj[key] != cuts[key]) { return false; }
        }
        return true;
      }
      if (this.cuts != null) {
          this.data = this.data.filter(filterByCut);
      }
      this.update();
  }

  this.update = function () {
      var value = this.value === "count"
          ? function() { return 1; }
          : function(d) { return d.value; };

      drilldown = this.drilldown;
      tip = d3.tip()
        .attr('class', 'd3-tip')
        .offset([-10, 0])
        .html(function(d) {
          return "<strong>" + d.data[drilldown] + "</strong><br /><small>Disbursement: USD" + dec(d.data.value) + "</small>";
        });
      svg.call(tip);

	    // Update legends
	    var legend = legends
	        .selectAll(".legend")
          .data(this.data);
	    var l = legend
	      .enter()
	      .append("g")
	      .attr("class", "legend")
	      .html("<rect/><text/>")
	      .attr("transform", function (d, i) {
	        var lw = _width * 1.5;
	        // Needs to be this to compensate for a) width, b) datacanvas transform
	        lw -= 250;
	        lh =  -height + 20 + (i * 20);
	        return "translate(-" + lw + "," + lh + ")";
	      });

        l.select("rect")
	        .attr("x", _width - 350)
	        .attr("width", 18)
	        .attr("height", 18)
          .attr("class", function(d) { return "mtef-sector-"+d['code']; })

        l.select("text")
          .attr("x", _width - 325)
          .attr("y", 9)
          .attr("dy", ".35em")
          .text(function (d) { return d[drilldown]; });

  	  var g = svg.selectAll(".arc")
                 .data(pie(this.data));

      g
      	  .enter().append("path")
          .attr("d", arc)
  	      .style("stroke", "#fff")
          .style("stroke-width", 1)
  	      .style("fill-rule", "evenodd")
          .attr("class", "arc segment")
          .each(function(d) { this._current = d; })
          .attr("class", function(d) { return "arc segment mtef-sector-" + d.data['code']; })
          .on("mousemove",mouseover)
          .on("mouseout", mouseleave);

      g
          .transition().duration(750)
          .attrTween("d", arcTween);
  }

  function mouseover(d) {
    tip.show(d);
    var seg = d3.select(this);
    seg
      .transition()
      .duration(200)
      .style("opacity", 0.5);
  }

  function mouseclick(d) {
      var seg = d3.select(this);
      if (seg.classed("selected")) {
          seg
              .classed("selected", false)
              .transition()
              .duration(200)
              .attr("d", arc)
              .style("stroke-width", 1);
      } else {
          seg.classed("selected", true)
             .transition()
             .duration(50)
             .attr("d", arcOver)
             .style("stroke", "white")
             .style("stroke-width", 1);
      }
  }

  function mouseleave(d) {
    tip.hide();
    d3.selectAll(".segment")
      .transition()
      .duration(50)
      .style("opacity", 1);
  }

  function arcTween(a) {
    var i = d3.interpolate(this._current, a);
    this._current = i(0);
    return function(t) {
      return arc(i(t));
    };
  }

  var dec = d3.format(',.0f');

  this._init();
};