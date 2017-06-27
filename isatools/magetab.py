from isatools import isatab
import tempfile

from isatools.isatab import get_squashed
from .model.v1 import *
import os
import logging
import csv
import numpy as np
import pandas as pd
from io import StringIO
from itertools import zip_longest
import re


logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_sdrf_filenames(ISA):
    sdrf_filenames = []
    for study in ISA.studies:
        for assay in [x for x in study.assays if x.technology_type.term.lower() == "dna microarray"]:
            sdrf_filenames.append(study.filename[2:-3] + assay.filename[2:-3] + "sdrf.txt")
    return sdrf_filenames


def _build_metadata_df(ISA):
    metadata_df = pd.DataFrame(columns=(
        "MAGE-TAB Version",
        "Investigation Title",
        "Public Release Date",
        "SDRF File"
    ))
    sdrf_filenames = _get_sdrf_filenames(ISA)
    metadata_df.loc[0] = [
        "1.1",
        ISA.title,
        ISA.public_release_date,
        sdrf_filenames[0]
    ]
    for i, sdrf_filename in enumerate(sdrf_filenames):
        if i == 0:
            pass
        else:
            metadata_df.loc[i] = [
                "",
                "",
                "",
                sdrf_filename
            ]
    return metadata_df


def _build_exp_designs_df(ISA):
    exp_designs_df = pd.DataFrame(columns=(
        "Experimental Design",
        "Experimental Design Term Source REF",
        "Experimental Design Term Accession Number"))
    microarray_study_design = []
    for study in ISA.studies:
        if len([x for x in study.assays if x.technology_type.term.lower() == "dna microarray"]) > 0:
            microarray_study_design.extend(study.design_descriptors)
    for i, design_descriptor in enumerate(microarray_study_design):
        exp_designs_df.loc[i] = [
            design_descriptor.term,
            design_descriptor.term_source.name,
            design_descriptor.term_accession
        ]
    return exp_designs_df


def _build_exp_factors_df(ISA):
    exp_factors_df = pd.DataFrame(columns=(
        "Experimental Factor Name",
        "Experimental Factor Type",
        "Experimental Factor Term Source REF",
        "Experimental Factor Term Accession Number"))
    microarray_study_factors = []
    for study in ISA.studies:
        if len([x for x in study.assays if x.technology_type.term.lower() == "dna microarray"]) > 0:
            microarray_study_factors.extend(study.factors)
    for i, factor in enumerate(microarray_study_factors):
        exp_factors_df.loc[i] = [
            factor.name,
            factor.factor_type.term,
            factor.factor_type.term_source.name if factor.factor_type.term_source else "",
            factor.factor_type.term_accession if factor.factor_type.term_source else ""
        ]
    return exp_factors_df


def _build_roles_str(roles):
    if roles is None:
        roles = list()
    roles_names = ''
    roles_accession_numbers = ''
    roles_source_refs = ''
    for role in roles:
        roles_names += (role.term if role.term else '') + ';'
        roles_accession_numbers += (role.term_accession if role.term_accession else '') + ';'
        roles_source_refs += (role.term_source.name if role.term_source else '') + ';'
    if len(roles) > 0:
        roles_names = roles_names[:-1]
        roles_accession_numbers = roles_accession_numbers[:-1]
        roles_source_refs = roles_source_refs[:-1]
    return roles_names, roles_accession_numbers, roles_source_refs


def _build_people_df(ISA):
    people_df = pd.DataFrame(columns=("Person Last Name",
                                      "Person Mid Initials",
                                      "Person First Name",
                                      "Person Email",
                                      "Person Phone",
                                      "Person Fax",
                                      "Person Address",
                                      "Person Affiliation",
                                      "Person Roles",
                                      "Person Roles Term Source REF",
                                      "Person Roles Term Accession Number"))
    for i, contact in enumerate(ISA.contacts):
        roles_names, roles_accessions, roles_sources = _build_roles_str(contact.roles)
        people_df.loc[i] = [
            contact.last_name,
            contact.mid_initials,
            contact.first_name,
            contact.email,
            contact.phone,
            contact.fax,
            contact.address,
            contact.affiliation,
            roles_names,
            roles_sources,
            roles_accessions
        ]
    return people_df


def _build_protocols_df(ISA):
    protocols_df = pd.DataFrame(columns=('Protocol Name',
                                         'Protocol Type',
                                         'Protocol Term Accession Number',
                                         'Protocol Term Source REF',
                                         'Protocol Description',
                                         'Protocol Parameters',
                                         'Protocol Hardware',
                                         'Protocol Software',
                                         'Protocol Contact'
                                         )
                                )
    microarray_study_protocols = []
    for study in ISA.studies:
        if len([x for x in study.assays if x.technology_type.term.lower() == "dna microarray"]) > 0:
            microarray_study_protocols.extend(study.protocols)
    for i, protocol in enumerate(microarray_study_protocols):
        parameters_names = ''
        parameters_accession_numbers = ''
        parameters_source_refs = ''
        for parameter in protocol.parameters:
            parameters_names += parameter.parameter_name.term + ';'
            parameters_accession_numbers += (
                                            parameter.parameter_name.term_accession if parameter.parameter_name.term_accession is not None else '') + ';'
            parameters_source_refs += (
                                      parameter.parameter_name.term_source.name if parameter.parameter_name.term_source else '') + ';'
        if len(protocol.parameters) > 0:
            parameters_names = parameters_names[:-1]
        if protocol.protocol_type:
            protocol_type_term = protocol.protocol_type.term
            protocol_type_term_accession = protocol.protocol_type.term_accession
            if protocol.protocol_type.term_source:
                protocol_type_term_source_name = protocol.protocol_type.term_source.name
                protocols_df.loc[i] = [
                    protocol.name,
                    protocol_type_term,
                    protocol_type_term_accession,
                    protocol_type_term_source_name,
                    protocol.description,
                    parameters_names,
                    "",
                    "",
                    ""
                ]
    return protocols_df


