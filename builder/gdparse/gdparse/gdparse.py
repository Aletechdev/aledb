#!/usr/bin/python
# -*- coding: latin-1 -*-
"""
Implements the GDParser class (that parses GenomeDiff files) and associated subroutines and exceptions.
Version compatible with Python3
"""

import re

EVIDENCE_TYPE_KEY = 'type'

MUTATION_KEY = 'mutation'

EVIDENCE_KEY = 'evidence'

VALIDATION_KEY = 'validation'

BRESEQ_VERSION_KEY = 'breseq_version'

RESEQ_TYPE_KEY = "reseq_type"  # population or clonal.

GENOMIC_DIFF_AUTHOR_KEY = "AUTHOR"

GENOMIC_DIFF_COMMAND_KEY = "COMMAND"

GENOMIC_DIFF_CREATED_KEY = "CREATED"

GENOMIC_DIFF_SEQ_REF_KEY = "REFSEQ"

PARENT_IDS_KEY = 'parent_ids'

MISSING_COVERAGE_EVIDENCE_TYPE = 'MC'

READ_ALIGNMENT_TYPE = 'RA'

JUNCTION_TYPE = 'JC'

UNKNOWN_BASE_TYPE = 'UN'

META_DATA_LINE_TAG = '#='

GENOME_DIFF_VERSION_TAG = "#=GENOME_DIFF"

MUTATION_TYPE_LIST = ['SNP', 'SUB', 'DEL', 'INS', 'MOB', 'AMP', 'CON', 'INV']

EVIDENCE_TYPE_LIST = [READ_ALIGNMENT_TYPE,
                      MISSING_COVERAGE_EVIDENCE_TYPE,
                      JUNCTION_TYPE,
                      UNKNOWN_BASE_TYPE]
VALIDATION_TYPE_LIST = ['TSEQ', 'PFLP', 'RFLP', 'PFGE', 'PHYL', 'CURA']

META_DATA_LINE_TAG_IDX = 0

META_DATA_LINE_FIELD_IDX = 1

BRESEQ_VERSION_INDEX = 1

BRESEQ_POPULATION_OPTION = "-p"


class SampleType:
    CLONAL = 0
    POPULATION = 1


class GDParseError(Exception):
    """
    Indicates a general or structural problem with the GD file not related to a particular field
    """

    def __init__(self, msg, inner_exception_msg=None):
        self.msg = msg

        self.inner_exception_msg = inner_exception_msg


class GDFieldError(GDParseError):
    """
    Indicates a problem encountered parsing a specific field
    """

    def __init__(self,
                 field_num,
                 field_name,
                 field_value,
                 msg,
                 inner_exception_msg=None):
        self.field_num = field_num
        self.field_name = field_name
        self.field_value = field_value
        self.msg = msg
        self.inner_exception_msg = inner_exception_msg


