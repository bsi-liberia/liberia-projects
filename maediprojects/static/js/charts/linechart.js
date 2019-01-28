// linechart.js

var lineChart = {};

var lineChart = function(el, data) {
  this.$el = d3.select(el);

  this.controls = el+"-controls";
  this.data = null;
  this.xData = null;
  this.yData = null;

  var svg, dataCanvas, width, height, x, y, xAxis, yAxis, line, area, bisector, setValue, setDrilldown, controls, select, legends, tip;

  var margin = {top: 20, right: 20, bottom: 30, left: 70};
  this._calcSize = function() {
    width = parseInt(this.$el.style('width'), 10) - margin.left - margin.right;
    height = parseInt(this.$el.style('height'), 10) - margin.top - margin.bottom;
  };
  this._calcSize();
  
  var parseDate = d3.timeParse("%Y");
  var color = d3.scaleOrdinal(d3.schemeCategory10);   // set the colour scale
  var dec = d3.format(",.2f");
  
  this._init = function() {
    svg = this.$el.append('svg')
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom);

    dataCanvas = svg
      .append("g")
      .attr("class", "data-canvas")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    x = d3.scaleTime()
      .range([0, width]);
    y = d3.scaleLinear()
      .range([height, 0]);

    xAxis = dataCanvas.append("g")
      .attr("class", "x-axis");

    yAxis = dataCanvas.append("g")
      .attr("class", "y-axis");

    legends = dataCanvas.append("g")
      .attr("class", "legends");

    dataCanvas.append("g")
      .attr("class", "series");

    dataCanvas.append("g")
      .attr("class", "focus-circles");
    
    // Define xAxis function.
    xAxis = d3.axisBottom(x).ticks(10);
    yAxis = d3.axisLeft(y).ticks(10);

    // Line function.
    line = d3.line()
      .x(function(d) { return x(d.date); })
      .y(function(d) { return y(d[setValue]); });

    controls = this.controls;
    selectDiv = d3.select(controls)
      .append("div")
      .attr("class", "form-group")
      .append("form")
      .attr("class","form-horizontal");

    selectDiv
      .append("label")
      .attr("class", "control-label col-sm-2")
      .text("Display");

    select = selectDiv
      .append("div")
      .attr("class", "col-sm-3")
      .append("select")
      .attr("class", "form-control")
      .on('change', this.changeControls)
      
    this.setData(data);
  };
  this.setData = function(options) {
    this.data = options.data.sectors;
    setDrilldown = options.drilldown;
    this.values = options.values;
    setValue = options.values[0]
    
    this.data.forEach(function(d) {
      d.date = parseDate(d.fy);
    });
    this.update();
  }
  this.update = function() {
    this._calcSize();
    svg
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom);
    // Scale the range of the data
    x = d3.scaleTime()
      .range([0, width]);
    xAxis = d3.axisBottom(x).ticks(10);
    x.domain(d3.extent(this.data, function(d) { return d.date; }));
    y.domain([0, d3.max(this.data, function(d) { return d[setValue]; })]);

    tip = d3.tip()
      .attr('class', 'd3-tip')
      .offset([-10, 0])
      .html(function(d) {
        return "<strong>" + d[setDrilldown] + " (" + d.fy + ")</strong><br /><small>USD" + dec(d[setValue]) + "</small>";
      });
    svg.call(tip);

    // Nest the entries by symbol
    var dataNest = d3.nest()
      .key(function(d) {return d[setDrilldown];})
      .entries(this.data)
      .map(
        function(d) {
          return { color: d.color,
            active: d.active,
            key: d.key,
            values: d.values.sort(function(x, y){
              return d3.ascending(x.date, y.date);
            })
          }
        })
      .sort(function(x, y){
        return d3.ascending(x.key, y.key);
      });

    legendSpace = width/dataNest.length; // spacing for the legend

    dataCanvas.selectAll("g.series .line").remove();

    var lines = dataCanvas.select("g.series")
      .selectAll(".line")
      .data(dataNest);

    var _line = lines
      .enter()
      .append("path")
      .attr("class", function(d) { return "line " + slugify(d.key);})
      .style("stroke", function(d) { // Add the colours dynamically
        return d.color = color(d.key)})
      .attr("id", function(d) {return 'tag'+d.key.replace(/\s+/g, '')}) // assign ID
      .attr("d", function(d) {return line(d.values)})
      .call(transition)

    // Make legend
    legends
      .attr("font-family", "sans-serif")
      .attr("font-size", 10)
      .attr("text-anchor", "end")
        .attr("transform", function(d,i) {
          w = parseInt(width, 10);
          w -= margin.right;
          return "translate(" + w + ",0)";
        });

    var legend = legends
      .selectAll("g")
      .data(dataNest)
      .enter()
      .append("g")
      .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")" });

    legend
      .append("rect")
      .attr("x", -19)
      .attr("width", 19)
      .attr("height", 19)
      .attr("fill", function (d) { return color(d.key)})
      .style("cursor", "pointer")
      .on("click", function(d, i){
        // Determine if current line is visible 
        var active   = d.active ? false : true ,
        newOpacity = active ? 0 : 1; 
        // Hide or show the elements based on the ID
        d3.select("#tag"+d.key.replace(/\s+/g, ''))
          .transition().duration(100) 
          .style("opacity", newOpacity); 
        // Update whether or not the elements are active
        d.active = active;
        })

    legend
      .append("text")
      .attr("x", -24)
      .attr("y", 9.5)
      .attr("dy", "0.32em")
      .style("cursor", "pointer")
      .on("click", function(d, i){
        // Determine if current line is visible 
        var active   = d.active ? false : true ,
        newOpacity = active ? 0 : 1; 
        // Hide or show the elements based on the ID
        d3.select("#tag"+d.key.replace(/\s+/g, ''))
            .transition().duration(100) 
            .style("opacity", newOpacity); 
        // Update whether or not the elements are active
        d.active = active;
        })
      .text(function(d) {return d.key});

    var _values = this.values

    _this = this;
    if (_values.length > 1) {
      var options = select
        .selectAll("option")
        .data(_values)
        .enter().append("option")
        .attr("value", function(d) {return d})
        .text(function(d) {return d});      
    }

    // Create focus circle for each data point in each series
    var focuscircles = dataCanvas.select("g.focus-circles")
      .selectAll("circle")
      .data(function() { return $.map(dataNest, function(k) { return k.values; })})

    var focuscircle = focuscircles
      .enter()
      .append("circle")
      .merge(focuscircles) // this is new in D4!
      .style('opacity', 0)
      .attr("r",12)
        .attr("cx", function(d){ return x(d.date);})
        .attr("cy",function(d){return y(d[setValue]);})
        .attr("class","focus-circle")
        .on("mouseover", circlemouseover)
        .on("mouseout", circlemouseout);

    focuscircles.exit().remove();

    // Add the X Axis
    svg.select(".x-axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis);

    // Add the Y Axis
    dataCanvas.select(".y-axis")
      .attr("transform", "translate(0,0)")
      .call(yAxis);
  }

  function circlemouseover(d) {
    thecircle = d3.select(this);
    tip.show(d);
    the_line = d3.select(".line." + slugify(d.name));
    the_line.style("stroke-width", "4px");
  }
  function circlemouseout(d) {
    thecircle = d3.select(this);
    tip.hide();
    the_line = d3.select(".line." + slugify(d.name));
    the_line.style("stroke-width", "2px");
  }

  function slugify(text)
  {
    return text.toString().toLowerCase()
      .replace(/\s+/g, '-')           // Replace spaces with -
      .replace(/[^\w\-]+/g, '')       // Remove all non-word chars
      .replace(/\-\-+/g, '-')         // Replace multiple - with single -
      .replace(/^-+/, '')             // Trim - from start of text
      .replace(/-+$/, '');            // Trim - from end of text
  }

  function transition(path) {
      path.transition()
          .duration(1500)
          .attrTween("stroke-dasharray", tweenDash);
  }
  function tweenDash() {
      var l = this.getTotalLength(),
          i = d3.interpolateString("0," + l, l + "," + l);
      return function (t) { return i(t); };
  }

  this.changeControls = function() {
    selectValue = d3.select(controls+" select").property("value");
    console.log(selectValue)
    setValue = selectValue;
    _this.update();
  }

  this.destroy = function(el) {
    // Any clean-up would go here
    // in this example there is nothing to do
  };

  this._init();
};