def _build_term_sources_df(ISA):
    term_sources_df = pd.DataFrame(columns=("Term Source Name", "Term Source File", "Term Source Version"))
    for i, term_source in enumerate(ISA.ontology_source_references):
        term_sources_df.loc[i] = [
            term_source.name,
            term_source.file,
            term_source.version
        ]
    return term_sources_df


def _build_publications_df(ISA):
    publications = ISA.studies[0].publications
    publications_df_cols = ['PubMed ID',
                            'Publication DOI',
                            'Publication Author List',
                            'Publication Title',
                            'Publication Status',
                            'Publication Status Term Accession Number',
                            'Publication Status Term Source REF']
    if len(publications) > 0:
        try:
            for comment in publications[0].comments:
                publications_df_cols.append('Comment[' + comment.name + ']')
        except TypeError:
            pass
    publications_df = pd.DataFrame(columns=tuple(publications_df_cols))
    for i, publication in enumerate(publications):
        if publication.status is not None:
            status_term = publication.status.term
            status_term_accession = publication.status.term_accession
            if publication.status.term_source is not None:
                status_term_source_name = publication.status.term_source.name
            else:
                status_term_source_name = ''
        else:
            status_term = ''
            status_term_accession = ''
            status_term_source_name = ''
        publications_df_row = [
            publication.pubmed_id,
            publication.doi,
            publication.author_list,
            publication.title,
            status_term,
            status_term_accession,
            status_term_source_name,
        ]
        try:
            for comment in publication.comments:
                publications_df_row.append(comment.value)
        except TypeError:
            pass
        publications_df.loc[i] = publications_df_row
    return publications_df


def _build_qc_df(ISA):
    qc_df = pd.DataFrame(columns=(
        "Quality Control Type",
        "Quality Control Term Accession Number",
        "Quality Control Term Source REF"))
    for i, qc_comment in enumerate([x for x in ISA.studies[0].comments if x.name == "Quality Control Type"]):
        qc_df.loc[i] = [
            qc_comment.value,
            "",
            ""
        ]
    return qc_df


def _build_replicates_df(ISA):
    replicates_df = pd.DataFrame(columns=(
        "Replicate Type",
        "Replicate Term Accession Number",
        "Replicate Term Source REF"))
    for i, replicate_comment in enumerate([x for x in ISA.studies[0].comments if x.name == "Replicate Type"]):
        replicates_df.loc[i] = [
            replicate_comment.value,
            "",
            ""
        ]
    return replicates_df


def _build_normalizations_df(ISA):
    normalizations_df = pd.DataFrame(columns=(
        "Normalization Type",
        "Normalization Term Accession Number",
        "Normalization Term Source REF"))
    for i, normalization_comment in enumerate([x for x in ISA.studies[0].comments if x.name == "Normalization Type"]):
        normalizations_df.loc[i] = [
            normalization_comment.value,
            "",
            ""
        ]
    return normalizations_df


def write_idf_file(inv_obj, output_path):
    investigation = inv_obj
    metadata_df = _build_metadata_df(investigation)
    exp_designs_df = _build_exp_designs_df(investigation)
    exp_factors_df = _build_exp_factors_df(investigation)

    qc_df = _build_qc_df(investigation)
    replicates_df = _build_replicates_df(investigation)
    normalizations_df = _build_normalizations_df(investigation)

    people_df = _build_people_df(investigation)
    publications_df = _build_publications_df(investigation)
    protocols_df = _build_protocols_df(investigation)
    term_sources_df = _build_term_sources_df(investigation)

    idf_df = pd.concat([
        metadata_df,
        exp_designs_df,
        exp_factors_df,
        qc_df,
        replicates_df,
        normalizations_df,
        people_df,
        publications_df,
        protocols_df,
        term_sources_df
    ], axis=1)
    idf_df = idf_df.set_index("MAGE-TAB Version").T
    idf_df = idf_df.replace('', np.nan)
    with open(os.path.join(output_path, "{}.idf.txt".format(investigation.identifier if investigation.identifier != "" else investigation.filename[2:-3])), "w") as idf_fp:
        idf_df.to_csv(path_or_buf=idf_fp, index=True, sep='\t', encoding='utf-8', index_label="MAGE-TAB Version")


def write_sdrf_table_files(i, output_path):
    tmp = tempfile.mkdtemp()
    isatab.write_study_table_files(inv_obj=i, output_dir=tmp)
    isatab.write_assay_table_files(inv_obj=i, output_dir=tmp)
    for study in i.studies:
        for assay in [x for x in study.assays if x.technology_type.term.lower() == "dna microarray"]:
            sdrf_filename = study.filename[2:-3] + assay.filename[2:-3] + "sdrf.txt"
            print("Writing {}".format(sdrf_filename))
            try:
                isatab.merge_study_with_assay_tables(os.path.join(tmp, study.filename),
                                                     os.path.join(tmp, assay.filename),
                                                     os.path.join(output_path, sdrf_filename))
            except FileNotFoundError:
                raise IOError("There was a problem merging intermediate ISA-Tab files into SDRF")


def dump(inv_obj, output_path):
    num_microarray_assays = 0
    for study in inv_obj.studies:
        num_microarray_assays += len([x for x in study.assays if x.technology_type.term.lower() == "dna microarray"])

    if num_microarray_assays > 0:
        write_idf_file(inv_obj, output_path=output_path)
        write_sdrf_table_files(i=inv_obj, output_path=output_path)
    else:
        raise IOError("Input must contain at least one assay of type DNA microarray, halt writing MAGE-TAB")
    return inv_obj