class GDParser():
    """
    Implements a parser that reads a GenomeDiff file and stores the information in two property dictionaries:

        metadata: a dictionary of key-value pairs
        data: a dictionary keyed by item class (mutation, evidence, validation) and then by item id.

    If passed a file handle (or other iterator) to a valid GenomeDiff file during initialization / construction,
    it will parse that on initialization. To parse a file after initialization, call the .populateFromFile()
    method.

    See http://barricklab.org/twiki/pub/Lab/ToolsBacterialGenomeResequencing/documentation/gd_format.html
        for GenomeDiff file format specification.
    """

    id2line_num = {}

    def __init__(self,
                 file_handle=None,
                 ignore_errors=False):
        """
        Constructor that populates the metadata and data properties from file_handle if given,
        otherwise initializes as blank.

        If ignore_errors is set to True, a parsing error will only cause the current line to
        be discarded, not the entire file.
        """

        self.meta_data = {}

        self.data = {MUTATION_KEY: {},
                     EVIDENCE_KEY: {},
                     VALIDATION_KEY: {}}

        self.valid_types = MUTATION_TYPE_LIST + EVIDENCE_TYPE_LIST + VALIDATION_TYPE_LIST

        if file_handle is not None:
            self.populate_from_file(file_handle, ignore_errors)

    @staticmethod
    def _smart_convert(data_string):
        """
        Attempts to convert a raw string into the following data types, returns the first successful:
            int, float, str
        """
        type_list = [int, float]
        for var_type in type_list:
            try:
                converted_var = var_type(data_string.strip())
                # Check for infinite values:
                if converted_var == float('Inf'):
                    converted_var = 1e6
                return converted_var
            except ValueError:
                pass
        # No match found
        return data_string.strip()

    @staticmethod
    def _is_genome_diff_header_appropriate(gd_version_line):
        is_genome_diff_header_appropriate = True
        header_str = gd_version_line[:len(GENOME_DIFF_VERSION_TAG)]
        if (header_str != GENOME_DIFF_VERSION_TAG):
            is_genome_diff_header_appropriate = False

        return is_genome_diff_header_appropriate

    def populate_from_file(self, file_handle, ignore_errors=False):
        """
        Reads a GenomeDiff format file line by line from a file_handle or other iterable,
        parsing the contents and storing them in two property dictionaries:

            metadata: a dictionary of key:value pairs for metadata variables

            data: a dictionary of all data entries, keyed by item class (mutation, evidence, validation)
                and then by item ID. Each item consists of all key:value pairs for that item,
                both defined and optional

        If ignore_errors is set to True, a parsing error will only cause the current line to
        be discarded, not the entire file.
        """

        # read version info
        gd_version_line = file_handle.readline()
        try:
            gd_version_line = gd_version_line.decode("utf-8")
        except:
            pass
        if not self._is_genome_diff_header_appropriate(gd_version_line):
            print(file_handle.name + " Invalid GenomeDiff file, header missing or malformed.")

        else:
            self._process_line(1, gd_version_line)
            for line_num, line in enumerate(file_handle.readlines()):
                try:
                    try:
                        line = line.decode("utf-8")
                    except:
                        pass
                    self._process_line(line_num, line)

                except GDFieldError as gd_file_field_error:

                    print(file_handle.name + " Parse error in field {}:{}, could not parse {}:".format(
                        gd_file_field_error.field_num,
                        gd_file_field_error.field_name,
                        gd_file_field_error.field_value))

                    print("Message: {}".format(gd_file_field_error.msg))

                    if gd_file_field_error.inner_exception_msg:
                        print(file_handle.name + " Exception: {}".format(gd_file_field_error.inner_exception_msg))

                    if not ignore_errors:
                        raise

                except GDParseError as gd_file_parse_error:

                    print(
                        file_handle.name + " There is an error in line {} of the GenomeDiff file.".format(line_num + 1))

                    print("Error returned: {}".format(gd_file_parse_error.msg))

                    if gd_file_parse_error.inner_exception_msg:
                        print("Exception: {}".format(gd_file_parse_error.inner_exception_msg))

                    if not ignore_errors:
                        raise

                except Exception as ex:
                    print(file_handle.name + " Unhandled exception on line {}:".format(line_num))
                    # print(ex.message)
                    raise

    def _parse_type_specific_fields(self, source_data, target_data, field_defs, start_field=3):
        """
        Parses a set of defined fields from a row of elements and updates a dictionary of named data elements.

        Returns the next field index after the processed ones.

        Parameters:
            source_data: a list of raw data elements
            target_data: reference to a dictionary which will be populated with fields from source_data
            field_defs: a list of dictionaries defining the fields.
                Required sub-fields:
                    name:    any valid string
                    type:    int, float, char, string
                Optional sub-fields:
                    allowed_values:    list that contains the values allowed in the field
                Optional sub-fields for string fields:
                    max_length:    integer describing the maximum allowed length.
                Optional sub-fields for numeric fields:
                    min_value:    number describing the maximum value allowed for a numeric field.
                    max_value:    number describing the minimum value allowed for a numeric field.
                    max_abs:    number describing the maximum absolute value allowed for a numeric field.
                    min_abs:    number describing the minimum absolute value allowed for a numeric field.
            start_field (optional): index of the first element in source_data to process (defaults to 3)
        """
        if len(source_data) < len(field_defs) + start_field:  # Check that we have enough fields to work with
            raise GDParseError("Premature line termination, needed at least {} fields, only got {}".format(
                len(field_defs) + start_field, len(source_data)))
        for field_idx, field in enumerate(source_data[start_field:start_field + len(field_defs)]):
            # Switch block for field type:
            if field_defs[field_idx]['type'] == 'string':
                try:
                    parsed_value = str(field)
                except ValueError as ve:
                    raise GDFieldError(field_idx + start_field, field_defs[field_idx]['name'], field,
                                       "Cannot convert to string", ve.message)

                if 'max_length' in field_defs[field_idx] and len(parsed_value) > field_defs[field_idx]['max_length']:
                    raise GDFieldError(field_idx + start_field, field_defs[field_idx]['name'], field,
                                       "Length of string field {} exceeds max length of {}".format(len(parsed_value),
                                                                                                   field_defs[
                                                                                                       field_idx][
                                                                                                       'max_length']))
            elif field_defs[field_idx]['type'] == 'char':
                try:
                    parsed_value = str(field)
                except ValueError as ve:
                    raise GDFieldError(field_idx + start_field, field_defs[field_idx]['name'], field,
                                       "Cannot convert to char", ve.message)
                if len(field) > 1:
                    raise GDFieldError(field_idx + start_field, field_defs[field_idx]['name'], field,
                                       "Char field must have length 1")
            elif field_defs[field_idx]['type'] in ('int',
                                                   'float'):  # group numeric fields into their own subgroup that can potentially have min/max checking
                if field_defs[field_idx]['type'] == 'int':
                    try:
                        parsed_value = int(field)
                    except ValueError as ve:
                        raise GDFieldError(field_idx + start_field, field_defs[field_idx]['name'], field,
                                           "Cannot convert to integer", ve.message)
                elif field_defs[field_idx]['type'] == 'float':
                    try:
                        parsed_value = float(field)
                    except ValueError as ve:
                        raise GDFieldError(field_idx + start_field, field_defs[field_idx]['name'], field,
                                           "Cannot convert to float", ve.message)
                if 'max_value' in field_defs[field_idx] and parsed_value > field_defs[field_idx]['max_value']:
                    raise GDFieldError(field_idx + start_field, field_defs[field_idx]['name'], field,
                                       "Value {} exceeds maximum allowable value of {}".format(parsed_value,
                                                                                               field_defs[field_idx][
                                                                                                   'max_value']))
                if 'min_value' in field_defs[field_idx] and parsed_value > field_defs[field_idx]['min_value']:
                    raise GDFieldError(field_idx + start_field, field_defs[field_idx]['name'], field,
                                       "Value {} below minimum allowable value of {}".format(parsed_value,
                                                                                             field_defs[field_idx][
                                                                                                 'min_value']))
                if 'max_abs' in field_defs[field_idx] and parsed_value > field_defs[field_idx]['max_abs']:
                    raise GDFieldError(field_idx + start_field, field_defs[field_idx]['name'], field,
                                       "Value {} exceeds maximum allowable absolute value of {}".format(parsed_value,
                                                                                                        field_defs[
                                                                                                            field_idx][
                                                                                                            'max_abs']))
                if 'min_abs' in field_defs[field_idx] and parsed_value > field_defs[field_idx]['min_abs']:
                    raise GDFieldError(field_idx + start_field, field_defs[field_idx]['name'], field,
                                       "Value {} below minimum allowable absolute value of {}".format(parsed_value,
                                                                                                      field_defs[
                                                                                                          field_idx][
                                                                                                          'min_abs']))
            if 'allowed_values' in field_defs[field_idx] and parsed_value not in field_defs[field_idx][
                'allowed_values']:
                raise GDFieldError(field_idx + start_field, field_defs[field_idx]['name'], field,
                                   "Value {} not permitted. Allowed values={}".format(parsed_value,
                                                                                      field_defs[field_idx][
                                                                                          'allowed_values']))
            target_data[field_defs[field_idx]['name']] = parsed_value
        return start_field + len(field_defs)

    @staticmethod
    def _is_meta_data_line(line):

        is_meta_data_line = False

        if line[:len(META_DATA_LINE_TAG)] == META_DATA_LINE_TAG:
            is_meta_data_line = True

        return is_meta_data_line

    @staticmethod
    def _get_meta_data_line_list(line):

        # Variable name and value are delineated by the first whitespace character
        meta_data_line_list = re.split('\s', line[2:], 1)

        return meta_data_line_list

    def _process_breseq_version(self, meta_data_field_string):

        meta_data_list = meta_data_field_string.split()

        breseq_version = meta_data_list[BRESEQ_VERSION_INDEX]

        self.meta_data[BRESEQ_VERSION_KEY] = breseq_version

    def _process_clonal_or_population(self, meta_data_field_string):
        meta_data_field_list = meta_data_field_string.split()
        if BRESEQ_POPULATION_OPTION in meta_data_field_list:
            self.meta_data[RESEQ_TYPE_KEY] = SampleType.POPULATION
        else:
            self.meta_data[RESEQ_TYPE_KEY] = SampleType.CLONAL

    def _process_meta_data(self, line):
        meta_data_line_list = self._get_meta_data_line_list(line)
        meta_data_tag = meta_data_line_list[META_DATA_LINE_TAG_IDX].strip()
        meta_data_field = meta_data_line_list[META_DATA_LINE_FIELD_IDX].strip()
        if meta_data_tag in self.meta_data.keys():
            if type(self.meta_data[meta_data_tag]) == 'list':
                self.meta_data[meta_data_tag].append(meta_data_field)
            else:
                self.meta_data[meta_data_tag] = [meta_data_field, self.meta_data[meta_data_tag]]
        else:
            self.meta_data[meta_data_tag] = meta_data_field
        if meta_data_field:
            if meta_data_tag == GENOMIC_DIFF_AUTHOR_KEY:
                self._process_breseq_version(meta_data_field)
            if meta_data_tag == GENOMIC_DIFF_COMMAND_KEY:
                self._process_clonal_or_population(meta_data_field)

    @staticmethod
    def _is_comment_line(line):
        is_comment_line = re.match('[#\s]', line[0])
        return is_comment_line

    def _process_line(self, line_num, line):
        """
        Processes each line of the file and either stores the information in the appropriate
            property dictionary (metadata, data) or does nothing (comment).

        returns None
        """

        if self._is_meta_data_line(line):
            self._process_meta_data(line)

        elif not self._is_comment_line(line):

            # this must be a data line
            new_data = {}
            data_elements = re.split('\t', line.strip())  # data lines are tab-delimited

            # Field 1: type <string>
            # type of the entry on this line.
            if data_elements[0] in MUTATION_TYPE_LIST:  # test for validity of type and assign the correct class:
                item_class = MUTATION_KEY
            elif data_elements[0] in EVIDENCE_TYPE_LIST:
                item_class = EVIDENCE_KEY
            elif data_elements[0] in VALIDATION_TYPE_LIST:
                item_class = VALIDATION_KEY
            else:
                raise GDFieldError(1, 'type', data_elements[0], "Invalid entry type")
            new_data['type'] = data_elements[0]

            # Field 2: id or evidence-id <uint32>
            # For evidence and validation lines, the id of this item. For mutation lines, the ids of all evidence or validation items that support this mutation. May be set to "." if a line was manually edited.
            try:
                item_id = int(data_elements[1])
                self.id2line_num[item_id] = line_num
            except ValueError as ve:  # check that it's an integer:
                raise GDFieldError(2, 'id', data_elements[1], "Cannot convert to integer", ve.message)

            # Field 3: parent-ids <uint32>
            # ids of evidence that support this mutation. May be set to "." or left blank.
            if data_elements[2] != '':
                if item_class == MUTATION_KEY or item_class == EVIDENCE_KEY:
                    if data_elements[2] == '.':
                        new_data[PARENT_IDS_KEY] = 'manual'
                    else:
                        try:
                            # Store the evidence ids as a list of ints
                            # and later check that they are valid once all the ids are loaded
                            new_data[PARENT_IDS_KEY] = [int(element) for element in data_elements[2].split(',')]
                        except ValueError as ve:
                            raise GDFieldError(2, PARENT_IDS_KEY, data_elements[2],
                                               "Cannot convert an element of parent_ids to integer", ve.message)
                else:
                    # we have a non-blank evidence field for something that isn't a mutation. Not good.
                    raise GDFieldError(3, PARENT_IDS_KEY, data_elements[2],
                                       "Parent ID references only valid for mutation entries")

            # ===============================================================
            # Content and length of next set of fields varies by class and type
            # ===============================================================

            # construct a list of field definitions to pass to a sub-parser
            field_list = []

            if new_data['type'] == 'SNP':  # Base substitution mutation
                # Field 4: seq_id <string>
                # id of reference sequence fragment containing mutation, evidence, or validation.
                field_list.append({'name': 'seq_id', 'type': 'string'})
                # Field 5: position <uint32>
                # position in reference sequence fragment.
                field_list.append({'name': 'position', 'type': 'int'})
                # Field 6: new_seq <char>
                # new base at position
                field_list.append({'name': 'new_seq', 'type': 'char'})
                # ------------------------------------------------------------------------------
                next_field = self._parse_type_specific_fields(data_elements, new_data, field_list, 3)
                # ------------------------------------------------------------------------------
            elif new_data['type'] == 'SUB':  # Multiple base substitution mutation
                # Field 4: seq_id <string>
                # id of reference sequence fragment containing mutation, evidence, or validation.
                field_list.append({'name': 'seq_id', 'type': 'string'})
                # Field 5: position <uint32>
                # position of the first replaced nucleotide in reference sequence fragment.
                field_list.append({'name': 'position', 'type': 'int'})
                # Field 6: size <uint32>
                # number of bases after the specified reference position to replace with new_seq
                field_list.append({'name': 'size', 'type': 'int'})
                # Field 7: new_seq <string>
                # new bases at position
                field_list.append({'name': 'new_seq', 'type': 'string'})
                # ------------------------------------------------------------------------------
                next_field = self._parse_type_specific_fields(data_elements, new_data, field_list, 3)
                # ------------------------------------------------------------------------------
            elif new_data['type'] == 'DEL':  # Deletion mutation
                # Field 4: seq_id <string>
                # id of reference sequence fragment containing mutation, evidence, or validation.
                field_list.append({'name': 'seq_id', 'type': 'string'})
                # Field 5: position <uint32>
                # position in reference sequence fragment.
                field_list.append({'name': 'position', 'type': 'int'})
                # Field 6: size <uint32>
                # number of bases deleted in reference, including reference position.
                field_list.append({'name': 'size', 'type': 'int'})
                # ------------------------------------------------------------------------------
                next_field = self._parse_type_specific_fields(data_elements, new_data, field_list, 3)
                # ------------------------------------------------------------------------------
            elif new_data['type'] == 'INS':  # Insertion mutation
                # Field 4: seq_id <string>
                # id of reference sequence fragment containing mutation, evidence, or validation.
                field_list.append({'name': 'seq_id', 'type': 'string'})
                # Field 5: position <uint32>
                # position in reference sequence fragment, after which the INS is placed.
                field_list.append({'name': 'position', 'type': 'int'})
                # Field 6: new_seq <string>
                # new bases inserted after the specified reference position
                field_list.append({'name': 'new_seq', 'type': 'string'})
                # ------------------------------------------------------------------------------
                next_field = self._parse_type_specific_fields(data_elements, new_data, field_list, 3)
                # ------------------------------------------------------------------------------
            elif new_data['type'] == 'MOB':  # Mobile element insertion mutation
                # Field 4: seq_id <string>
                # id of reference sequence fragment containing mutation, evidence, or validation.
                field_list.append({'name': 'seq_id', 'type': 'string'})
                # Field 5: position <uint32>
                # position in reference sequence fragment.
                field_list.append({'name': 'position', 'type': 'int'})
                # Field 6: repeat_name <string>
                # name of the mobile element. Should correspond to an annotated repeat_region in the reference.
                field_list.append({'name': 'repeat_name', 'type': 'string'})
                # Field 7: strand <1/-1>
                # strand of mobile element insertion.
                field_list.append({'name': 'strand', 'type': 'int', 'allowable_values': [-1, 1]})
                # Field 8: duplication_size <uint32>
                # number of bases duplicated during insertion, beginning with the specified reference position.
                field_list.append({'name': 'duplication_size', 'type': 'int'})
                # ------------------------------------------------------------------------------
                next_field = self._parse_type_specific_fields(data_elements, new_data, field_list, 3)
                # ------------------------------------------------------------------------------
            elif new_data['type'] == 'AMP':  # Amplification Mutation
                # Field 4: seq_id <string>
                # id of reference sequence fragment containing mutation, evidence, or validation.
                field_list.append({'name': 'seq_id', 'type': 'string'})
                # Field 5: position <uint32>
                # position in reference sequence fragment.
                field_list.append({'name': 'position', 'type': 'int'})
                # Field 6: size <uint32>
                # number of bases duplicated starting with the specified reference position.
                field_list.append({'name': 'size', 'type': 'int'})
                # Field 7: new_copy_number <uint32>
                # new number of copies of specified bases.
                field_list.append({'name': 'new_copy_number', 'type': 'int'})
                # ------------------------------------------------------------------------------
                next_field = self._parse_type_specific_fields(data_elements, new_data, field_list, 3)
                # ------------------------------------------------------------------------------
            elif new_data['type'] == 'CON':  # Gene conversion mutation
                # Field 4: seq_id <string>
                # id of reference sequence fragment containing mutation, evidence, or validation.
                field_list.append({'name': 'seq_id', 'type': 'string'})
                # Field 5: position <uint32>
                # position in reference sequence fragment that was the target of gene conversion from another genomic location.
                field_list.append({'name': 'position', 'type': 'int'})
                # Field 6: size <uint32>
                # number of bases to replace in the reference genome beginning at the specified position.
                field_list.append({'name': 'size', 'type': 'int'})
                # Field 7: region <sequence:start-end>
                # region in the reference genome to use as a replacement.
                field_list.append({'name': 'region', 'type': 'string'})
                # ------------------------------------------------------------------------------
                next_field = self._parse_type_specific_fields(data_elements, new_data, field_list, 3)
                # ------------------------------------------------------------------------------
            elif new_data['type'] == 'INV':  # Inversion mutation
                # Field 4: seq_id <string>
                # id of reference sequence fragment containing mutation, evidence, or validation.
                field_list.append({'name': 'seq_id', 'type': 'string'})
                # Field 5: position <uint32>
                # position in reference sequence fragment.
                field_list.append({'name': 'position', 'type': 'int'})
                # Field 6: size <uint32>
                # number of bases in inverted region beginning at the specified reference position.
                field_list.append({'name': 'size', 'type': 'int'})
                # ------------------------------------------------------------------------------
                next_field = self._parse_type_specific_fields(data_elements, new_data, field_list, 3)
                # ------------------------------------------------------------------------------
            elif new_data['type'] == 'RA':  # Read alignment evidence
                # Field 4: seq_id <string>
                # id of reference sequence fragment containing mutation, evidence, or validation.
                field_list.append({'name': 'seq_id', 'type': 'string'})
                # Field 5: position <uint32>
                # position in reference sequence fragment.
                field_list.append({'name': 'position', 'type': 'int'})
                # Field 6: insert_position <uint32>
                # number of bases inserted after the reference position to get to this base. An value of zero refers to the base. A value of 5 means that this evidence if for the fifth newly inserted column after the reference position.
                field_list.append({'name': 'insert_position', 'type': 'int'})
                # Field 7: ref_base <char>
                # base in the reference genome.
                field_list.append({'name': 'ref_base', 'type': 'char'})
                # Field 8: new_base <char>
                # new base supported by read alignment evidence.
                field_list.append({'name': 'new_base', 'type': 'char'})
                # ------------------------------------------------------------------------------
                next_field = self._parse_type_specific_fields(data_elements, new_data, field_list, 3)
                # ------------------------------------------------------------------------------
            elif new_data['type'] == 'MC':  # Missing coverage evidence
                # Field 4: seq_id <string>
                # id of reference sequence fragment containing mutation, evidence, or validation.
                field_list.append({'name': 'seq_id', 'type': 'string'})
                # Field 5: start <uint32>
                # start position in reference sequence fragment.
                field_list.append({'name': 'start', 'type': 'int'})
                # Field 6: end <uint32>
                # end position in reference sequence of region.
                field_list.append({'name': 'end', 'type': 'int'})
                # Field 7: start_range <uint32>
                # number of bases to offset after the start position to define the upper limit of the range where the start of a deletion could be.
                field_list.append({'name': 'start_range', 'type': 'int'})
                # Field 8: end_range <uint32>
                # number of bases to offset before the end position to define the lower limit of the range where the start of a deletion could be.
                field_list.append({'name': 'end_range', 'type': 'int'})
                # ------------------------------------------------------------------------------
                next_field = self._parse_type_specific_fields(data_elements, new_data, field_list, 3)
                # ------------------------------------------------------------------------------
            elif new_data['type'] == 'JC':  # New junction evidence
                # Field 4: side_1_seq_id <string>
                # id of reference sequence fragment containing side 1 of the junction.
                field_list.append({'name': 'side_1_seq_id', 'type': 'string'})
                # Field 5: side_1_position <uint32>
                # position of side 1 at the junction boundary.
                field_list.append({'name': 'side_1_position', 'type': 'int'})
                # Field 6: side_1_strand <1/-1>
                # direction that side 1 continues matching the reference sequence
                field_list.append({'name': 'side_1_strand', 'type': 'int', 'allowable_values': [-1, 1]})
                # Field 7: side_2_seq_id <string>
                # id of reference sequence fragment containing side 2 of the junction.
                field_list.append({'name': 'side_2_seq_id', 'type': 'string'})
                # Field 8: side_2_position <uint32>
                # position of side 2 at the junction boundary.
                field_list.append({'name': 'side_2_position', 'type': 'int'})
                # Field 9: side_2_strand <1/-1>
                # direction that side 2 continues matching the reference sequence
                field_list.append({'name': 'side_2_strand', 'type': 'int', 'allowable_values': [-1, 1]})
                # Field 10: overlap <uint32>
                # number of bases that the two sides of the new junction have in common.
                field_list.append({'name': 'overlap', 'type': 'int'})
                # ------------------------------------------------------------------------------
                next_field = self._parse_type_specific_fields(data_elements, new_data, field_list, 3)
                # ------------------------------------------------------------------------------
            elif new_data['type'] == 'UN':  # Unknown base evidence
                # Field 4: seq_id <string>
                # id of reference sequence fragment containing mutation, evidence, or validation.
                field_list.append({'name': 'seq_id', 'type': 'string'})
                # Field 5: start <uint32>
                # start position in reference sequence fragment.
                field_list.append({'name': 'start', 'type': 'int'})
                # Field 6: end <uint32>
                # end position in reference sequence of region.
                field_list.append({'name': 'end', 'type': 'int'})
                # ------------------------------------------------------------------------------
                next_field = self._parse_type_specific_fields(data_elements, new_data, field_list, 3)
                # ------------------------------------------------------------------------------
            elif new_data['type'] == 'CURA':  # True-positive curated by an expert
                # An expert has examined the data output from a prediction program and determined that this mutations is a true positive.
                # Field 4: expert <string>
                # Name or initials of the person who predicted the mutation.
                field_list.append({'name': 'expert', 'type': 'string'})
                # ------------------------------------------------------------------------------
                next_field = self._parse_type_specific_fields(data_elements, new_data, field_list, 3)
                # ------------------------------------------------------------------------------
            elif new_data['type'] == 'FPOS':  # False-positive curated by an expert
                # An expert has examined the raw read data and determined that this predicted mutation is a false positive.
                # Field 4: expert <string>
                # Name or initials of the person who predicted the mutation.
                field_list.append({'name': 'expert', 'type': 'string'})
                # ------------------------------------------------------------------------------
                next_field = self._parse_type_specific_fields(data_elements, new_data, field_list, 3)
                # ------------------------------------------------------------------------------
            elif new_data['type'] == 'PHYL':  # Phylogenetic comparison
                # This validation was transferred from validation in another, related genome.
                # Field 4: gd <string>
                # Name of the genome_diff file containing the evidence.
                field_list.append({'name': 'gd', 'type': 'string'})
                # ------------------------------------------------------------------------------
                next_field = self._parse_type_specific_fields(data_elements, new_data, field_list, 3)
                # ------------------------------------------------------------------------------
            elif new_data['type'] == 'TSEQ':  # Targeted resequencing
                # Field 4: seq_id <string>
                # id of reference sequence fragment containing mutation, evidence, or validation.
                field_list.append({'name': 'seq_id', 'type': 'string'})
                # Field 5: primer1_start <uint32>
                # position in reference sequence of the 5' end of primer 1.
                field_list.append({'name': 'primer1_start', 'type': 'int'})
                # Field 6: primer1_end <uint32>
                # position in reference sequence of the 3' end of primer 1.
                field_list.append({'name': 'primer1_end', 'type': 'int'})
                # Field 7: primer2_start <uint32>
                # position in reference sequence of the 5' end of primer 2.
                field_list.append({'name': 'primer2_start', 'type': 'int'})
                # Field 8: primer2_end <uint32>
                # position in reference sequence of the 3' end of primer 2.
                field_list.append({'name': 'primer2_end', 'type': 'int'})
                # ------------------------------------------------------------------------------
                next_field = self._parse_type_specific_fields(data_elements, new_data, field_list, 3)
                # ------------------------------------------------------------------------------
                if new_data['primer1_start'] >= new_data['primer1_end']:
                    raise GDFieldError(6, 'primer1_end', new_data['primer1_end'],
                                       "Primer 1 end location {} must be > primer start location {}".format(
                                           new_data['primer1_end'], new_data['primer1_start']))
                if new_data['primer2_start'] >= new_data['primer2_end']:
                    raise GDFieldError(8, 'primer2_end', new_data['primer2_end'],
                                       "Primer 2 end location {} must be > primer start location {}".format(
                                           new_data['primer2_end'], new_data['primer2_start']))
            elif new_data['type'] == 'PFLP':  # PCR-fragment length polymorphism
                # Field 4: seq_id <string>
                # id of reference sequence fragment containing mutation, evidence, or validation.
                field_list.append({'name': 'seq_id', 'type': 'string'})
                # Field 5: primer1_start <uint32>
                # position in reference sequence of the 5' end of primer 1.
                field_list.append({'name': 'primer1_start', 'type': 'int'})
                # Field 6: primer1_end <uint32>
                # position in reference sequence of the 3' end of primer 1.
                field_list.append({'name': 'primer1_end', 'type': 'int'})
                # Field 7: primer2_start <uint32>
                # position in reference sequence of the 5' end of primer 2.
                field_list.append({'name': 'primer2_start', 'type': 'int'})
                # Field 8: primer2_end <uint32>
                # position in reference sequence of the 3' end of primer 2.
                field_list.append({'name': 'primer2_end', 'type': 'int'})
                # ------------------------------------------------------------------------------
                next_field = self._parse_type_specific_fields(data_elements, new_data, field_list, 3)
                # ------------------------------------------------------------------------------
                if new_data['primer1_start'] >= new_data['primer1_end']:
                    raise GDFieldError(6, 'primer1_end', new_data['primer1_end'],
                                       "Primer 1 end location {} must be > primer start location {}".format(
                                           new_data['primer1_end'], new_data['primer1_start']))
                if new_data['primer2_start'] >= new_data['primer2_end']:
                    raise GDFieldError(8, 'primer2_end', new_data['primer2_end'],
                                       "Primer 2 end location {} must be > primer start location {}".format(
                                           new_data['primer2_end'], new_data['primer2_start']))
            elif new_data['type'] == 'RFLP':  # Restriction fragment length polymorphism
                # Field 4: seq_id <string>
                # id of reference sequence fragment containing mutation, evidence, or validation.
                field_list.append({'name': 'seq_id', 'type': 'string'})
                # Field 5: primer1_start <uint32>
                # position in reference sequence of the 5' end of primer 1.
                field_list.append({'name': 'primer1_start', 'type': 'int'})
                # Field 6: primer1_end <uint32>
                # position in reference sequence of the 3' end of primer 1.
                field_list.append({'name': 'primer1_end', 'type': 'int'})
                # Field 7: primer2_start <uint32>
                # position in reference sequence of the 5' end of primer 2.
                new_data['primer2_start'] = int(data_elements[6])
                # Field 8: primer2_end <uint32>
                # position in reference sequence of the 3' end of primer 2.
                field_list.append({'name': 'primer2_start', 'type': 'int'})
                # Field 9: enzyme <string>
                # Restriction enzyme used to distinguish reference from mutated allele.
                field_list.append({'name': 'enzyme', 'type': 'string'})
                # ------------------------------------------------------------------------------
                next_field = self._parse_type_specific_fields(data_elements, new_data, field_list, 3)
                # ------------------------------------------------------------------------------
                if new_data['primer1_start'] >= new_data['primer1_end']:
                    raise GDFieldError(6, 'primer1_end', new_data['primer1_end'],
                                       "Primer 1 end location {} must be > primer start location {}".format(
                                           new_data['primer1_end'], new_data['primer1_start']))
                if new_data['primer2_start'] >= new_data['primer2_end']:
                    raise GDFieldError(8, 'primer2_end', new_data['primer2_end'],
                                       "Primer 2 end location {} must be > primer start location {}".format(
                                           new_data['primer2_end'], new_data['primer2_start']))
            elif new_data['type'] == 'PFGE':  # Pulsed-field gel electrophoresis
                # Changes in fragment sizes of genomic DNA digested with restriction enzymes and separated by pulsed-field
                # Field 4: seq_id <string>
                # id of reference sequence fragment containing mutation, evidence, or validation.
                field_list.append({'name': 'seq_id', 'type': 'string'})
                # Field 5: enzyme <string>
                # Restriction enzyme used to digest genomic DNA and observe fragments.
                field_list.append({'name': 'enzyme', 'type': 'string'})
                # ------------------------------------------------------------------------------
                next_field = self._parse_type_specific_fields(data_elements, new_data, field_list, 3)
                # ------------------------------------------------------------------------------
            elif new_data['type'] == 'NOTE':  # Note
                # Generic container for a note about a mutation prediction
                # Field 4: note <string>
                # Free text note.
                field_list.append({'name': 'note', 'type': 'string'})
                # ------------------------------------------------------------------------------
                next_field = self._parse_type_specific_fields(data_elements, new_data, field_list, 3)
                # ------------------------------------------------------------------------------
            else:
                raise GDFieldError(1, 'type', data_elements[0], "Invalid entry type")

            # =================================================
            # Process any optional key=value pairs
            # =================================================
            for field_idx in range(next_field, len(data_elements)):
                split_field = data_elements[field_idx].split('=')
                if len(split_field) > 1:
                    key = split_field[0].strip()
                    value = self._smart_convert(split_field[1].strip())
                    new_data[key] = value
            # Insert the dictionary for the new item into the class data dictionary, keyed by id.
            self.data[item_class][item_id] = new_data
