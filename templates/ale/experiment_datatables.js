
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
                    ]
                },
            ],
        });

    });


    function get_selected_experiment_ids(table) {
        var selected_data = table.rows('.selected').data();
        var exp_ids = '';
        for (var i = 0; i < selected_data.length; i++) {
            exp_ids += selected_data[i][1] + ",";
        }
        return exp_ids;
    }

    function download_zip(data) {
        var zip = new JSZip();

        var output_sample_name_array = [];

        for (var i = 0; i < data.length; i++) {

            var exp_data = data[i];

            var file_name = exp_data[0] + '.csv';
            var csv_data = exp_data[1];
            output_sample_name_array.push([file_name]);

            var output_sample_csv_data = [new CSV(csv_data).encode()];
            var output_sample_metadata_file = new Blob(output_sample_csv_data, { type: 'text/plain;charset=utf-8' });
            zip.folder("samples").file(file_name, output_sample_metadata_file)
        }


        zip.generateAsync({type:"blob"})
        .then(function (blob) {
          saveAs(blob, 'download' + '.zip')
        });
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