inv_to_idf_map = {
            "Study File Name": "SDRF File",
            "Study Title": "Investigation Title",
            "Study Description": "Experiment Description",
            "Study Public Release Date": "Public Release Date",
            "Comment[MAGETAB TimeStamp_Version]": "MAGETAB TimeStamp_Version",
            "Comment[ArrayExpressReleaseDate]": "ArrayExpressReleaseDate",
            "Comment[Date of Experiment]": "Date of Experiment",
            "Comment[AEMIAMESCORE]": "AEMIAMESCORE",
            "Comment[Submitted Name]": "Submitted Name",
            "Comment[ArrayExpressAccession]": "ArrayExpressAccession",
            "Study Design Type": "Experimental Design",
            "Study Design Type Term Accession Number": "Experimental Design Term Accession Number",
            "Study Design Type Ter Source REF": "Experimental Design Term Source REF",
            "Study Factor Name": "Experimental Factor Name",
            "Study Factor Type": "Experimental Factor Type",
            "Study Factor Type Term Accession Number": "Experimental Factor Type Term Accession Number",
            "Study Factor Type Ter Source REF": "Experimental Factor Type Term Source REF",
            "Study PubMed ID": "PubMed ID",
            "Study Publication DOI": "Publication DOI",
            "Study Publication Author List": "Publication Author List",
            "Study Publication Title": "Publication Title",
            "Study Publication Status": "Publication Status",
            "Study Publication Status Term Accession Number": "Publication Status Term Accession Number",
            "Study Publication Status Term Source REF": "Publication Status Term Source REF",
            "Study Person Last Name": "Person Last Name",
            "Study Person First Name": "Person First Name",
            "Study Person Mid Initials": "Person Mid Initials",
            "Study Person Email": "Person Email",
            "Study Person Phone": "Person Phone",
            "Study Person Fax": "Person Fax",
            "Study Person Address": "Person Address",
            "Study Person Affiliation": "Person Affiliation",
            "Study Person Roles": "Person Role",
            "Study Person Roles Term Accession Number": "Person Role Term Accession Number",
            "Study Person Roles Term Source REF": "Person Role Term Source REF",
            "Study Protocol Name": "Protocol Name",
            "Study Protocol Description": "Protocol Description",
            "Study Protocol Parameters": "Protocol Parameters",
            "Study Protocol Type": "Protocol Type",
            "Study Protocol Type Accession Number": "Protocol Term Accession Number",
            "Study Protocol Type Source REF": "Protocol Term Source REF",
            "Comment[Protocol Software]": "Protocol Software",
            "Comment[Protocol Hardware]": "Protocol Hardware",
            "Comment[Protocol Contact]": "Protocol Contact",
            "Term Source Name": "Term Source Name",
            "Term Source File": "Term Source File",
            "Term Source Version": "Term Source Version",
            "Term Source Description": "Term Source Description"
        }  # Relabel these, ignore all other lines


def cast_inv_to_idf(FP):
    # Cut out relevant Study sections from Investigation file
    idf_FP = StringIO()
    for line in FP:
        if line.startswith(tuple(inv_to_idf_map.keys())) or line.startswith("Comment["):
            for k, v in inv_to_idf_map.items():
                line = line.replace(k, v)
            idf_FP.write(line)
    idf_FP.seek(0)
    idf_FP.name = FP.name
    return idf_FP


def get_first_node_index(header):
    squashed_header = list(map(lambda x: squashstr(x), header))
    nodes = ["samplename", "extractname", "labeledextractname", "hybridizationname", "assayname"]
    for node in nodes:
        try:
            index = squashed_header.index(node)
            return index
        except ValueError:
            pass


def split_tables(sdrf_path):

    def split_on_sample(sdrf_df):
        sdrf_df_isatab_header = sdrf_df.isatab_header
        sdrf_df_cols = list(sdrf_df.columns)
        sample_name_index = sdrf_df_cols.index("Sample Name")
        study_df = sdrf_df[sdrf_df.columns[0:sample_name_index + 1]].drop_duplicates()
        study_df.isatab_header = sdrf_df_isatab_header[0:sample_name_index + 1]
        assay_df = sdrf_df[sdrf_df.columns[sample_name_index:]]
        assay_df.isatab_header = sdrf_df_isatab_header[sample_name_index:]
        return study_df, assay_df

    sdrf_df = isatab.read_tfile(sdrf_path)

    sdrf_columns = list(sdrf_df.columns)
    if "Hybridization Name" in sdrf_columns:
        sdrf_df.columns = [x.replace("Hybridization Name", "Hybridization Assay Name") for x in sdrf_columns]
        sdrf_df.isatab_header = [x.replace("Hybridization Name", "Hybridization Assay Name") for x in sdrf_df.isatab_header]

    if "Sample Name" in sdrf_df.columns:
        return split_on_sample(sdrf_df)
    else:  # insert Sample Name
        sdrf_df_columns = list(sdrf_df.columns)
        sdrf_df["Sample Name"] = sdrf_df[sdrf_df_columns[get_first_node_index(sdrf_df_columns)]]
        sdrf_df_isatab_header = sdrf_df.isatab_header
        sdrf_df_isatab_header.insert(get_first_node_index(sdrf_df_columns), "Sample Name")

        sdrf_df_columns.insert(get_first_node_index(sdrf_df_columns), "Sample Name")

        sdrf_df = sdrf_df[sdrf_df_columns]
        sdrf_df.isatab_header = sdrf_df_isatab_header

        return split_on_sample(sdrf_df)


def transposed_tsv_to_dict(file_path):
    with open(file_path, 'rU') as tsvfile:
        tsvreader = csv.reader(filter(lambda r: r[0] != '#', tsvfile), dialect='excel-tab')
        table_dict = {}
        for row in tsvreader:
            while row and row[-1] is '':  # transpose
                row.pop()
            table_dict[row[0]] = row[1:]  # build dict of label key: list of values
    return table_dict


class MageTabParserException(Exception):
    pass


def squashstr(string):
    nospaces = "".join(string.split())
    return nospaces.lower()


def get_squashed(key):  # for MAGE-TAB spec 2.1.7, deal with variants on labels
    try:
        if squashstr(key[:key.index('[')]) == 'comment':
            return 'comment' + key[key.index('['):]
        else:
            return squashstr(key)
    except ValueError:
        return squashstr(key)


