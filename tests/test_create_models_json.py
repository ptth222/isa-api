"""Tests on serializing planning objects in isatools.create.models to JSON"""
import json
import os
import unittest
from io import StringIO

from isatools.create.models import *
from isatools.tests import utils


def ordered(o):  # to enable comparison of JSONs with lists using ==
    if isinstance(o, dict):
        return sorted((k, ordered(v)) for k, v in o.items())
    if isinstance(o, list):
        return sorted(ordered(x) for x in o if x is not None)
    else:
        return o

NAME = 'name'

FACTORS_0_VALUE = 'nitroglycerin'
FACTORS_0_VALUE_ALT = 'alchohol'
FACTORS_0_VALUE_THIRD = 'water'
FACTORS_1_VALUE = 5
FACTORS_1_UNIT = OntologyAnnotation(term='kg/m^3')
FACTORS_2_VALUE = 100.0
FACTORS_2_VALUE_ALT = 50.0
FACTORS_2_UNIT = OntologyAnnotation(term='s')

TEST_EPOCH_0_NAME = 'test epoch 0'
TEST_EPOCH_1_NAME = 'test epoch 1'
TEST_EPOCH_2_NAME = 'test epoch 2'

TEST_STUDY_ARM_NAME_00 = 'first arm'
TEST_STUDY_ARM_NAME_01 = 'second arm'
TEST_STUDY_ARM_NAME_02 = 'third arm'

TEST_STUDY_DESIGN_NAME = 'test study design'
TEST_STUDY_DESIGN_NAME_THREE_ARMS = 'TEST STUDY DESIGN WITH THREE ARMS'
TEST_STUDY_DESIGN_NAME_TWO_ARMS_MULTI_ELEMENT_CELLS = 'TEST STUDY DESIGN WITH TWO ARMS (MULTI-ELEMENT CELLS)'

TEST_EPOCH_0_RANK = 0

SCREEN_DURATION_VALUE = 100
FOLLOW_UP_DURATION_VALUE = 5 * 366
WASHOUT_DURATION_VALUE = 30
DURATION_UNIT = OntologyAnnotation(term='day')

DIETARY_FACTOR_0_VALUE = 'Vitamin A'
DIETARY_FACTOR_1_VALUE = 30.0
DIETARY_FACTOR_1_UNIT = OntologyAnnotation(term='mg')
DIETARY_FACTOR_2_VALUE = 50
DIETARY_FACTOR_2_UNIT = OntologyAnnotation(term='day')

RADIOLOGICAL_FACTOR_0_VALUE = 'Gamma ray'
RADIOLOGICAL_FACTOR_1_VALUE = 12e-3
RADIOLOGICAL_FACTOR_1_UNIT = OntologyAnnotation(term='Gy')
RADIOLOGICAL_FACTOR_2_VALUE = 5
RADIOLOGICAL_FACTOR_2_UNIT = OntologyAnnotation(term='hour')

BIOLOGICAL_FACTOR_0_VALUE = 'Anthrax'
BIOLOGICAL_FACTOR_1_VALUE = 12e-3
BIOLOGICAL_FACTOR_1_UNIT = OntologyAnnotation(term='mg')
BIOLOGICAL_FACTOR_2_VALUE = 7
BIOLOGICAL_FACTOR_2_UNIT = OntologyAnnotation(term='day')


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.first_treatment = Treatment(factor_values=(
            FactorValue(factor_name=BASE_FACTORS[0], value=FACTORS_0_VALUE),
            FactorValue(factor_name=BASE_FACTORS[1], value=FACTORS_1_VALUE, unit=FACTORS_1_UNIT),
            FactorValue(factor_name=BASE_FACTORS[2], value=FACTORS_2_VALUE, unit=FACTORS_2_UNIT)
        ))
        self.second_treatment = Treatment(factor_values=(
            FactorValue(factor_name=BASE_FACTORS[0], value=FACTORS_0_VALUE_ALT),
            FactorValue(factor_name=BASE_FACTORS[1], value=FACTORS_1_VALUE, unit=FACTORS_1_UNIT),
            FactorValue(factor_name=BASE_FACTORS[2], value=FACTORS_2_VALUE, unit=FACTORS_2_UNIT)
        ))
        self.third_treatment = Treatment(factor_values=(
            FactorValue(factor_name=BASE_FACTORS[0], value=FACTORS_0_VALUE_ALT),
            FactorValue(factor_name=BASE_FACTORS[1], value=FACTORS_1_VALUE, unit=FACTORS_1_UNIT),
            FactorValue(factor_name=BASE_FACTORS[2], value=FACTORS_2_VALUE_ALT, unit=FACTORS_2_UNIT)
        ))
        self.fourth_treatment = Treatment(factor_values=(
            FactorValue(factor_name=BASE_FACTORS[0], value=FACTORS_0_VALUE_THIRD),
            FactorValue(factor_name=BASE_FACTORS[1], value=FACTORS_1_VALUE, unit=FACTORS_1_UNIT),
            FactorValue(factor_name=BASE_FACTORS[2], value=FACTORS_2_VALUE, unit=FACTORS_2_UNIT)
        ))
        self.fifth_treatment = Treatment(element_type=INTERVENTIONS['DIET'], factor_values=(
            FactorValue(factor_name=BASE_FACTORS[0], value=DIETARY_FACTOR_0_VALUE),
            FactorValue(factor_name=BASE_FACTORS[1], value=DIETARY_FACTOR_1_VALUE, unit=DIETARY_FACTOR_1_UNIT),
            FactorValue(factor_name=BASE_FACTORS[2], value=DIETARY_FACTOR_2_VALUE, unit=DIETARY_FACTOR_2_UNIT)
        ))
        self.sixth_treatment = Treatment(element_type=INTERVENTIONS['RADIOLOGICAL'], factor_values=(
            FactorValue(factor_name=BASE_FACTORS[0], value=RADIOLOGICAL_FACTOR_0_VALUE),
            FactorValue(factor_name=BASE_FACTORS[1], value=RADIOLOGICAL_FACTOR_1_VALUE,
                        unit=RADIOLOGICAL_FACTOR_1_UNIT),
            FactorValue(factor_name=BASE_FACTORS[2], value=RADIOLOGICAL_FACTOR_2_VALUE,
                        unit=RADIOLOGICAL_FACTOR_2_UNIT)
        ))
        self.seventh_treatment = Treatment(element_type=INTERVENTIONS['BIOLOGICAL'], factor_values=(
            FactorValue(factor_name=BASE_FACTORS[0], value=BIOLOGICAL_FACTOR_0_VALUE),
            FactorValue(factor_name=BASE_FACTORS[1], value=BIOLOGICAL_FACTOR_1_VALUE, unit=BIOLOGICAL_FACTOR_1_UNIT),
            FactorValue(factor_name=BASE_FACTORS[2], value=BIOLOGICAL_FACTOR_2_VALUE, unit=BIOLOGICAL_FACTOR_2_UNIT)
        ))
        self.screen = NonTreatment(element_type=SCREEN,
                                   duration_value=SCREEN_DURATION_VALUE, duration_unit=DURATION_UNIT)
        self.run_in = NonTreatment(element_type=RUN_IN,
                                   duration_value=WASHOUT_DURATION_VALUE, duration_unit=DURATION_UNIT)
        self.washout = NonTreatment(element_type=WASHOUT,
                                    duration_value=WASHOUT_DURATION_VALUE, duration_unit=DURATION_UNIT)
        self.follow_up = NonTreatment(element_type=FOLLOW_UP,
                                      duration_value=FOLLOW_UP_DURATION_VALUE, duration_unit=DURATION_UNIT)
        self.potential_concomitant_washout = NonTreatment(element_type=WASHOUT, duration_value=FACTORS_2_VALUE,
                                                          duration_unit=FACTORS_2_UNIT)
        self.cell_screen = StudyCell('SCREEN CELL', elements=(self.screen,))
        self.cell_run_in = StudyCell('RUN-IN CELL', elements=(self.run_in,))
        self.cell_single_treatment_00 = StudyCell('SINGLE-TREATMENT CELL', elements=[self.first_treatment])
        self.cell_single_treatment_01 = StudyCell('ANOTHER SINGLE-TREATMENT CELL', elements=[self.second_treatment])
        self.cell_single_treatment_02 = StudyCell('YET ANOTHER SINGLE-TREATMENT CELL', elements=[self.third_treatment])
        self.cell_single_treatment_diet = StudyCell('DIET CELL', elements=[self.fifth_treatment])
        self.cell_single_treatment_radiological = StudyCell('RADIOLOGICAL CELL', elements=[self.sixth_treatment])
        self.cell_single_treatment_biological = StudyCell('BIOLOGICAL CELL', elements=[self.seventh_treatment])
        self.cell_multi_elements = StudyCell('MULTI-ELEMENT CELL',
                                             elements=[{self.first_treatment, self.second_treatment,
                                                        self.fourth_treatment}, self.washout, self.second_treatment])
        self.cell_multi_elements_padded = StudyCell('PADDED MULTI-ELEMENT CELL',
                                                    elements=[self.first_treatment, self.washout, {
                                                        self.second_treatment,
                                                        self.fourth_treatment
                                                    }, self.washout, self.third_treatment, self.washout])
        self.cell_multi_elements_bio_diet = StudyCell('MULTI-ELEMENT CELL BIO-DIET',
                                                     elements=[{
                                                           self.second_treatment,
                                                           self.fourth_treatment,
                                                           self.first_treatment
                                                       }, self.washout, self.fifth_treatment, self.washout,
                                                           self.seventh_treatment])
        self.cell_follow_up = StudyCell('FOLLOW-UP CELL', elements=(self.follow_up,))
        self.cell_washout_00 = StudyCell('WASHOUT CELL', elements=(self.washout,))
        self.cell_washout_01 = StudyCell('ANOTHER WASHOUT', elements=[self.washout])
        self.sample_assay_plan_for_screening = SampleAssayPlan(name='SAMPLE ASSAY PLAN FOR SCREENING')
        self.sample_assay_plan_for_treatments = SampleAssayPlan(name='SAMPLE ASSAY PLAN FOR TREATMENTS')
        self.sample_assay_plan_for_washout = SampleAssayPlan(name='SAMPLE ASSAY PLAN FOR WASHOUT')
        self.sample_assay_plan_for_follow_up = SampleAssayPlan(name='FOLLOW-UP SAMPLE ASSAY PLAN')
        self.single_treatment_cell_arm = StudyArm(name=TEST_STUDY_ARM_NAME_00, group_size=10, arm_map=OrderedDict([
            [self.cell_screen, None], [self.cell_run_in, None],
            [self.cell_single_treatment_00, self.sample_assay_plan_for_treatments],
            [self.cell_washout_00, self.sample_assay_plan_for_washout],
            [self.cell_single_treatment_01, self.sample_assay_plan_for_treatments],
            [self.cell_follow_up, self.sample_assay_plan_for_follow_up]
        ]))
        self.single_treatment_cell_arm_01 = StudyArm(name=TEST_STUDY_ARM_NAME_01, group_size=30, arm_map=OrderedDict([
            [self.cell_screen, None], [self.cell_run_in, None],
            [self.cell_single_treatment_00, self.sample_assay_plan_for_treatments],
            [self.cell_washout_00, self.sample_assay_plan_for_washout],
            [self.cell_single_treatment_biological, self.sample_assay_plan_for_treatments],
            [self.cell_follow_up, self.sample_assay_plan_for_follow_up]
        ]))
        self.single_treatment_cell_arm_02 = StudyArm(name=TEST_STUDY_ARM_NAME_02, group_size=24, arm_map=OrderedDict([
            [self.cell_screen, None], [self.cell_run_in, None],
            [self.cell_single_treatment_diet, self.sample_assay_plan_for_treatments],
            [self.cell_washout_00, self.sample_assay_plan_for_washout],
            [self.cell_single_treatment_radiological, self.sample_assay_plan_for_treatments],
            [self.cell_follow_up, self.sample_assay_plan_for_follow_up]
        ]))
        self.multi_treatment_cell_arm = StudyArm(name=TEST_STUDY_ARM_NAME_00, group_size=35, arm_map=OrderedDict([
            [self.cell_screen, self.sample_assay_plan_for_screening],
            [self.cell_multi_elements_padded, self.sample_assay_plan_for_treatments],
            [self.cell_follow_up, self.sample_assay_plan_for_follow_up]
        ]))
        self.multi_treatment_cell_arm_01 = StudyArm(name=TEST_STUDY_ARM_NAME_01, group_size=5, arm_map=OrderedDict([
            [self.cell_screen, self.sample_assay_plan_for_screening],
            [self.cell_multi_elements_bio_diet, self.sample_assay_plan_for_treatments],
            [self.cell_follow_up, self.sample_assay_plan_for_follow_up]
        ]))


