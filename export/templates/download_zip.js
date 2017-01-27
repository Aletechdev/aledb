/**
 * Created by dgosting on 1/27/17.
 */
// CSV: https://github.com/knrz/CSV.js/

var zip = new JSZip();

var output_sample_name_array = [];

for (var i = 0; i < data.length; i++) {

    var exp_data = data[i];

    var file_name = exp_data[1] + '.csv';
    var csv_data = exp_data[0];
    output_sample_name_array.push([file_name]);

    var output_sample_csv_data = [new CSV(csv_data).encode()];
    var output_sample_metadata_file = new Blob(output_sample_csv_data, { type: 'text/plain;charset=utf-8' });
    zip.folder("samples").file(file_name, output_sample_metadata_file)
}


zip.generateAsync({type:"blob"})
.then(function (blob) {
  saveAs(blob, 'download' + '.zip')
});