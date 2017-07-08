/**
 * Created by dgosting on 8/30/16.
 */
var missing_coverage_count_cells = document.getElementsByClassName("missing_coverage_count");
var sample_name_cells = document.getElementsByClassName("sample_name");
var mutation_count_cells = document.getElementsByClassName("mutation_count");
var mean_coverage_cells = document.getElementsByClassName("mean_coverage");
var total_reads_cells = document.getElementsByClassName("total_reads");
var percent_reads_mapped_cells = document.getElementsByClassName("percent_reads_mapped");
var mapped_read_count_cells = document.getElementsByClassName("mapped_read_count");
var average_read_length_cells = document.getElementsByClassName("average_read_length");

var danger_color = '#cc3333';
var warning_color = 'pink';

for (var i = 0, max = missing_coverage_count_cells.length; i < max; i++) {

    var bad_data_row = false;

    var missing_coverage_count_upper_bound = 5;
    var mean_coverage_lower_bound = 75;
    var mapped_read_count_lower_bound = 1250000;

    var missing_coverage_count = missing_coverage_count_cells[i].childNodes[0].nodeValue;
    if (missing_coverage_count > missing_coverage_count_upper_bound) {

        missing_coverage_count_cells[i].style.backgroundColor = danger_color;

        if (mean_coverage_cells[i].style.backgroundColor != danger_color) {
            mean_coverage_cells[i].style.backgroundColor = warning_color
        }

        if (mapped_read_count_cells[i].style.backgroundColor != danger_color) {
            mapped_read_count_cells[i].style.backgroundColor = warning_color
        }

        bad_data_row = true
    }

    var mean_coverage = mean_coverage_cells[i].childNodes[0].nodeValue;
    if (mean_coverage < mean_coverage_lower_bound) {

        mean_coverage_cells[i].style.backgroundColor = danger_color;

        if (missing_coverage_count_cells[i].style.backgroundColor != danger_color) {
            missing_coverage_count_cells[i].style.backgroundColor = warning_color
        }

        if (mapped_read_count_cells[i].style.backgroundColor != danger_color) {
            mapped_read_count_cells[i].style.backgroundColor = warning_color
        }

        bad_data_row = true
    }

    var mapped_read_count = mapped_read_count_cells[i].childNodes[0].nodeValue;
    if (mapped_read_count < mapped_read_count_lower_bound) {

        mapped_read_count_cells[i].style.backgroundColor = danger_color;

        if (missing_coverage_count_cells[i].style.backgroundColor != danger_color) {
            missing_coverage_count_cells[i].style.backgroundColor = warning_color
        }

        if (mean_coverage_cells[i].style.backgroundColor != danger_color) {
            mean_coverage_cells[i].style.backgroundColor = warning_color
        }

        bad_data_row = true
    }

    if (bad_data_row) {
        sample_name_cells[i].style.backgroundColor = warning_color;
        mutation_count_cells[i].style.backgroundColor = warning_color;
        total_reads_cells[i].style.backgroundColor = warning_color;
        percent_reads_mapped_cells[i].style.backgroundColor = warning_color;
        average_read_length_cells[i].style.backgroundColor = warning_color;
    }
}