class StudyCellEncoderTest(BaseTestCase):

    def setUp(self):
        return super(StudyCellEncoderTest, self).setUp()

    def test_encode_single_treatment_cell(self):
        actual_json_cell = json.loads(json.dumps(self.cell_single_treatment_00, cls=StudyCellEncoder))
        with open(os.path.join(os.path.dirname(__file__), 'data', 'json', 'create',
                               'single-treatment-cell.json')) as expected_json_fp:
            expected_json_cell = json.load(expected_json_fp)
        self.assertEqual(ordered(actual_json_cell), ordered(expected_json_cell))

    def test_encode_multi_treatment_cell(self):
        self.maxDiff = None
        json_cell = json.loads(json.dumps(self.cell_multi_elements_padded, cls=StudyCellEncoder))
        with open(os.path.join(os.path.dirname(__file__), 'data', 'json', 'create',
                               'multi-treatment-padded-cell.json')) as expected_json_fp:
            expected_json_cell = json.load(expected_json_fp)
        self.assertEqual(ordered(json_cell), ordered(expected_json_cell))


class StudyCellDecoderTest(BaseTestCase):

    def setUp(self):
        return super(StudyCellDecoderTest, self).setUp()

    def test_decode_single_treatment_cell(self):
        decoder = StudyCellDecoder()
        with open(os.path.join(os.path.dirname(__file__), 'data', 'json', 'create',
                               'single-treatment-cell.json')) as expected_json_fp:
            json_text = json.dumps(json.load(expected_json_fp))
            actual_cell = decoder.loads(json_text)
        # print(self.cell_single_treatment)
        # print('\n')
        # print(actual_cell)
        # self.assertEqual(self.cell_single_treatment.elements[0], actual_cell.elements[0])
        self.assertEqual(self.cell_single_treatment_00, actual_cell)

    def test_decode_multi_treatment_cell(self):
        decoder = StudyCellDecoder()
        with open(os.path.join(os.path.dirname(__file__), 'data', 'json', 'create',
                               'multi-treatment-padded-cell.json')) as expected_json_fp:
            json_text = json.dumps(json.load(expected_json_fp))
            actual_cell = decoder.loads(json_text)
        self.assertEqual(len(self.cell_multi_elements_padded.elements), len(actual_cell.elements))
        for i in range(len(actual_cell.elements)):
            print(i)
            print(actual_cell.elements[i])
            print(self.cell_multi_elements_padded.elements[i])
            self.assertEqual(self.cell_multi_elements_padded.elements[i], actual_cell.elements[i])
        self.assertEqual(self.cell_multi_elements_padded, actual_cell)


