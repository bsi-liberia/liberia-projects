// barchart.js

var barChart = {};

var barChart = function(el, options) {
  this.$el = d3.select(el);
  var svg, margin, height, g, x0, x1, y, z, xAxis, yAxis, legends, dataCanvas;
  
  this._init = function() {
    svg = this.$el.append("svg")
          .attr("width",  960)
          .attr("height", 500),
        margin = {top: 20, right: 20, bottom: 100, left: 70},
        width = 960 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom,
        g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");


    dataCanvas = svg
      .append("g")
      .attr("class", "data-canvas")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    x0 = d3.scaleBand()
        .rangeRound([0, width])
        .paddingInner(0.1);

    x1 = d3.scaleBand()
        .padding(0.05);

    y = d3.scaleLinear()
        .rangeRound([height, 0]);

    bars = dataCanvas.append("g")
      .attr("class", "bars")

    dataCanvas.append("g")
      .attr("class", "x-axis");

    dataCanvas.append("g")
      .attr("class", "y-axis")
      .append("text")
        .attr("class", "axis-legend");
    
    // Define xAxis function.
    xAxis = d3.axisBottom(x0).ticks(10);
    yAxis = d3.axisLeft(y).ticks(null).tickFormat(function(d) {
          return d / 1000000000 + 'bn';
        });

    legends = dataCanvas.append("g")
        .attr("class", "legends");
    
    if (options.colours) {
      z = d3.scaleOrdinal().range(options.colours);
    } else {
      z = d3.scaleOrdinal(d3.schemeCategory10);
    }
        
    this.setData(options);     
  }
  this.setData = function(options) {
    this.data = options.data;
    this.keys = options.keys;
    this.update();
  }
  this.update = function () {
    var data = this.data;
    var keys = this.keys;

    x0.domain(data.map(function(d) { return d.name; }));
    x1.domain(keys).rangeRound([0, x0.bandwidth()]);
    y.domain([0, d3.max(data, function(d) { return d3.max(keys, function(key) { return d[key]; }); })]).nice();

    tip = d3.tip()
      .attr('class', 'd3-tip')
      .offset([-10, 0])
      .html(function(d) {
        return "<strong>" + d.key + "</strong><br /><small>USD" + dec(d.value) + "</small>";
      });
    svg.call(tip);

    var bars = svg.select("g.bars")
      .selectAll("g.bargroup")
      .data(data)

    var bargroup = bars
      .enter()
      .append("g")
      .merge(bars)
        .attr("class", "bargroup")
        .attr("transform", function(d) { return "translate(" + x0(d.name) + ",0)"; })
      .selectAll("rect")
      .data(function(d) { return keys.map(function(key) { return {key: key, value: d[key]}; }); })

    var bar = bargroup
      .enter().append("rect")
        .attr('height', 0)
        .attr('y', height)

    bar
        .merge(bargroup)
        .transition()
        .duration(500)
        .attr("class","bar")
        .attr("x", function(d) { return x1(d.key); })
        .attr("y", function(d) { return y(d3.max([d.value, 0])); })
        .attr("width", x1.bandwidth())
        .attr("height", function(d) { return height - y(d3.max([d.value, 0])); })
        .attr("fill", function(d) { return z(d.key); })
    bar
        .on("mousemove",mouseover)
        .on("mouseout", mouseleave);

    bargroup.exit().remove()
    bars.exit().remove()

    // Add the X Axis
    svg.select(".x-axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis)
        .selectAll("text")  
          .style("text-anchor", "end")
          .attr("dx", "-.8em")
          .attr("dy", ".15em")
          .attr("transform", "rotate(-45)")
          .call(wrap, x0.bandwidth());

    // Add the Y Axis
    _yAxis = svg.select(".y-axis")
      .attr("transform", "translate(0,0)")
      .call(yAxis)

    _yAxisLegend = _yAxis.select("text.axis-legend")
        .attr("x", 2)
        .attr("y", y(y.ticks().pop()) + 0.5)
        .attr("dy", "0.32em")
        .attr("fill", "#000")
        .attr("font-weight", "bold")
        .attr("text-anchor", "start")
        .text("Value (USD millions)")

    _yAxisLegend
        .exit().remove();

    /*

    g.append("g")
        .attr("class", "axis")
        .attr("transform", "translate(-10," + height + ")")
        .call(d3.axisBottom(x0).ticks(10))
        ;

    g.append("g")
        .attr("class", "axis")
        .call(d3.axisLeft(y).ticks(null).tickFormat(function(d) {
          return d / 1000000000 + 'bn';
        }))
      .append("text")
        .attr("x", 2)
        .attr("y", y(y.ticks().pop()) + 0.5)
        .attr("dy", "0.32em")
        .attr("fill", "#000")
        .attr("font-weight", "bold")
        .attr("text-anchor", "start")
        .text("Value");
        */

    var legend = legends
        .attr("font-family", "sans-serif")
        .attr("font-size", 10)
        .attr("text-anchor", "end")
        .selectAll("g")
       .data(keys.slice())
       .enter().append("g")
        .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

    legend.append("rect")
        .attr("x", width - 19)
        .attr("width", 19)
        .attr("height", 19)
        .attr("fill", z);

    legend.append("text")
        .attr("x", width - 24)
        .attr("y", 9.5)
        .attr("dy", "0.32em")
        .text(function(d) { return d; });

    legend.exit().remove();
  }
  function wrap(text, width) {
    text.each(function() {
      var text = d3.select(this),
          words = text.text().split(/\s+/).reverse(),
          word,
          line = [],
          lineNumber = 0,
          lineHeight = 1.1, // ems
          y = text.attr("y"),
          dy = parseFloat(text.attr("dy")),
          tspan = text.text(null).append("tspan").attr("x", 0).attr("y", y).attr("dy", dy + "em");
      while (word = words.pop()) {
        line.push(word);
        tspan.text(line.join(" "));
        if (tspan.node().getComputedTextLength() > width) {
          line.pop();
          tspan.text(line.join(" "));
          line = [word];
          tspan = text.append("tspan").attr("x", 0).attr("y", y).attr("dy", ++lineNumber * lineHeight + dy + "em").text(word);
        }
      }
    });
  } 
  function mouseover(d) {
    tip.show(d);
    var seg = d3.select(this);
    seg
      .transition()
      .duration(50)
      .style("fill-opacity", 0.5);
  }
  function mouseleave(d) {
    tip.hide();
    d3.selectAll("rect")
      .transition()
      .duration(50)
      .style("fill-opacity", 1);
  }
  var dec = d3.format(',.0f');
  this._init();
}