def parse_idf(file_path, technology_type=None, measurement_type=None, technology_platform=None):

    def get_single(values):
        stripped_values = [x for x in values if x != '']
        if len(stripped_values) > 0:
            if len(stripped_values) > 1:
                print("Warning: more than one value found, selecting first in value list")
            return stripped_values[0]

    table_dict = transposed_tsv_to_dict(file_path=file_path)

    squashed_table_dict = {}

    for k, v in table_dict.items():
        squashed_table_dict[get_squashed(k)] = v

    ISA = Investigation()
    S = Study()

    ts_dict = {}

    # Term Source section of IDF

    ts_names = []
    ts_files = []
    ts_versions = []

    try:
        ts_names = squashed_table_dict["termsourcename"]
    except KeyError:
        pass
    try:
        ts_files = squashed_table_dict["termsourcefile"]
    except KeyError:
        pass
    try:
        ts_versions = squashed_table_dict["termsourceversion"]
    except KeyError:
        pass

    for name, file, version in zip_longest(ts_names, ts_files, ts_versions):
        os = OntologySource(name=name, file=file, version=version)
        ISA.ontology_source_references.append(os)
        ts_dict[name] = os

    # Header section of IDF

    try:
        magetab_version = get_single(values=squashed_table_dict["mage-tabversion"])
        S.comments.append(Comment(name="MAGE-TAB Version", value=magetab_version))
    except KeyError:
        print("WARNING: The field MAGE-TAB Version is compulsory but not found")
    try:
        S.title = get_single(values=squashed_table_dict["investigationtitle"])
    except KeyError:
        pass
    try:
        investigation_accession = get_single(values=squashed_table_dict["investigationaccession"])
        S.comments.append(Comment(name="Investigation Accession", value=investigation_accession))
    except KeyError:
        pass
    try:
        investigation_accession_tsr = get_single(values=squashed_table_dict["investigationaccessiontermsourceref"])
        S.comments.append(Comment(name="Investigation Accession Term Source REF", value=investigation_accession_tsr))
    except KeyError:
        pass

    # Experimental Design section of IDF

    experimental_designs = []
    experimental_design_tsrs = []
    experimental_design_tans = []

    try:
        experimental_designs = squashed_table_dict["experimentaldesign"]
    except KeyError:
        pass
    try:
        experimental_design_tsrs = squashed_table_dict["experimentaldesigntermsourceref"]
    except KeyError:
        pass
    try:
        experimental_design_tans = squashed_table_dict["experimentaldesigntermaccessionnumber"]
    except KeyError:
        pass

    for design, tsr, tan in zip_longest(experimental_designs, experimental_design_tsrs, experimental_design_tans):
        try:
            ts = ts_dict[tsr]
        except KeyError:
            ts = None
        S.design_descriptors.append(OntologyAnnotation(term=design, term_source=ts, term_accession=tan))

    # Experimental Factor section of IDF

    factor_names = []
    factor_types = []
    factor_tsrs = []
    factor_tans = []

    try:
        factor_names = squashed_table_dict["experimentalfactorname"]
    except KeyError:
        pass
    try:
        factor_types = squashed_table_dict["experimentalfactortype"]
    except KeyError:
        pass
    try:
        factor_tsrs = squashed_table_dict["experimentalfactortermsourceref"]
    except KeyError:
        pass
    try:
        factor_tans = squashed_table_dict["experimentalfactortermaccessionnumber"]
    except KeyError:
        pass

    for name, type, tsr, tan in zip_longest(factor_names, factor_types, factor_tsrs, factor_tans):
        try:
            ts = ts_dict[tsr]
        except KeyError:
            ts = None
        S.factors.append(StudyFactor(name=name, factor_type=OntologyAnnotation(term=type, term_source=ts,
                                                                               term_accession=tan)))

    # Person section of IDF

    person_last_names = []
    person_first_names = []
    person_mid_initials = []
    person_emails = []
    person_phones = []
    person_addresses = []
    person_affiliations = []
    person_roles = []
    person_roles_tsrs = []
    person_roles_tans = []

    try:
        person_last_names = squashed_table_dict["personlastname"]
    except KeyError:
        pass
    try:
        person_first_names = squashed_table_dict["personfirstname"]
    except KeyError:
        pass
    try:
        person_mid_initials = squashed_table_dict["personmidinitials"]
    except KeyError:
        pass
    try:
        person_emails = squashed_table_dict["personemail"]
    except KeyError:
        pass
    try:
        person_phones = squashed_table_dict["personphone"]
    except KeyError:
        pass
    try:
        person_addresses = squashed_table_dict["personaddress"]
    except KeyError:
        pass
    try:
        person_affiliations = squashed_table_dict["personaffiliation"]
    except KeyError:
        pass
    try:
        person_roles = squashed_table_dict["personroles"]
    except KeyError:
        pass
    try:
        person_roles_tsrs = squashed_table_dict["personrolestermsourceref"]
    except KeyError:
        pass
    try:
        person_roles_tans = squashed_table_dict["personrolestermaccessionnumber"]
    except KeyError:
        pass

    for fname, lname, initials, email, phone, address, affiliation, rolesterm, rolestsrs, rolestans in zip_longest(
            person_last_names, person_first_names, person_mid_initials, person_emails, person_phones, person_addresses,
            person_affiliations, person_roles, person_roles_tsrs, person_roles_tans):

        roles = []

        for role, roletsr, roletan in zip_longest(rolesterm.split(';') if rolesterm is not None else [],
                                                  rolestsrs.split(';') if rolestsrs is not None else [],
                                                  rolestans.split(';') if rolestans is not None else[]):
            try:
                rolets = ts_dict[roletsr]
            except KeyError:
                rolets = None
            roles.append(OntologyAnnotation(term=role, term_source=rolets, term_accession=roletan))  # FIXME roletsr

        S.contacts.append(Person(first_name=fname, last_name=lname, mid_initials=initials, email=email, phone=phone,
                                 address=address, affiliation=affiliation, roles=roles))

    # Quality Control Type section of IDF

    qc_types = []
    qc_tsrs = []
    qc_tans = []

    try:
        qc_types = squashed_table_dict["qualitycontroltype"]
    except KeyError:
        pass
    try:
        qc_tsrs = squashed_table_dict["qualitycontroltermsourceref"]
    except KeyError:
        pass
    try:
        qc_tans = squashed_table_dict["qualitycontroltermaccessionnumber"]
    except KeyError:
        pass

    if len(qc_types) > 0:
        S.comments.append(Comment(name="Quality Control Type", value=';'.join(qc_types)))
    if len(qc_tsrs) > 0:
        S.comments.append(Comment(name="Quality Control Term Source REF", value=';'.join(qc_tsrs)))
    if len(qc_tans) > 0:
        S.comments.append(Comment(name="Quality Control Term Accession Number", value=';'.join(qc_tans)))

    # Replicate Type section of IDF

    rt_types = []
    rt_tsrs = []
    rt_tans = []
    try:
        rt_types = squashed_table_dict["replicatetype"]
    except KeyError:
        pass
    try:
        rt_tsrs = squashed_table_dict["replicatetermsourceref"]
    except KeyError:
        pass
    try:
        rt_tans = squashed_table_dict["replicatetermaccessionnumber"]
    except KeyError:
        pass

    if len(rt_types) > 0:
        S.comments.append(Comment(name="Replicate Type", value=';'.join(rt_types)))
    if len(rt_tsrs) > 0:
        S.comments.append(Comment(name="Replicate Term Source REF", value=';'.join(rt_tsrs)))
    if len(rt_tans) > 0:
        S.comments.append(Comment(name="Replicate Term Accession Number", value=';'.join(rt_tans)))

    # Normalization Type section of IDF

    norm_types = []
    norm_tsrs = []
    norm_tans = []

    try:
        norm_types = squashed_table_dict["normalizationtype"]
    except KeyError:
        pass
    try:
        norm_tsrs = squashed_table_dict["normalizationtermsourceref"]
    except KeyError:
        pass
    try:
        norm_tans = squashed_table_dict["normalizationtermaccessionnumber"]
    except KeyError:
        pass

    if len(norm_types) > 0:
        S.comments.append(Comment(name="Normalization Type", value=';'.join(norm_types)))
    if len(norm_tsrs) > 0:
        S.comments.append(Comment(name="Normalization Term Source REF", value=';'.join(norm_tsrs)))
    if len(norm_tans) > 0:
        S.comments.append(Comment(name="Normalization Term Accession Number", value=';'.join(norm_tans)))

    # Dates section of IDF
    try:
        S.comments.append(Comment(name="Date of Experiment",
                                  value=get_single(values=squashed_table_dict["dateofexperiment"])))
    except KeyError:
        pass
    try:
        S.public_release_date = get_single(values=squashed_table_dict["publicreleasedate"])
    except KeyError:
        pass

    # Publications section of IDF

    pub_pmids = []
    pub_dois = []
    pub_author_list = []
    pub_titles = []
    pub_statuses = []
    pub_status_tsrs = []
    pub_status_tans = []

    try:
        pub_pmids = squashed_table_dict["pubmedid"]
    except KeyError:
        pass
    try:
        pub_dois = squashed_table_dict["publicationdoi"]
    except KeyError:
        pass
    try:
        pub_author_list = squashed_table_dict["publicationauthorlist"]
    except KeyError:
        pass
    try:
        pub_titles = squashed_table_dict["publicationtitle"]
    except KeyError:
        pass
    try:
        pub_statuses = squashed_table_dict["publicationstatus"]
    except KeyError:
        pass
    try:
        pub_status_tsrs = squashed_table_dict["publicationstatustermsourceref"]
    except KeyError:
        pass
    try:
        pub_status_tans = squashed_table_dict["publicationstatustermaccessionnumber"]
    except KeyError:
        pass

    for pmid, doi, authors, title, statusterm, statustsr, statustan in zip_longest(pub_pmids, pub_dois, pub_author_list,
                                                                                   pub_titles, pub_statuses,
                                                                                   pub_status_tsrs, pub_status_tans):
        try:
            statusts = ts_dict[statustsr]
        except KeyError:
            statusts = None
        status = OntologyAnnotation(term=statusterm, term_source=statusts, term_accession=statustan)
        S.publications.append(Publication(pubmed_id=pmid, doi=doi, author_list=authors, title=title, status=status))

    # Description section of IDF

    try:
        S.description = get_single(values=squashed_table_dict["experimentdescription"])
    except KeyError:
        pass

    # Protocols section of IDF

    prot_names = []
    prot_types = []
    prot_tsrs = []
    prot_tans = []
    prot_descriptions = []
    prot_params = []
    prot_hardware = []
    prot_software = []
    prot_contacts = []

    try:
        prot_names = squashed_table_dict["protocolname"]
    except KeyError:
        pass
    try:
        prot_types = squashed_table_dict["protocoltype"]
    except KeyError:
        pass
    try:
        prot_tsrs = squashed_table_dict["protocoltermsourceref"]
    except KeyError:
        pass
    try:
        prot_tans = squashed_table_dict["protocoltermaccessionnumber"]
    except KeyError:
        pass
    try:
        prot_descriptions = squashed_table_dict["protocoldescription"]
    except KeyError:
        pass
    try:
        prot_params = squashed_table_dict["protocolparameters"]
    except KeyError:
        pass
    try:
        prot_hardware = squashed_table_dict["protocolhardware"]
    except KeyError:
        pass
    try:
        prot_software = squashed_table_dict["protocolsoftware"]
    except KeyError:
        pass
    try:
        prot_contacts = squashed_table_dict["protocolcontact"]
    except KeyError:
        pass

    for name, prottypeterm, prottsr, prottan, desc, protparams, hard, soft, contact in zip_longest(prot_names,
                                                                                                   prot_types,
                                                                                                   prot_tsrs, prot_tans,
                                                                                                   prot_descriptions,
                                                                                                   prot_params,
                                                                                                   prot_hardware,
                                                                                                   prot_software,
                                                                                                   prot_contacts):
        try:
            protts = ts_dict[prottsr]
        except KeyError:
            protts = None
        prottype = OntologyAnnotation(term=prottypeterm, term_source=protts, term_accession=prottan)
        params = list(map(lambda x: ProtocolParameter(parameter_name=OntologyAnnotation(term=x)),
                          [x for x in protparams.split(';') if x != ''] if protparams is not None else []))
        protcomments = [
            Comment(name="Protocol Hardware", value=hard),
            Comment(name="Protocol Software", value=hard),
            Comment(name="Protocol Contact", value=contact)
        ]
        S.protocols.append(Protocol(name=name, protocol_type=prottype, description=desc, parameters=params,
                                    comments=protcomments))

    # SDRF file section of IDF
    sdrf_file = None
    try:
        sdrf_file = get_single(values=squashed_table_dict["sdrffile"])
        S.comments.append(Comment(name="SDRF File", value=sdrf_file))
    except KeyError:
        pass

    # Comments in IDF

    comments_dict = dict(map(lambda x: (x[0][8:-1], get_single(x[1])), [x for x in squashed_table_dict.items()
                                                                        if x[0].startswith("comment")]))

    for key in comments_dict.keys():
        c = Comment(name=key, value=comments_dict[key])
        S.comments.append(c)

    if "ArrayExpressAccession" in comments_dict.keys():
        S.identifier = comments_dict["ArrayExpressAccession"]  # ArrayExpress adds this, so use it as the study ID

    design_types = None

    if "experimentaldesign" in squashed_table_dict.keys():
        design_types = experimental_designs

    elif "AEExperimentType" in comments_dict.keys():
        design_types = [comments_dict["AEExperimentType"]]

    inferred_m_type = None
    inferred_t_type = None
    inferred_t_plat = None
    if design_types is not None:
        inferred_m_type, inferred_t_type, inferred_t_plat = get_measurement_and_tech(design_types=design_types)
    else:  # Final try to determine types from study title
        if "transcription prof" in S.title.lower() or "gene expression prof" in S.title.lower():
            inferred_m_type = "transcription profiling"
            measurement_type = "DNA microarray"

    if sdrf_file is not None:
        S.filename = "s_{}".format(sdrf_file)
        a_filename = "a_{}".format(sdrf_file)

        ttoa = None
        if technology_type is not None:
            ttoa = OntologyAnnotation(term=technology_type)
        elif technology_type is None and inferred_t_type is not None:
            print("Detected probable '{}' technology type".format(inferred_t_type))
            ttoa = OntologyAnnotation(term=inferred_t_type)

        mtoa = None
        if measurement_type is not None:
            mtoa = OntologyAnnotation(term=measurement_type)
        elif measurement_type is None and inferred_m_type is not None:
            print("Detected probable '{}' measurement type".format(inferred_m_type))
            mtoa = OntologyAnnotation(term=inferred_m_type)

        tp = ''
        if technology_platform is not None:
            tp = technology_platform
        elif technology_platform is None and inferred_t_plat is not None:
            print("Detected probable '{}' technology platform".format(inferred_t_plat))
            tp = inferred_t_plat

        A = Assay(filename=a_filename, technology_type=ttoa, measurement_type=mtoa, technology_platform=tp)

        if (A.measurement_type, A.technology_type) in [
            ("transcription profiling", "nucleotide sequencing"),
            ("protein-DNA binding site identification", "nucleotide sequencing")
        ]:
            if "library construction" not in [x.name for x in S.protocols]:
                logger.info("PROTOCOL INSERTION: {}, library construction".format(a_filename))
                S.protocols.append(Protocol(name="library construction",
                                            protocol_type=OntologyAnnotation(term="library construction")))
            if "nucleic acid sequencing" not in [x.name for x in S.protocols]:
                logger.info("PROTOCOL INSERTION: {}, nucleic acid sequencing".format(a_filename))
                S.protocols.append(Protocol(name="nucleic acid sequencing",
                                            protocol_type=OntologyAnnotation(term="nucleic acid sequencing")))
        S.assays = [A]

    ISA.identifier = S.identifier
    ISA.title = S.title
    ISA.studies = [S]
    return ISA