class SampleAndAssayPlanEncoderAndDecoderTest(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.plan = SampleAndAssayPlan()
        self.tissue_char = Characteristic(category='organism part', value='tissue')
        self.dna_char = Characteristic(category='nucleic acid', value='DNA')
        self.mirna_char = Characteristic(category='nucleic acid', value='miRNA')
        self.mrna_char = Characteristic(category='nucleic acid', value='mRNA')
        self.sample_node = ProductNode(id_='product-node/0000', node_type=SAMPLE, size=3,
                                       characteristics=[self.tissue_char])
        self.protocol_node_dna = ProtocolNode(id_='protocol-node/0000', name='DNA extraction', version="1.0.0")
        self.protocol_node_rna = ProtocolNode(id_='protocol-node/0001', name='RNA extraction', version="0.1")
        self.dna_node = ProductNode(id_='product-node/0001', node_type=SAMPLE, size=3,
                                    characteristics=[self.dna_char])
        self.mrna_node = ProductNode(id_='product-node/0002', node_type=SAMPLE, size=3,
                                     characteristics=[self.mrna_char])
        self.mirna_node = ProductNode(id_='product-node/0003', node_type=SAMPLE, size=5,
                                      characteristics=[self.mirna_char])
        self.plan.add_nodes([self.sample_node, self.protocol_node_dna, self.protocol_node_rna, self.dna_node,
                             self.mrna_node, self.mirna_node])
        self.plan.add_links([(self.sample_node, self.protocol_node_rna), (self.sample_node, self.protocol_node_dna),
                             (self.protocol_node_rna, self.mrna_node), (self.protocol_node_rna, self.mirna_node),
                             (self.protocol_node_dna, self.dna_node)
                             ])

    def test_encode_dna_rna_extraction_plan(self):
        actual_json_plan = json.loads(json.dumps(self.plan, cls=SampleAndAssayPlanEncoder))
        with open(os.path.join(os.path.dirname(__file__), 'data', 'json', 'create',
                               'dna-rna-extraction-sample-and-assay-plan.json')) as expected_json_fp:
            expected_json_plan = json.load(expected_json_fp)
        self.assertEqual(ordered(actual_json_plan), ordered(expected_json_plan))

    def test_decode_dna_rna_extraction_plan(self):
        decoder = SampleAndAssayPlanDecoder()
        with open(os.path.join(os.path.dirname(__file__), 'data', 'json', 'create',
                               'dna-rna-extraction-sample-and-assay-plan.json')) as expected_json_fp:
            json_text = json.dumps(json.load(expected_json_fp))
            actual_plan = decoder.loads(json_text)
        # pdb.set_trace()
        self.assertEqual(self.plan, actual_plan)


class StudyArmEncoderTest(BaseTestCase):

    def setUp(self):
        return super(StudyArmEncoderTest, self).setUp()

    def test_encode_arm_with_single_element_cells(self):
        actual_json_arm = json.loads(json.dumps(self.single_treatment_cell_arm, cls=StudyArmEncoder))
        with open(os.path.join(os.path.dirname(__file__), 'data', 'json', 'create',
                               'study-arm-with-single-element-cells.json')) as expected_json_fp:
            expected_json_arm = json.load(expected_json_fp)
        print(actual_json_arm)
        self.assertEqual(ordered(actual_json_arm), ordered(expected_json_arm))

    def test_encode_arm_with_multi_element_cell(self):
        actual_json_arm = json.loads(json.dumps(self.multi_treatment_cell_arm, cls=StudyArmEncoder))
        with open(os.path.join(os.path.dirname(__file__), 'data', 'json', 'create',
                               'study-arm-with-multi-element-cell.json')) as expected_json_fp:
            expected_json_arm = json.load(expected_json_fp)
        self.assertEqual(ordered(actual_json_arm), ordered(expected_json_arm))


class StudyArmDecoderTest(BaseTestCase):

    def setUp(self):
        return super(StudyArmDecoderTest, self).setUp()

    def test_decode_arm_with_single_element_cells(self):
        decoder = StudyArmDecoder()
        with open(os.path.join(os.path.dirname(__file__), 'data', 'json', 'create',
                               'study-arm-with-single-element-cells.json')) as expected_json_fp:
            json_text = json.dumps(json.load(expected_json_fp))
            actual_arm = decoder.loads(json_text)
        self.assertEqual(self.single_treatment_cell_arm, actual_arm)

    def test_decode_arm_with_multi_element_cells(self):
        decoder = StudyArmDecoder()
        with open(os.path.join(os.path.dirname(__file__), 'data', 'json', 'create',
                               'study-arm-with-multi-element-cell.json')) as expected_json_fp:
            json_text = json.dumps(json.load(expected_json_fp))
            actual_arm = decoder.loads(json_text)
        self.assertEqual(self.multi_treatment_cell_arm, actual_arm)


class StudyDesignEncoderTest(BaseTestCase):

    def setUp(self):
        super(StudyDesignEncoderTest, self).setUp()
        self.three_arm_study_design = StudyDesign(name=TEST_STUDY_DESIGN_NAME_THREE_ARMS, study_arms={
            self.single_treatment_cell_arm,
            self.single_treatment_cell_arm_01,
            self.single_treatment_cell_arm_02
        })
        self.multi_element_cell_two_arm_study_design = StudyDesign(
            name=TEST_STUDY_DESIGN_NAME_TWO_ARMS_MULTI_ELEMENT_CELLS, study_arms=[
                self.multi_treatment_cell_arm,
                self.multi_treatment_cell_arm_01
            ])

    def test_encode_study_design_with_three_arms(self):
        actual_json_study_design = json.loads(json.dumps(self.three_arm_study_design, cls=StudyDesignEncoder))
        with open(os.path.join(os.path.dirname(__file__), 'data', 'json', 'create',
                               'study-design-with-three-arms-single-element-cells.json')) as expected_json_fp:
            expected_json_study_design = json.load(expected_json_fp)
        self.assertEqual(ordered(actual_json_study_design), ordered(expected_json_study_design))

    def test_encode_study_design_with_two_arms_with_multi_element_cells(self):
        actual_json_study_design = json.loads(json.dumps(self.multi_element_cell_two_arm_study_design,
                                                         cls=StudyDesignEncoder))
        with open(os.path.join(os.path.dirname(__file__), 'data', 'json', 'create',
                               'study-design-with-two-arms-multi-element-cells.json')) as expected_json_fp:
            expected_json_study_design = json.load(expected_json_fp)
        self.assertEqual(ordered(actual_json_study_design), ordered(expected_json_study_design))


class StudyDesignDecoderTest(BaseTestCase):

    def setUp(self):
        super(StudyDesignDecoderTest, self).setUp()
        self.three_arm_study_design = StudyDesign(name=TEST_STUDY_DESIGN_NAME_THREE_ARMS, study_arms={
            self.single_treatment_cell_arm,
            self.single_treatment_cell_arm_01,
            self.single_treatment_cell_arm_02
        })
        self.multi_element_cell_two_arm_study_design = StudyDesign(
            name=TEST_STUDY_DESIGN_NAME_TWO_ARMS_MULTI_ELEMENT_CELLS, study_arms=[
                self.multi_treatment_cell_arm,
                self.multi_treatment_cell_arm_01
            ])

    def test_decode_study_design_with_three_arms(self):
        decoder = StudyDesignDecoder()
        with open(os.path.join(os.path.dirname(__file__), 'data', 'json', 'create',
                               'study-design-with-three-arms-single-element-cells.json')) as expected_json_fp:
            json_text = json.dumps(json.load(expected_json_fp))
            actual_study_design = decoder.loads(json_text)
        # print("\nExpected:\n")
        # print(self.three_arm_study_design)
        # print("\nActual:\n")
        # print(actual_study_design)
        # print("\nDifference:\n")
        import difflib
        # difflib.ndiff(repr(self.three_arm_study_design), repr(actual_study_design))
        self.assertEqual(self.three_arm_study_design.name, actual_study_design.name)
        """
        for i, arm in enumerate(self.three_arm_study_design.study_arms):
            print("comparing study arm #{0} - {1}".format(i, arm.name))
            print("Difference:\n")
            difflib.ndiff(arm, actual_study_design.study_arms[i])
            print("\nExpected:\n")
            print(arm)
            print("\nActual:\n")
            print(actual_study_design.study_arms[i])
            self.assertEqual(arm, actual_study_design.study_arms[i])
        self.assertEqual(self.three_arm_study_design.study_arms[0], actual_study_design.study_arms[0])
        self.assertEqual(self.three_arm_study_design.study_arms[1], actual_study_design.study_arms[1])
        expected_third_arm = self.three_arm_study_design.study_arms[2]
        self.assertEqual(expected_third_arm.name, actual_study_design.study_arms[2].name)
        self.assertEqual(expected_third_arm.group_size,
                         actual_study_design.study_arms[2].group_size)
        # print("Arm map:")
        # print(list(actual_study_design.study_arms[2].arm_map.keys()))
        i = 0
        for cell, sample_assay_plan in expected_third_arm.arm_map.items():
            print("testing cell {0}".format(cell.name))
            print(cell)
            print(list(actual_study_design.study_arms[2].arm_map.keys())[i])
            self.assertTrue(cell in actual_study_design.study_arms[2].arm_map)
            self.assertEqual(sample_assay_plan, actual_study_design.study_arms[2].arm_map[cell])
            i = i + 1
        self.assertEqual(self.three_arm_study_design.study_arms[2], actual_study_design.study_arms[2])
        # self.assertEqual(self.three_arm_study_design.study_arms[2], actual_study_design.study_arms[2])
        """
        self.assertEqual(self.three_arm_study_design, actual_study_design)

    def test_decode_study_design_with_two_arms_with_multi_element_cells(self):
        decoder = StudyDesignDecoder()
        with open(os.path.join(os.path.dirname(__file__), 'data', 'json', 'create',
                               'study-design-with-two-arms-multi-element-cells.json')) as expected_json_fp:
            json_text = json.dumps(json.load(expected_json_fp))
            actual_study_design = decoder.loads(json_text)
        self.assertEqual(self.multi_element_cell_two_arm_study_design, actual_study_design)


class EncodeToJsonTests(unittest.TestCase):

    def setUp(self):
        pass

    @unittest.skip(
        'Serialization implementation incomplete (out of sync with model)')
    def test_serialize_dna_micro_assay_default_topology_modifiers(self):
        expected = ordered(
            json.loads("""{
                "technical_replicates": 1,
                "array_designs": []
            }""")
        )

        actual = ordered(
            json.loads(
                json.dumps(DNAMicroAssayTopologyModifiers(),
                           cls=SampleAssayPlanEncoder)
            )
        )
        self.assertTrue(expected == actual)

    @unittest.skip(
        'Serialization implementation incomplete (out of sync with model)')
    def test_serialize_dna_seq_assay_default_topology_modifiers(self):
        expected = ordered(
            json.loads("""{
                "technical_replicates": 1,
                "distinct_libraries": 0,
                "instruments": []
            }""")
        )

        actual = ordered(
            json.loads(
                json.dumps(DNASeqAssayTopologyModifiers(),
                           cls=SampleAssayPlanEncoder)
            )
        )
        self.assertTrue(expected == actual)

    @unittest.skip(
        'Serialization implementation incomplete (out of sync with model)')
    def test_serialize_ms_assay_default_topology_modifiers(self):
        expected = ordered(
            json.loads("""{
                "sample_fractions": [],            
                "injection_modes": []
            }""")
        )

        actual = ordered(
            json.loads(
                json.dumps(MSTopologyModifiers(),
                           cls=SampleAssayPlanEncoder)
            )
        )
        self.assertTrue(expected == actual)

    @unittest.skip(
        'Serialization implementation incomplete (out of sync with model)')
    def test_serialize_ms_assay_topology_modifiers(self):
        expected = ordered(
            json.loads("""{
                "sample_fractions": [
                    "non-polar",
                    "polar"
                ],
                "injection_modes": [
                    {
                        "acquisition_modes": [],
                        "injection_mode": "DI"
                    },
                    {
                        "chromatography_column": "Chrom col",
                        "instrument": "MS instr",
                        "acquisition_modes": [
                            {
                                "acquisition_method": "positive",
                                "technical_repeats": 1
                            }
                        ],
                        "injection_mode": "LC",
                        "chromatography_instrument": "Chrom instr"
                    }
                ]
            }""")
    )

        top_mods = MSTopologyModifiers()
        top_mods.sample_fractions.add('polar')
        top_mods.sample_fractions.add('non-polar')
        top_mods.injection_modes.add(MSInjectionMode())
        top_mods.injection_modes.add(
            MSInjectionMode(
                injection_mode='LC', chromatography_instrument='Chrom instr',
                chromatography_column='Chrom col', ms_instrument='MS instr',
                acquisition_modes={
                    MSAcquisitionMode(
                        acquisition_method='positive', technical_repeats=1)
                }
            )
        )

        actual = ordered(
            json.loads(
                json.dumps(top_mods, cls=SampleAssayPlanEncoder)
            )
        )
        self.assertTrue(expected == actual)

    @unittest.skip(
        'Serialization implementation incomplete (out of sync with model)')
    def test_serialize_nmr_assay_default_topology_modifiers(self):
        expected = ordered(
            json.loads("""{
                "technical_replicates": 1,
                "instruments": [],
                "injection_modes": [],
                "pulse_sequences": [],
                "acquisition_modes": []
            }""")
        )

        actual = ordered(
            json.loads(
                json.dumps(NMRTopologyModifiers(),
                           cls=SampleAssayPlanEncoder)
            )
        )
        self.assertTrue(expected == actual)

    @unittest.skip(
        'Serialization implementation incomplete (out of sync with model)')
    def test_serialize_default_assay_type(self):
        expected = ordered(
            json.loads("""{
                "measurement_type": "",
                "technology_type": "",
                "topology_modifiers": []
            }""")
        )

        actual = ordered(
            json.loads(
                json.dumps(AssayType(), cls=SampleAssayPlanEncoder)
            )
        )
        self.assertTrue(expected == actual)

    @unittest.skip(
        'Serialization implementation incomplete (out of sync with model)')
    def test_serialize_assay_type(self):
        expected = ordered(
            json.loads("""{
                "measurement_type": "genome sequencing",
                "technology_type": "DNA microarray",
                "topology_modifiers": []
            }""")
        )

        actual = ordered(
            json.loads(
                json.dumps(self.assay_type, cls=SampleAssayPlanEncoder)
            )
        )
        self.assertTrue(expected == actual)

    @unittest.skip(
        'Serialization implementation incomplete (out of sync with model)')
    def test_serialize_assay_type_with_dna_micro_top_mods(self):
        self.assay_type.topology_modifiers = self.top_mods

        expected = ordered(
            json.loads("""{
                "topology_modifiers": {
                    "technical_replicates": 2,
                    "array_designs": ["A-AFFY-27", "A-AFFY-28"]
                },
                "measurement_type": "genome sequencing",
                "technology_type": "DNA microarray"
            }""")
        )
        actual = ordered(
            json.loads(
                json.dumps(self.assay_type, cls=SampleAssayPlanEncoder)
            )
        )
        self.assertTrue(expected == actual)

    @unittest.skip(
        'Serialization implementation incomplete (out of sync with model)')
    def test_serialize_default_sampleassayplan(self):
        expected = ordered(
            json.loads("""{
                "group_size": 0,
                "assay_types": [],
                "sample_plan": [],
                "sample_types": [],
                "sample_qc_plan": [],
                "assay_plan": []
            }""")
        )
        actual = ordered(
            json.loads(
                json.dumps(SampleAssayPlan(), cls=SampleAssayPlanEncoder)
            )
        )

        self.assertTrue(expected == actual)

    @unittest.skip(
        'Serialization implementation incomplete (out of sync with model)')
    def test_serialize_sampleplan(self):
        expected = ordered(
            json.loads("""{
                "group_size": 20,
                "assay_plan": [],
                "sample_plan": [
                    {
                        "sample_type": "liver",
                        "sampling_size": 3
                    },
                    {
                        "sample_type": "tissue",
                        "sampling_size": 5
                    }
                ],
                "sample_qc_plan": [],
                "assay_types": [],
                "sample_types": ["liver", "tissue"]
            }""")
        )

        actual = ordered(
            json.loads(
                json.dumps(self.plan, cls=SampleAssayPlanEncoder)
            )
        )
        self.assertTrue(expected == actual)

    @unittest.skip(
        'Serialization implementation incomplete (out of sync with model)')
    def test_serialize_sampleplan_with_qc(self):
        self.plan.add_sample_type('water')
        self.plan.add_sample_qc_plan_record('water', 8)
        batch1 = SampleQCBatch()
        batch1.material = 'blank'
        batch1.parameter_values = [
            ParameterValue(category=ProtocolParameter(
                parameter_name=OntologyAnnotation(term='param1')), value=5),
            ParameterValue(category=ProtocolParameter(
                parameter_name=OntologyAnnotation(term='param1')), value=4),
            ParameterValue(category=ProtocolParameter(
                parameter_name=OntologyAnnotation(term='param1')), value=3),
            ParameterValue(category=ProtocolParameter(
                parameter_name=OntologyAnnotation(term='param1')), value=2),
            ParameterValue(category=ProtocolParameter(
                parameter_name=OntologyAnnotation(term='param1')), value=1),
            ParameterValue(category=ProtocolParameter(
                parameter_name=OntologyAnnotation(term='param1')), value=1),
            ParameterValue(category=ProtocolParameter(
                parameter_name=OntologyAnnotation(term='param1')), value=1),
            ParameterValue(category=ProtocolParameter(
                parameter_name=OntologyAnnotation(term='param1')), value=1),
            ParameterValue(category=ProtocolParameter(
                parameter_name=OntologyAnnotation(term='param1')), value=1),
            ParameterValue(category=ProtocolParameter(
                parameter_name=OntologyAnnotation(term='param1')), value=1)
        ]
        self.plan.pre_run_batch = batch1
        batch2 = SampleQCBatch()
        batch2.material = 'solvent'
        batch2.parameter_values = [
            ParameterValue(category=ProtocolParameter(
                parameter_name=OntologyAnnotation(term='param2')), value=x)
            for x in reversed([x.value for x in batch1.parameter_values])]
        self.plan.post_run_batch = batch2

        expected = ordered(
            json.loads("""{
                        "group_size": 20,
                        "assay_plan": [],
                        "sample_plan": [
                            {
                                "sample_type": "liver",
                                "sampling_size": 3
                            },
                            {
                                "sample_type": "tissue",
                                "sampling_size": 5
                            }
                        ],
                        "sample_qc_plan": [
                            {
                                "sample_type": "water",
                                "injection_interval": 8
                            }
                        ],
                        "assay_types": [],
                        "sample_types": ["liver", "tissue", "water"],
                        "pre_run_batch": {
                            "material": "blank",
                            "variable_type": "parameter",
                            "variable_name": "param1",
                            "values": [
                                5, 4, 3, 2, 1, 1, 1, 1, 1, 1
                            ]
                        },
                        "post_run_batch": {
                            "material": "solvent",
                            "variable_type": "parameter",
                            "variable_name": "param2",
                            "values": [
                                1, 1, 1, 1, 1, 1, 2, 3, 4, 5
                            ]
                        }
                    }""")
        )
        actual = ordered(json.loads(
                json.dumps(self.plan, cls=SampleAssayPlanEncoder)
        ))
        self.assertTrue(expected == actual)

    @unittest.skip(
        'Serialization implementation incomplete (out of sync with model)')
    def test_serialize_sampleassayplan(self):
        self.plan.add_sample_type('water')
        self.plan.add_sample_qc_plan_record('water', 8)

        self.assay_type.topology_modifiers = self.top_mods

        self.plan.add_assay_type(self.assay_type)
        self.plan.add_assay_plan_record('liver', self.assay_type)
        self.plan.add_assay_plan_record('tissue', self.assay_type)

        expected = ordered(
            json.loads("""{
                "sample_types": ["liver", "tissue", "water"],
                "group_size": 20,
                "sample_plan": [
                    {
                        "sampling_size": 3,
                        "sample_type": "liver"
                    },
                    {
                        "sampling_size": 5,
                        "sample_type": "tissue"
                    }
                ],
                "sample_qc_plan": [
                    {
                        "injection_interval": 8,
                        "sample_type": "water"
                    }
                ],
                "assay_types": [
                    {
                        "topology_modifiers": {
                            "technical_replicates": 2,
                            "array_designs": ["A-AFFY-27", "A-AFFY-28"]
                        }, 
                        "technology_type": "DNA microarray", 
                        "measurement_type": "genome sequencing"
                    }],
                "assay_plan": [
                    {
                        "sample_type": "liver",
                        "assay_type": {
                            "topology_modifiers": {
                                "technical_replicates": 2,
                                "array_designs": ["A-AFFY-27", "A-AFFY-28"]
                            },
                            "technology_type": "DNA microarray",
                            "measurement_type": "genome sequencing"
                        }
                    },
                    {
                        "sample_type": "tissue",
                        "assay_type": {
                            "topology_modifiers": {
                                "technical_replicates": 2,
                                "array_designs": ["A-AFFY-27", "A-AFFY-28"]
                            }, 
                            "technology_type": "DNA microarray", 
                            "measurement_type": "genome sequencing"
                        }
                    }
                ]
            }""")
        )

        actual = ordered(
            json.loads(
                json.dumps(self.plan, cls=SampleAssayPlanEncoder)
            )
        )
        self.assertTrue(expected == actual)

    @unittest.skip(
        'Serialization implementation incomplete (out of sync with model)')
    def test_serialize_treatment_sequence(self):

        expected = ordered(json.loads("""{
            "rankedTreatments": [
                {
                    "treatment": {
                        "factorValues": [
                            {
                                "category": {
                                    "factorName": "AGENT",
                                    "factorType": {
                                        "annotationValue": "perturbation agent",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "calpol"
                            },
                            {
                                "category": {
                                    "factorName": "DURATION",
                                    "factorType": {
                                        "annotationValue": "time",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "long"
                            },
                            {
                                "category": {
                                    "factorName": "INTENSITY",
                                    "factorType": {
                                        "annotationValue": "intensity",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "high"
                            }
                        ],
                        "treatmentType": "chemical intervention"
                    },
                    "rank": 1
                },
                {
                    "treatment": {
                        "factorValues": [
                            {
                                "category": {
                                    "factorName": "AGENT",
                                    "factorType": {
                                        "annotationValue": "perturbation agent",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "calpol"
                            },
                            {
                                "category": {
                                    "factorName": "DURATION",
                                    "factorType": {
                                        "annotationValue": "time",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "short"
                            },
                            {
                                "category": {
                                    "factorName": "INTENSITY",
                                    "factorType": {
                                        "annotationValue": "intensity",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "low"
                            }
                        ],
                        "treatmentType": "chemical intervention"
                    },
                    "rank": 1
                },
                {
                    "treatment": {
                        "factorValues": [
                            {
                                "category": {
                                    "factorName": "AGENT",
                                    "factorType": {
                                        "annotationValue": "perturbation agent",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "no agent"
                            },
                            {
                                "category": {
                                    "factorName": "DURATION",
                                    "factorType": {
                                        "annotationValue": "time",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "long"
                            },
                            {
                                "category": {
                                    "factorName": "INTENSITY",
                                    "factorType": {
                                        "annotationValue": "intensity",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "low"
                            }
                        ],
                        "treatmentType": "chemical intervention"
                    },
                    "rank": 1
                },
                {
                    "treatment": {
                        "factorValues": [
                            {
                                "category": {
                                    "factorName": "AGENT",
                                    "factorType": {
                                        "annotationValue": "perturbation agent",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "calpol"
                            },
                            {
                                "category": {
                                    "factorName": "DURATION",
                                    "factorType": {
                                        "annotationValue": "time",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "short"
                            },
                            {
                                "category": {
                                    "factorName": "INTENSITY",
                                    "factorType": {
                                        "annotationValue": "intensity",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "high"
                            }
                        ],
                        "treatmentType": "chemical intervention"
                    },
                    "rank": 1
                },
                {
                    "treatment": {
                        "factorValues": [
                            {
                                "category": {
                                    "factorName": "AGENT",
                                    "factorType": {
                                        "annotationValue": "perturbation agent",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "calpol"
                            },
                            {
                                "category": {
                                    "factorName": "DURATION",
                                    "factorType": {
                                        "annotationValue": "time",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "long"
                            },
                            {
                                "category": {
                                    "factorName": "INTENSITY",
                                    "factorType": {
                                        "annotationValue": "intensity",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "low"
                            }
                        ],
                        "treatmentType": "chemical intervention"
                    },
                    "rank": 1
                },
                {
                    "treatment": {
                        "factorValues": [
                            {
                                "category": {
                                    "factorName": "AGENT",
                                    "factorType": {
                                        "annotationValue": "perturbation agent",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "no agent"
                            },
                            {
                                "category": {
                                    "factorName": "DURATION",
                                    "factorType": {
                                        "annotationValue": "time",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "short"
                            },
                            {
                                "category": {
                                    "factorName": "INTENSITY",
                                    "factorType": {
                                        "annotationValue": "intensity",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "low"
                            }
                        ],
                        "treatmentType": "chemical intervention"
                    },
                    "rank": 1
                },
                {
                    "treatment": {
                        "factorValues": [
                            {
                                "category": {
                                    "factorName": "AGENT",
                                    "factorType": {
                                        "annotationValue": "perturbation agent",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "no agent"
                            },
                            {
                                "category": {
                                    "factorName": "DURATION",
                                    "factorType": {
                                        "annotationValue": "time",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "short"
                            },
                            {
                                "category": {
                                    "factorName": "INTENSITY",
                                    "factorType": {
                                        "annotationValue": "intensity",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "high"
                            }
                        ],
                        "treatmentType": "chemical intervention"
                    },
                    "rank": 1
                },
                {
                    "treatment": {
                        "factorValues": [
                            {
                                "category": {
                                    "factorName": "AGENT",
                                    "factorType": {
                                        "annotationValue": "perturbation agent",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "no agent"
                            },
                            {
                                "category": {
                                    "factorName": "DURATION",
                                    "factorType": {
                                        "annotationValue": "time",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "long"
                            },
                            {
                                "category": {
                                    "factorName": "INTENSITY",
                                    "factorType": {
                                        "annotationValue": "intensity",
                                        "termSource": "",
                                        "termAccession": ""
                                    }
                                },
                                "value": "high"
                            }
                        ],
                        "treatmentType": "chemical intervention"
                    },
                    "rank": 1
                }
            ]
        }"""))

        actual = ordered(
            json.loads(
                json.dumps(self.treatment_sequence, cls=None)
            )
        )
        self.assertTrue(expected == actual)


class DecodeFromJsonTests(unittest.TestCase):

    def setUp(self):
        self.plan = SampleAssayPlan()
        self.plan.group_size = 20
        self.plan.add_sample_type('liver')
        self.plan.add_sample_type('tissue')
        self.plan.add_sample_plan_record('liver', 3)
        self.plan.add_sample_plan_record('tissue', 5)

        self.top_mods = DNAMicroAssayTopologyModifiers()
        self.top_mods.technical_replicates = 2
        self.top_mods.array_designs = {'A-AFFY-27', 'A-AFFY-28'}

        self.assay_type = AssayType(measurement_type='genome sequencing',
                                    technology_type='DNA microarray')

        factory = TreatmentFactory(intervention_type=INTERVENTIONS['CHEMICAL'],
                                   factors=BASE_FACTORS)
        factory.add_factor_value(BASE_FACTORS[0], 'calpol')
        factory.add_factor_value(BASE_FACTORS[0], 'no agent')
        factory.add_factor_value(BASE_FACTORS[1], 'low')
        factory.add_factor_value(BASE_FACTORS[1], 'high')
        factory.add_factor_value(BASE_FACTORS[2], 'short')
        factory.add_factor_value(BASE_FACTORS[2], 'long')
        self.treatment_sequence = TreatmentSequence(
            ranked_treatments=factory.compute_full_factorial_design())

    @unittest.skip(
        'Serialization implementation incomplete (out of sync with model)')
    def test_decode_sample_assay_plan_ms(self):
        decoder = SampleAssayPlanDecoder()
        sample_assay_plan = decoder.load(StringIO("""{
                        "sample_types": ["liver", "tissue", "water"],
                        "group_size": 20,
                        "sample_plan": [
                            {
                                "sampling_size": 3,
                                "sample_type": "liver"
                            },
                            {
                                "sampling_size": 5,
                                "sample_type": "tissue"
                            }
                        ],
                        "sample_qc_plan": [
                            {
                                "injection_interval": 8,
                                "sample_type": "water"
                            }
                        ],
                        "assay_types": [
                            {
                                "topology_modifiers": {
                                    "sample_fractions": ["polar", "non-polar"],
                                    "injection_modes": [
                                        {
                                            "injection_mode": "DI",
                                            "chromatography_column": null,
                                            "chromatography_instrument": "none reported",
                                            "instrument": null,
                                            "acquisition_modes": [{
                                                "acquisition_method": "positive",
                                                "technical_repeats": 1
                                            }]
                                        },
                                        {
                                            "injection_mode": "LC",
                                            "chromatography_column": "Chrom col",
                                            "chromatography_instrument": "Chrom instr",
                                            "instrument": "MS instr",
                                            "acquisition_modes": [
                                                {
                                                    "acquisition_method": "positive",
                                                    "technical_repeats": 2
                                                },
                                                {
                                                    "acquisition_method": "negative",
                                                    "technical_repeats": 2
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "technology_type": "metabolite profiling",
                                "measurement_type": "mass spectrometry"
                            }
                        ],
                        "assay_plan": [
                            {
                                "sample_type": "liver",
                                "assay_type": {
                                    "topology_modifiers": {
                                        "sample_fractions": ["polar", "non-polar"],
                                        "injection_modes": [
                                            {
                                                "injection_mode": "DI",
                                                "chromatography_column": null,
                                                "chromatography_instrument": "none reported",
                                                "instrument": null,
                                                "acquisition_modes": [{
                                                    "acquisition_method": "postitive/negative",
                                                    "technical_repeats": 1
                                                }]
                                            },
                                            {
                                                "injection_mode": "LC",
                                                "chromatography_column": "Chrom col",
                                                "chromatography_instrument": "Chrom instr",
                                                "instrument": "MS instr",
                                                "acquisition_modes": [
                                                    {
                                                        "acquisition_method": "postitive",
                                
                                                        "technical_repeats": 2
                                                    },
                                                    {
                                                        "acquisition_method": "negative",
                                                        "technical_repeats": 2
                                                    }
                                                ]
                                            }
                                        ]
                                    },
                                    "technology_type": "metabolite profiling",
                                    "measurement_type": "mass spectrometry"
                                }
                            }
                        ],
                        "pre_run_batch": {},
                        "post_run_batch": {}
                    }"""))
        plan = SampleAssayPlan()
        assay_type = AssayType(
            measurement_type=OntologyAnnotation(term='metabolite profiling'),
            technology_type=OntologyAnnotation(term='mass spectrometry')
        )
        topology_modifiers = MSTopologyModifiers()
        topology_modifiers.sample_fractions.add('polar')
        topology_modifiers.sample_fractions.add('non=polar')
        assay_type.topology_modifiers = topology_modifiers
        injection_mode_di = MSInjectionMode()
        injection_mode_di.acquisition_modes.add(MSAcquisitionMode(
            acquisition_method='positive/negative',
            technical_repeats=1
        ))
        topology_modifiers.injection_modes.add(injection_mode_di)
        injection_mode_lc = MSInjectionMode(
            injection_mode='LC', chromatography_column='Chrom col',
            chromatography_instrument='Chrom instr', ms_instrument='MS instr')
        injection_mode_lc.acquisition_modes.add(MSAcquisitionMode(
            acquisition_method='positive', technical_repeats=2
        ))
        injection_mode_lc.acquisition_modes.add(MSAcquisitionMode(
            acquisition_method='negative', technical_repeats=2
        ))
        plan.add_assay_type(assay_type)

    @unittest.skip(
        'Serialization implementation incomplete (out of sync with model)')
    def test_decode_sample_assay_plan(self):
        decoder = SampleAssayPlanDecoder()
        sample_assay_plan = decoder.load(StringIO("""{
                "sample_types": ["liver", "tissue", "water"],
                "group_size": 20,
                "sample_plan": [
                    {
                        "sampling_size": 3,
                        "sample_type": "liver"
                    },
                    {
                        "sampling_size": 5,
                        "sample_type": "tissue"
                    }
                ],
                "sample_qc_plan": [
                    {
                        "injection_interval": 8,
                        "sample_type": "water"
                    }
                ],
                "assay_types": [
                    {
                        "topology_modifiers": {
                            "technical_replicates": 2,
                            "array_designs": ["A-AFFY-27", "A-AFFY-28"]
                        }, 
                        "technology_type": "DNA microarray", 
                        "measurement_type": "genome sequencing"
                    }],
                "assay_plan": [
                    {
                        "sample_type": "liver",
                        "assay_type": {
                            "topology_modifiers": {
                                "technical_replicates": 2,
                                "array_designs": ["A-AFFY-27", "A-AFFY-28"]
                            },
                            "technology_type": "DNA microarray",
                            "measurement_type": "genome sequencing"
                        }
                    },
                    {
                        "sample_type": "tissue",
                        "assay_type": {
                            "topology_modifiers": {
                                "technical_replicates": 2,
                                "array_designs": ["A-AFFY-27", "A-AFFY-28"]
                            }, 
                            "technology_type": "DNA microarray", 
                            "measurement_type": "genome sequencing"
                        }
                    }
                ],
                "pre_run_batch": {},
                "post_run_batch": {}
            }"""))

        self.plan.add_sample_type('water')
        self.plan.add_sample_qc_plan_record('water', 8)

        self.assay_type.topology_modifiers = self.top_mods

        self.plan.add_assay_type(self.assay_type)
        self.plan.add_assay_plan_record('liver', self.assay_type)
        self.plan.add_assay_plan_record('tissue', self.assay_type)

        self.assertEqual(sample_assay_plan, self.plan)

    @unittest.skip(
        'Serialization implementation incomplete (out of sync with model)')
    def test_IsaModelFactory_NMR_serialization_issue_293(self):
        decoder = SampleAssayPlanDecoder()
        sample_assay_plan = decoder.load(StringIO("""{
                "sample_types": ["liver", "tissue", "water"],
                "group_size": 20,
                "sample_plan": [
                    {
                        "sampling_size": 3,
                        "sample_type": "liver"
                    },
                    {
                        "sampling_size": 5,
                        "sample_type": "tissue"
                    }
                ],
                "sample_qc_plan": [
                    {
                        "injection_interval": 8,
                        "sample_type": "water"
                    }
                ],
                "assay_types": [
                    {
                        "topology_modifiers": {
                            "technical_replicates": 2,
                            "injection_modes": [],
                            "instruments": ["Instrument A"],
                            "pulse_sequences": ["TOCSY"],
                            "acquisition_modes": ["mode1"]
                        }, 
                        "technology_type": "nmr spectroscopy",
                        "measurement_type": "metabolite profiling"
                    }],
                "assay_plan": [
                    {
                        "sample_type": "liver",
                        "assay_type": {
                            "topology_modifiers": {
                                "technical_replicates": 2,
                                "injection_modes": [],
                                "instruments": ["Instrument A"],
                                "pulse_sequences": ["TOCSY"],
                                "acquisition_modes": ["mode1"]
                            },
                            "technology_type": "nmr spectroscopy",
                            "measurement_type": "metabolite profiling"
                        }
                    },
                    {
                        "sample_type": "tissue",
                        "assay_type": {
                            "topology_modifiers": {
                                "technical_replicates": 2,
                                "injection_modes": [],
                                "instruments": ["Instrument A"],
                                "pulse_sequences": ["TOCSY"],
                                "acquisition_modes": ["mode1"]
                            }, 
                            "technology_type": "nmr spectroscopy", 
                            "measurement_type": "metabolite profiling"
                        }
                    }
                ]
            }"""))

        with open(os.path.join(utils.JSON_DATA_DIR, 'create',
                               'treatment_sequence_test.json')) as json_fp:
            treatment_plan = TreatmentSequenceDecoder().load(json_fp)
        study_design = StudyDesign()
        study_design.add_single_sequence_plan(treatment_plan, sample_assay_plan)
        isa_object_factory = IsaModelObjectFactory(study_design)
        study = isa_object_factory.create_assays_from_plan()
        self.assertEqual(len(study.assays), 2)

    @unittest.skip(
        'Serialization implementation incomplete (out of sync with model)')
    def test_create_from_decoded_json(self):
        with open(os.path.join(
                utils.JSON_DATA_DIR, 'create', 'sampleassayplan_test.json')) \
                as json_fp:
            sample_assay_plan = SampleAssayPlanDecoder().load(json_fp)
        with open(
                os.path.join(utils.JSON_DATA_DIR, 'create',
                             'treatment_sequence_test.json')) as json_fp:
            treatment_plan = TreatmentSequenceDecoder().load(json_fp)
        study_design = StudyDesign()
        study_design.add_single_sequence_plan(treatment_plan, sample_assay_plan)
        isa_object_factory = IsaModelObjectFactory(study_design)
        study = isa_object_factory.create_assays_from_plan()
        self.assertEqual(len(study.sources), 80)
        self.assertEqual(len(study.samples), 360)
        self.assertEqual(len(study.process_sequence), 360)

    @unittest.skip(
        'Serialization implementation incomplete (out of sync with model)')
    def test_decode_treatment_sequence(self):
        decoder = TreatmentSequenceDecoder()
        treatment_sequence = decoder.load(StringIO("""{
            "rankedTreatments": [
                {
                    "treatment": {
                        "factorValues": [
                            {
                                "category": {
                                    "factorName": "AGENT",
                                    "factorType": {
                                        "annotationValue": "perturbation agent",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "calpol"
                            },
                            {
                                "category": {
                                    "factorName": "DURATION",
                                    "factorType": {
                                        "annotationValue": "time",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "long"
                            },
                            {
                                "category": {
                                    "factorName": "INTENSITY",
                                    "factorType": {
                                        "annotationValue": "intensity",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "high"
                            }
                        ],
                        "treatmentType": "chemical intervention"
                    },
                    "rank": 1
                },
                {
                    "treatment": {
                        "factorValues": [
                            {
                                "category": {
                                    "factorName": "AGENT",
                                    "factorType": {
                                        "annotationValue": "perturbation agent",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "calpol"
                            },
                            {
                                "category": {
                                    "factorName": "DURATION",
                                    "factorType": {
                                        "annotationValue": "time",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "short"
                            },
                            {
                                "category": {
                                    "factorName": "INTENSITY",
                                    "factorType": {
                                        "annotationValue": "intensity",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "low"
                            }
                        ],
                        "treatmentType": "chemical intervention"
                    },
                    "rank": 1
                },
                {
                    "treatment": {
                        "factorValues": [
                            {
                                "category": {
                                    "factorName": "AGENT",
                                    "factorType": {
                                        "annotationValue": "perturbation agent",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "no agent"
                            },
                            {
                                "category": {
                                    "factorName": "DURATION",
                                    "factorType": {
                                        "annotationValue": "time",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "long"
                            },
                            {
                                "category": {
                                    "factorName": "INTENSITY",
                                    "factorType": {
                                        "annotationValue": "intensity",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "low"
                            }
                        ],
                        "treatmentType": "chemical intervention"
                    },
                    "rank": 1
                },
                {
                    "treatment": {
                        "factorValues": [
                            {
                                "category": {
                                    "factorName": "AGENT",
                                    "factorType": {
                                        "annotationValue": "perturbation agent",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "calpol"
                            },
                            {
                                "category": {
                                    "factorName": "DURATION",
                                    "factorType": {
                                        "annotationValue": "time",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "short"
                            },
                            {
                                "category": {
                                    "factorName": "INTENSITY",
                                    "factorType": {
                                        "annotationValue": "intensity",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "high"
                            }
                        ],
                        "treatmentType": "chemical intervention"
                    },
                    "rank": 1
                },
                {
                    "treatment": {
                        "factorValues": [
                            {
                                "category": {
                                    "factorName": "AGENT",
                                    "factorType": {
                                        "annotationValue": "perturbation agent",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "calpol"
                            },
                            {
                                "category": {
                                    "factorName": "DURATION",
                                    "factorType": {
                                        "annotationValue": "time",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "long"
                            },
                            {
                                "category": {
                                    "factorName": "INTENSITY",
                                    "factorType": {
                                        "annotationValue": "intensity",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "low"
                            }
                        ],
                        "treatmentType": "chemical intervention"
                    },
                    "rank": 1
                },
                {
                    "treatment": {
                        "factorValues": [
                            {
                                "category": {
                                    "factorName": "AGENT",
                                    "factorType": {
                                        "annotationValue": "perturbation agent",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "no agent"
                            },
                            {
                                "category": {
                                    "factorName": "DURATION",
                                    "factorType": {
                                        "annotationValue": "time",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "short"
                            },
                            {
                                "category": {
                                    "factorName": "INTENSITY",
                                    "factorType": {
                                        "annotationValue": "intensity",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "low"
                            }
                        ],
                        "treatmentType": "chemical intervention"
                    },
                    "rank": 1
                },
                {
                    "treatment": {
                        "factorValues": [
                            {
                                "category": {
                                    "factorName": "AGENT",
                                    "factorType": {
                                        "annotationValue": "perturbation agent",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "no agent"
                            },
                            {
                                "category": {
                                    "factorName": "DURATION",
                                    "factorType": {
                                        "annotationValue": "time",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "short"
                            },
                            {
                                "category": {
                                    "factorName": "INTENSITY",
                                    "factorType": {
                                        "annotationValue": "intensity",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "high"
                            }
                        ],
                        "treatmentType": "chemical intervention"
                    },
                    "rank": 1
                },
                {
                    "treatment": {
                        "factorValues": [
                            {
                                "category": {
                                    "factorName": "AGENT",
                                    "factorType": {
                                        "annotationValue": "perturbation agent",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "no agent"
                            },
                            {
                                "category": {
                                    "factorName": "DURATION",
                                    "factorType": {
                                        "annotationValue": "time",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "long"
                            },
                            {
                                "category": {
                                    "factorName": "INTENSITY",
                                    "factorType": {
                                        "annotationValue": "intensity",
                                        "termSource": null,
                                        "termAccession": ""
                                    }
                                },
                                "value": "high"
                            }
                        ],
                        "treatmentType": "chemical intervention"
                    },
                    "rank": 1
                }
            ]
        }"""))

        self.assertEqual(
            repr(treatment_sequence), repr(self.treatment_sequence))

    @unittest.skip(
        'Serialization implementation incomplete (out of sync with model)')
    def test_summary_from_treatment_sequence(self):
        decoder = TreatmentSequenceDecoder()
        treatment_sequence = decoder.load(StringIO("""{
                    "rankedTreatments": [
                        {
                            "treatment": {
                                "factorValues": [
                                    {
                                        "category": {
                                            "factorName": "AGENT",
                                            "factorType": {
                                                "annotationValue": "perturbation agent",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "calpol"
                                    },
                                    {
                                        "category": {
                                            "factorName": "DURATION",
                                            "factorType": {
                                                "annotationValue": "time",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "long"
                                    },
                                    {
                                        "category": {
                                            "factorName": "INTENSITY",
                                            "factorType": {
                                                "annotationValue": "intensity",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "high"
                                    }
                                ],
                                "treatmentType": "chemical intervention"
                            },
                            "rank": 1
                        },
                        {
                            "treatment": {
                                "factorValues": [
                                    {
                                        "category": {
                                            "factorName": "AGENT",
                                            "factorType": {
                                                "annotationValue": "perturbation agent",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "calpol"
                                    },
                                    {
                                        "category": {
                                            "factorName": "DURATION",
                                            "factorType": {
                                                "annotationValue": "time",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "short"
                                    },
                                    {
                                        "category": {
                                            "factorName": "INTENSITY",
                                            "factorType": {
                                                "annotationValue": "intensity",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "low"
                                    }
                                ],
                                "treatmentType": "chemical intervention"
                            },
                            "rank": 1
                        },
                        {
                            "treatment": {
                                "factorValues": [
                                    {
                                        "category": {
                                            "factorName": "AGENT",
                                            "factorType": {
                                                "annotationValue": "perturbation agent",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "no agent"
                                    },
                                    {
                                        "category": {
                                            "factorName": "DURATION",
                                            "factorType": {
                                                "annotationValue": "time",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "long"
                                    },
                                    {
                                        "category": {
                                            "factorName": "INTENSITY",
                                            "factorType": {
                                                "annotationValue": "intensity",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "low"
                                    }
                                ],
                                "treatmentType": "chemical intervention"
                            },
                            "rank": 1
                        },
                        {
                            "treatment": {
                                "factorValues": [
                                    {
                                        "category": {
                                            "factorName": "AGENT",
                                            "factorType": {
                                                "annotationValue": "perturbation agent",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "calpol"
                                    },
                                    {
                                        "category": {
                                            "factorName": "DURATION",
                                            "factorType": {
                                                "annotationValue": "time",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "short"
                                    },
                                    {
                                        "category": {
                                            "factorName": "INTENSITY",
                                            "factorType": {
                                                "annotationValue": "intensity",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "high"
                                    }
                                ],
                                "treatmentType": "chemical intervention"
                            },
                            "rank": 1
                        },
                        {
                            "treatment": {
                                "factorValues": [
                                    {
                                        "category": {
                                            "factorName": "AGENT",
                                            "factorType": {
                                                "annotationValue": "perturbation agent",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "calpol"
                                    },
                                    {
                                        "category": {
                                            "factorName": "DURATION",
                                            "factorType": {
                                                "annotationValue": "time",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "long"
                                    },
                                    {
                                        "category": {
                                            "factorName": "INTENSITY",
                                            "factorType": {
                                                "annotationValue": "intensity",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "low"
                                    }
                                ],
                                "treatmentType": "chemical intervention"
                            },
                            "rank": 1
                        },
                        {
                            "treatment": {
                                "factorValues": [
                                    {
                                        "category": {
                                            "factorName": "AGENT",
                                            "factorType": {
                                                "annotationValue": "perturbation agent",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "no agent"
                                    },
                                    {
                                        "category": {
                                            "factorName": "DURATION",
                                            "factorType": {
                                                "annotationValue": "time",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "short"
                                    },
                                    {
                                        "category": {
                                            "factorName": "INTENSITY",
                                            "factorType": {
                                                "annotationValue": "intensity",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "low"
                                    }
                                ],
                                "treatmentType": "chemical intervention"
                            },
                            "rank": 1
                        },
                        {
                            "treatment": {
                                "factorValues": [
                                    {
                                        "category": {
                                            "factorName": "AGENT",
                                            "factorType": {
                                                "annotationValue": "perturbation agent",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "no agent"
                                    },
                                    {
                                        "category": {
                                            "factorName": "DURATION",
                                            "factorType": {
                                                "annotationValue": "time",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "short"
                                    },
                                    {
                                        "category": {
                                            "factorName": "INTENSITY",
                                            "factorType": {
                                                "annotationValue": "intensity",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "high"
                                    }
                                ],
                                "treatmentType": "chemical intervention"
                            },
                            "rank": 1
                        },
                        {
                            "treatment": {
                                "factorValues": [
                                    {
                                        "category": {
                                            "factorName": "AGENT",
                                            "factorType": {
                                                "annotationValue": "perturbation agent",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "no agent"
                                    },
                                    {
                                        "category": {
                                            "factorName": "DURATION",
                                            "factorType": {
                                                "annotationValue": "time",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "long"
                                    },
                                    {
                                        "category": {
                                            "factorName": "INTENSITY",
                                            "factorType": {
                                                "annotationValue": "intensity",
                                                "termSource": null,
                                                "termAccession": ""
                                            }
                                        },
                                        "value": "high"
                                    }
                                ],
                                "treatmentType": "chemical intervention"
                            },
                            "rank": 1
                        }
                    ]
                }"""))
        report = make_summary_from_treatment_sequence(treatment_sequence)
        expected_report = """{
    "number_of_treatment": 8,
    "number_of_factors": 3,
    "length_of_treatment_sequence": 1,
    "number_of_treatments": 8,
    "full_factorial": true,
    "list_of_treatments": [
        [
            {
                "factor": "INTENSITY",
                "value": "high"
            },
            {
                "factor": "AGENT",
                "value": "no agent"
            },
            {
                "factor": "DURATION",
                "value": "short"
            }
        ],
        [
            {
                "factor": "AGENT",
                "value": "no agent"
            },
            {
                "factor": "INTENSITY",
                "value": "low"
            },
            {
                "factor": "DURATION",
                "value": "short"
            }
        ],
        [
            {
                "factor": "AGENT",
                "value": "no agent"
            },
            {
                "factor": "INTENSITY",
                "value": "low"
            },
            {
                "factor": "DURATION",
                "value": "long"
            }
        ],
        [
            {
                "factor": "AGENT",
                "value": "calpol"
            },
            {
                "factor": "INTENSITY",
                "value": "low"
            },
            {
                "factor": "DURATION",
                "value": "short"
            }
        ],
        [
            {
                "factor": "AGENT",
                "value": "calpol"
            },
            {
                "factor": "INTENSITY",
                "value": "high"
            },
            {
                "factor": "DURATION",
                "value": "short"
            }
        ],
        [
            {
                "factor": "AGENT",
                "value": "calpol"
            },
            {
                "factor": "INTENSITY",
                "value": "low"
            },
            {
                "factor": "DURATION",
                "value": "long"
            }
        ],
        [
            {
                "factor": "INTENSITY",
                "value": "high"
            },
            {
                "factor": "AGENT",
                "value": "no agent"
            },
            {
                "factor": "DURATION",
                "value": "long"
            }
        ],
        [
            {
                "factor": "AGENT",
                "value": "calpol"
            },
            {
                "factor": "INTENSITY",
                "value": "high"
            },
            {
                "factor": "DURATION",
                "value": "long"
            }
        ]
    ],
    "number_of_factor_levels_per_factor": {
        "AGENT": [
            "calpol",
            "no agent"
        ],
        "INTENSITY": [
            "high",
            "low"
        ],
        "DURATION": [
            "short",
            "long"
        ]
    }
}"""
        self.assertEqual(sorted(json.loads(expected_report)), sorted(report))