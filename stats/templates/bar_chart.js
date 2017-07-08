/**
* Created by dgosting on 6/29/16.
*/

var barHeight = 30;
var height = (barHeight + 10) * gene_data.length;
var width = 500;
var padding = 100;

var x = d3.scale.linear().domain([0, gene_data.length]).range([0, height]);
var y = d3.scale.linear().domain([0, d3.max(gene_data, function(datum) { return datum.the_count; })]).rangeRound([0, width]);

// add the canvas to the DOM
var gene_bar = d3.select(".chart").
append("svg:svg").
attr("height", height).
attr("width", width + padding + (2*extra_padding));

gene_bar.selectAll("rect").
data(gene_data).
enter().
append("svg:rect").
attr("y", function(datum, index) { return x(index); }).
attr("x", padding + (2*extra_padding)).
attr("width", function(datum) { return y(datum.the_count); }).
attr("height", barHeight).
attr("fill", function (datum) {return datum.color;});

gene_bar.selectAll("text").
data(gene_data).
enter().
append("svg:text").
attr("y", function(datum, index) { return x(index) + barHeight + 5; }).
attr("x", function(datum) { return y(datum.the_count) + 80 + (2*extra_padding); }).
attr("dy", -barHeight/2).
attr("dx", "1.2em").
attr("text-anchor", "end").
text(function(datum) { return datum.the_count;}).
attr("fill", "white");

gene_bar.selectAll("text.yAxis").
data(gene_data).
enter().append("svg:text").
attr("y", function(datum, index) { return x(index) + barHeight + 5; }).
attr("x", padding - 5 + (2*extra_padding)).
attr("dy", -barHeight/2).
attr("text-anchor", "end").
attr("style", "font-size: 14; font-family: Helvetica, sans-serif; font-weight: bold").
text(function(datum) { return _get_label(datum)}).
attr("class", "yAxis").
attr("fill", "black");

var legend = gene_bar.append("g")
    .attr("class", "legend")
    .attr("height", 100)
    .attr("width", 100);

legend.selectAll('rect')
    .data(color_set)
    .enter()
    .append("rect")
    .attr("x", width + extra_padding)
    .attr("y", function(d, i){ return (i *  20) + height - 250;})
    .attr("width", 10)
    .attr("height", 10)
    .style("fill", function(d) {return color_set[color_set.indexOf(d)];});

legend.selectAll('text')
    .data(mutation_types)
    .enter()
        .append("text")
    .attr("x", width + 15 + extra_padding)
    .attr("y", function(d, i){ return (i *  20) + height - 250 + 10;})
    .text(function(d) {return mutation_types[mutation_types.indexOf(d)];});
