
    $(document).ready(function () {
        var table = $('#exp_table').DataTable({
            scrollY: 600,
            scrollX: true,
            paging: false,
            dom: 'l<<"pull-left"B><"pull-right"f>r>t<<"pull-left"i><"pull-right"p>>',
            deferRender: true,
            columnDefs: [
                {
                    targets: 0,
                    orderable: false,
                    className: 'select-checkbox',
                },
                {
                    "targets": 1,
                    "visible": true,
                }
            ],
            select: {
                style: 'multi',
                selector: 'td:first-child'
            },
            order: [[1, 'asc']],
            buttons: [
                {
                    extend: 'collection',
                    text: 'Select',
                    buttons: ['selectAll', 'selectNone']
                },
                {
                    extend: 'collection',
                    text: 'Export',
                    buttons: [
                        {
                            text: 'Mutations',
                            action: function () {
                                export_data(table, 'mut');
                            }
                        },
                        {
                            text: 'Converged Mutations',
                            action: function () {
                                export_data(table, "converged_mut");
                            }
                        },
                        {
                            text: 'Fixed Mutations',
                            action: function () {
                                export_data(table, "fixed_mut")
                            }
                        },
                        {
                            text: 'Metadata',
                            action: function () {
                                export_metadata(table)
                            }
                        },
                    ]
                },
            ],
        });

    });


    function get_selected_experiment_ids(table) {
        var selected_data = table.rows('.selected').data();
        var experiment_ids = []
        for (var i = 0; i < selected_data.length; i++) {
            experiment_ids.push(selected_data[i][1])
        }
        return experiment_ids.join(",");
    }


    function export_data(table, mutation_type){
        exp_ids = get_selected_experiment_ids(table);
        if (exp_ids == ''){
            swal("", "Please select experiments and try again.", "warning");
            return;
        }
        var url = "/export";
        var params = {
                    'mut_type': mutation_type,
                    'project_id': project_id,
                    'experiment_ids': exp_ids
                };
        var form = $('<form method="GET" action="' + url + '">');
        $.each(params, function(k, v) {
            form.append($('<input type="hidden" name="' + k +
                    '" value="' + v + '">'));
        });
        $('body').append(form);
        form.submit();
    }

    function export_metadata(table){
        var exp_ids = get_selected_experiment_ids(table);
        if (exp_ids == ''){
            swal("", "Please select experiments and try again.", "warning");
            return;
        }
        var url = "/md_export";
        var params = {
                    'project_id': project_id,
                    'experiment_ids': exp_ids
                };
        var form = $('<form method="GET" action="' + url + '">');
        $.each(params, function(k, v) {
            form.append($('<input type="hidden" name="' + k +
                    '" value="' + v + '">'));
        });
        $('body').append(form);
        form.submit();
    }