/**
 * Created by dgosting on 9/19/16.
 */
var selected_experiments = [];
$(function(){
    $("#experiment_selector li a").click(function(){
        $("#selector_button").text($(this).text());
        $("#selector_button").val($(this).text());
    });
 });
function add_experiment_to_download_list() {
    var exp_name = document.getElementById('selector_button').innerText;
    if(exp_name == "Select Experiment") {

    } else if(exp_name == 'All') {
        for(var i = selected_experiments.length - 1; i >= 0; i--) {
            remove_experiment(selected_experiments[i])
        }
        add_exp_to_list('All')

    } else if(!selected_experiments.includes(exp_name)) {
        if(selected_experiments.includes('All')) {
            remove_experiment('All');
        }
        add_exp_to_list(exp_name)
    }
    set_export_experiments_input_field();

    document.getElementById('download').style.display = 'inline';
    document.getElementById('mut_type_selected').style.display = 'inline';
}

function add_exp_to_list(exp_name) {
    var ul = document.getElementById("selected_experiments");
    var li = document.createElement("li");
    var exp = document.createElement("div");
    exp.setAttribute("class", "pull-left");
    exp.innerText = exp_name;
    var trash_can = document.createElement("div");
    trash_can.setAttribute("class", "pull-right");
    trash_can.innerHTML = '<a href="#/"><i class="fa fa-trash" aria-hidden="true"></i></a>';
    trash_can.onclick = function () {
        remove_experiment(exp_name)
    };
    var clear_div = document.createElement("div");
    clear_div.setAttribute("class", "clearfix");
    li.appendChild(exp);
    li.appendChild(trash_can);
    li.appendChild(clear_div);
    li.setAttribute("class", "list-group-item");
    li.setAttribute("id", exp_name);
    ul.appendChild(li);
    selected_experiments.push(exp_name)
}

function remove_experiment(param) {
    var elem = document.getElementById(param);
    var elem_id = elem.id;
    elem.parentNode.removeChild(elem);
    var index = selected_experiments.indexOf(elem_id);
    selected_experiments.splice(index, 1);
    set_export_experiments_input_field();

    if (selected_experiments.length == 0) {
        document.getElementById('download').style.display = 'none';
    }
}

function set_export_experiments_input_field() {
    if(selected_experiments.length != 0) {
        document.getElementById('download_experiments').value = selected_experiments.join(',');
    } else {
        document.getElementById('download_experiments').value = "";
    }
}

function print_warning_message() {
    document.getElementById('warning_message').style.display = 'block'
}