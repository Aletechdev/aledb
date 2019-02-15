#! /usr/local/bin/python3.6

import sys
import csv
import os
import json
from jsonschema import Draft4Validator

def is_valid(csv_directory_path, schema_file_path):

    Valdation = True

    with open(schema_file_path, "r") as j:
        schema = json.load(j)

    for filename in os.listdir(csv_directory_path):
        if filename.endswith(".csv"):

            csvfile = os.path.splitext(filename)[0]

            transpose = zip(*csv.reader(open(csv_directory_path + "/" + csvfile +'.csv', "r")))
            csv.writer(open("transposedFile.csv", "w")).writerows(transpose)

            with open("transposedFile.csv") as f:
                reader = csv.DictReader(f)
                rows = list(reader)


            jsonobj = json.dumps(rows)
            jsonarray = json.loads(jsonobj)

            validator = Draft4Validator(schema)
            

            if (len(sorted(validator.iter_errors(jsonarray), key=str))) > 0:
                with open(filename +'-XMPD_ValidatorLOGFILE.txt', 'w') as f:
                    Valdation = False

                    print("ERROR - Metadata File " + filename + " Does not Pass Valdation. Error Logfile generated.")
                    orig_stdout = sys.stdout
                    sys.stdout = f
                    i=0

                    print("Please fix all errors below for Metadata File " + filename + " in order to run file on ALE mutation Pipeline")

                    for error in sorted(validator.iter_errors(jsonarray), key=str):
                        i+=1
                        if error.validator == "pattern":
                            if ((error.path[1] == 'ALE-number') or (error.path[1] == 'Flask-number') or (error.path[1] == 'Isolate-number') or
                                (error.path[1] == 'technical-replicate-number') or (error.path[1] == 'sample-time') or (error.path[1] == "temperature(Celcius")):
                                print('['+str(i)+'] - ' + 'Invalid input, numerical value only for field: ' + error.path[1])
                            else:
                                print('['+str(i)+'] - ' +'Invalid input for field: ' + error.path[1])
                        

                        if error.validator == "enum":
                            print('['+str(i)+'] - Field: ' + str(error.path[1]) + ", " + error.message)

                        if error.validator == "required":
                            print('['+str(i)+'] - ' + error.message)

                        elif (error.validator == "required") and (error.validator == "enum") and (error.validator == "pattern"):
                            print('['+str(i)+'] - ' + error.message)

                    sys.stdout.close()
                    sys.stdout=orig_stdout

     
    try:
        os.remove("transposedFile.csv")
    except OSError:
        pass

    if Valdation == True:
        print("Metadata Files Validated! [Proceed]")
        return True
    elif Valdation == False:
        return False

if __name__ == '__main__':

    if len(sys.argv) < 3:
        print('Input CSVfile directory followed by JsonSchemaFile directory')
        sys.exit()

    csv_directory_path = sys.argv[1]
    schema_file_path = sys.argv[2]

    is_valid(csv_directory_path, schema_file_path)