def get_measurement_and_tech(design_types):
    for design_type in design_types:
        if re.match("(?i).*ChIP-Chip.*", design_type):
            return "protein-DNA binding site identification", "DNA microarray", "ChIP-Chip"
        if re.match("(?i).*RNA-seq.*", design_type) or re.match("(?i).*RNA-Seq.*", design_type) or re.match(
                "(?i).*transcription profiling by high throughput sequencing.*", design_type):
            return "transcription profiling", "nucleotide sequencing", "RNA-Seq"
        if re.match(".*transcription profiling by array.*", design_type) or re.match("dye_swap_design", design_type):
            return "transcription profiling", "DNA microarray", "GeneChip"
        if re.match("(?i).*methylation profiling by array.*", design_type):
            return "DNA methylation profiling", "DNA microarray", "Me-Chip"
        if re.match("(?i).*comparative genomic hybridization by array.*", design_type):
            return "comparative genomic hybridization", "DNA microarray", "CGH-Chip"
        if re.match(".*genotyping by array.*", design_type):
            return "SNP analysis", "DNA microarray", "SNPChip"
        if re.match("(?i).*ChIP-Seq.*", design_type) or re.match("(?i).*chip-seq.*", design_type):
            return "protein-DNA binding site identification", "nucleotide sequencing", "ChIP-Seq"
        else:
            return None, None, None


class Parser(object):
    """ The MAGE-TAB parser
    This parses MAGE-TAB IDF and SDRF files into Ithe Python ISA model. It does some best-effort inferences on missing
    metadata required by ISA, but note that outputs may still be incomplete and flag warnings and errors in the ISA
    validators. """

    def __init__(self):
        self.ISA = Investigation(studies=Study())
        self._ts_dict = {}

    def parse_idf(self, in_filename):
        idfdict = {}
        with open(in_filename, 'rU') as in_file:
            tabreader = csv.reader(filter(lambda r: r[0] != '#', in_file), dialect='excel-tab')
            for row in tabreader:
                key = get_squashed(key=row[0])
                idfdict[key] = row[1:]

        # Parse the ontology sources first, as we need to reference these later
        self.parse_ontology_sources(idfdict.get('termsourcename'),
                                            idfdict.get('termsourcefile'),
                                            idfdict.get('termsourceversion'))
        # Then parse the rest of the sections in blocks; follows order of MAGE-TAB v1.1 2011-07-28 specification
        self.parse_investigation(idfdict.get('investigationtitle'),
                                         idfdict.get('investigationaccession'),
                                         idfdict.get('investigationaccessiontermsourceref'))
        self.parse_experimental_designs(idfdict.get('experimentaldesign'),
                                        idfdict.get('experimentaldesigntermsourceref'),
                                        idfdict.get('experimentaldesigntermaccessionnumber'))
        self.parse_experimental_factors(idfdict.get('experimentalfactorname'),
                                        idfdict.get('experimentalfactortype'),
                                        idfdict.get('experimentalfactortypetermsourceref'),
                                        idfdict.get('experimentalfactortypetermaccessionnumber'))
        self.parse_people(idfdict.get('personlastname'),
                                  idfdict.get('personfirstname'),
                                  idfdict.get('personmidinitials'),
                                  idfdict.get('personemail'),
                                  idfdict.get('personphone'),
                                  idfdict.get('personfax'),
                                  idfdict.get('personaddress'),
                                  idfdict.get('personaffiliation'),
                                  idfdict.get('personroles'),
                                  idfdict.get('personrolestermsourceref'),
                                  idfdict.get('personrolestermaccessionnumber'))
        self.parse_dates(idfdict.get('dateofexperiment'), idfdict.get('publicreleasedate'))
        self.parse_publications(idfdict.get('pubmedid'),
                                        idfdict.get('publicationdoi'),
                                        idfdict.get('publicationauthorlist'),
                                        idfdict.get('publicationtitle'),
                                        idfdict.get('publicationstatus'),
                                        idfdict.get('publicationstatustermsourceref'),
                                        idfdict.get('publicationstatustermaccessionnumber'))
        self.parse_experiment_description(idfdict.get('experimentdescription'))
        self.parse_protocols(idfdict.get('protocolname'),
                             idfdict.get('protocoltype'),
                             idfdict.get('protocoltermsourceref'),
                             idfdict.get('protocoltermaccessionnumber'),
                             idfdict.get('protocoldescription'),
                             idfdict.get('protocolparameters'),
                             idfdict.get('protocolhardware'),
                             idfdict.get('protocolsoftware'),
                             idfdict.get('protocolcontact'))
        self.parse_sdrf_file(idfdict.get('sdrffile'))
        self.parse_comments({key: idfdict[key] for key in [x for x in idfdict.keys() if x.startswith('comment[')]})

    def parse_ontology_sources(self, names, files, versions):
        for name, file, version, description in zip_longest(names, files, versions):
            os = OntologySource(name=name, file=file, version=version)
            self.ISA.ontology_source_references.append(os)
            self._ts_dict[name] = os

    def parse_investigation(self, titles, accessions, accessiontsrs):
        for title, accession, accessiontsr in zip_longest(titles, accessions, accessiontsrs):
            self.ISA.identifier = accession
            self.ISA.title = title
            self.ISA.studies[-1].title = title
            self.ISA.studies[-1].identifier = accession
            if accessiontsr is not None:
                self.ISA.comments.append(Comment(name="Investigation Accession Term Source REF", value=accessiontsr))
            break  # because there should only be one or zero rows

    def parse_experimental_designs(self, designs, tsrs, tans):
        for design, tsr, tan in zip_longest(designs, tsrs, tans):
            design_descriptor = OntologyAnnotation(term=design, term_source=self._ts_dict.get(tsr), term_accession=tan)
            self.ISA.studies[-1].design_descriptors.append(design_descriptor)

    def parse_experimental_factors(self, factors, factortypes, tsrs, tans):
        for factor, factortype, tsr, tan in zip_longest(factors, factortypes, tsrs, tans):
            factortype_oa = OntologyAnnotation(term=factortype, term_source=self._ts_dict.get(tsr), term_accession=tan)
            study_factor = StudyFactor(name=factor, factor_type=factortype_oa)
            self.ISA.studies[-1].factors.append(study_factor)

    def parse_people(self, lastnames, firstnames, midinitialss, emails, phones, faxes, addresses,
                             affiliations, roles, roletans, roletrs):
        for lastname, firstname, midinitials, email, phone, fax, address, role, roletan, roletsr in \
                zip_longest(lastnames, firstnames, midinitialss, emails, phones, faxes, addresses, affiliations, roles,
                            roletans, roletrs):
            rolesoa = OntologyAnnotation(term=role, term_source=self._ts_dict.get(roletsr), term_accession=roletan)
            person = Person(last_name=lastname, first_name=firstname, mid_initials=midinitials, email=email,
                            phone=phone, fax=fax, address=address, roles=rolesoa)
            self.ISA.studies[-1].contacts.append(person)

    def parse_dates(self, dateofexperiments, publicreleasedates):
        for dateofexperiment, publicreleasedate in zip_longest(dateofexperiments, publicreleasedates):
            self.ISA.public_release_date = publicreleasedate
            self.ISA.studies[-1].public_release_date = publicreleasedate
            self.ISA.studies[-1].comments.append(Comment(name="Date of Experiment", value=dateofexperiment))
            break  # because there should only be one or zero rows

    def parse_publications(self, pubmedids, dois, authorlists, titles, statuses, statustans, statustsrs):
        for pubmedid, doi, authorlist, title, status, statustsr, statustan in \
                zip_longest(pubmedids, dois, authorlists, titles, statuses, statustans, statustsrs):
            statusoa = OntologyAnnotation(term=status, term_source=self._ts_dict.get(statustsr),
                                          term_accession=statustan)
            publication = Publication(pubmed_id=pubmedid, doi=doi, author_list=authorlist, title=title, status=statusoa)
            self.ISA.studies[-1].publications.append(publication)

    def parse_experiment_description(self, descriptions):
        for description in zip_longest(descriptions):
            self.ISA.description = description
            self.ISA.studies[-1].description = description
            break  # because there should only be one or zero rows

    def parse_protocols(self, names, ptypes, tsrs, tans, descriptions, parameterslists, hardwares, softwares, contacts):
        for name, ptype, tsr, tan, description, parameterslist, hardware, software, contact in \
                zip_longest(names, ptypes, tsrs, tans, descriptions, parameterslists, hardwares, softwares, contacts):
            protocoltype_oa = OntologyAnnotation(term=ptype, term_source=self._ts_dict.get(tsr), term_accession=tan)
            protocol = Protocol(name=name, protocol_type=protocoltype_oa, description=description,
                                parameters=list(map(lambda x: Protocol(name=x), parameterslists.split(';'))))
            protocol.comments = [Comment(name="Protocol Hardware", value=hardware),
                                 Comment(name="Protocol Software", value=software),
                                 Comment(name="Protocol Contact", value=contact)]
            self.ISA.studies[-1].protocol.append(protocol)

    def parse_sdrf_file(self, sdrffiles):
        for sdrffile in zip_longest(sdrffiles):
            self.ISA.studies[-1].comments.append(Comment(name="SDRF FIle", value=sdrffile))

    def parse_comments(self, commentsdict):
        for k, v in commentsdict.items():
            if len(v) > 0:
                if len(v) > 1:
                    v = ';'.join(v)
                else:
                    v = v[0]
                self.ISA.studies[-1].comments.append(Comment(name=k[8:-1], value=v))

    def infer_missing_metadata(self):
        I = self.ISA
        S = I.studies[-1]

        # first let's try and infer the MT/TT from the study design descriptors, only checks first one
        defaultassay = self._get_measurement_and_tech(S.design_descriptors[0].term)

        # next, go through the loaded comments to see what we can find
        for comment in S.comments:
            commentkey = get_squashed(comment.name)
            # ArrayExpress specific comments
            # (1) if there is no default assay yet, try use AEExperimentType
            if commentkey == 'aeexperimenttype' and defaultassay is None:
                defaultassay = self._get_measurement_and_tech(comment.value)
            # (2) if there is no identifier set, try use ArrayExpressAccession
            if commentkey == 'arrayexpressaccession':
                if I.identifier == '':
                    I.identifier = comment.value
                if S.identifier == '':
                    S.identifier = comment.value
            # (3) if there is no submission date set, try use ArrayExpressSubmissionDate
            if commentkey == 'arrayexpresssubmissiondate':
                if I.submission_date == '':
                    I.submission_date = comment.value
                if S.submission_date == '':
                    S.submission_date = comment.value

        # if there is STILL no defaultassay set, try infer from study title
        if defaultassay is None \
                and ('transcriptionprof' in get_squashed(S.title) or 'geneexpressionprof' in get_squashed(S.title)):
            defaultassay = Assay(measurement_type=OntologyAnnotation(term='transcription profiling'),
                                 technology_type=OntologyAnnotation(term='DNA microarray'),
                                 technology_platform='GeneChip')

        if defaultassay is None:
            defaultassay = Assay()

        defaultassay.filename = 'a_{0}_assay.txt'.format(S.identifier)

        S.assays = [defaultassay]

    @staticmethod
    def _get_measurement_and_tech(design_type):
        assay = None
        if re.match('(?i).*ChIP-Chip.*', design_type):
            assay = Assay(measurement_type=OntologyAnnotation(term='protein-DNA binding site identification'),
                          technology_type=OntologyAnnotation(term='DNA microarray'),
                          technology_platform='ChIP-Chip')
        if re.match('(?i).*RNA-seq.*', design_type) or re.match('(?i).*RNA-Seq.*', design_type) or re.match(
                '(?i).*transcription profiling by high throughput sequencing.*', design_type):
            assay = Assay(measurement_type=OntologyAnnotation(term='transcription profiling'),
                          technology_type=OntologyAnnotation(term='nucleotide sequencing'),
                          technology_platform='RNA-Seq')
        if re.match('.*transcription profiling by array.*', design_type) or re.match('dye_swap_design',
                                                                                     design_type):
            assay = Assay(measurement_type=OntologyAnnotation(term='transcription profiling'),
                          technology_type=OntologyAnnotation(term= 'DNA microarray'),
                          technology_platform='GeneChip')
        if re.match('(?i).*methylation profiling by array.*', design_type):
            assay = Assay(measurement_type=OntologyAnnotation(term='DNA methylation profiling'),
                          technology_type=OntologyAnnotation(term='DNA microarray'),
                          technology_platform='Me-Chip')
        if re.match('(?i).*comparative genomic hybridization by array.*', design_type):
            assay = Assay(measurement_type=OntologyAnnotation(term='comparative genomic hybridization'),
                          technology_type=OntologyAnnotation(term='DNA microarray'),
                          technology_platform='CGH-Chip')
        if re.match('.*genotyping by array.*', design_type):
            assay = Assay(measurement_type=OntologyAnnotation(term='SNP analysis'),
                          technology_type=OntologyAnnotation(term='DNA microarray'),
                          technology_platform='SNPChip')
        if re.match('(?i).*ChIP-Seq.*', design_type) or re.match('(?i).*chip-seq.*', design_type):
            assay = Assay(measurement_type=OntologyAnnotation(term='protein-DNA binding site identification'),
                          technology_type=OntologyAnnotation(term='nucleotide sequencing'),
                          technology_platform='ChIP-Seq')
        return assay