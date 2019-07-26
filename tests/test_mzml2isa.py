import unittest
import shutil
from isatools.convert import mzml2isa
from isatools.tests.utils import assert_tab_content_equal
from isatools.tests import utils
import tempfile
import os
from io import StringIO


class TestMzml2IsaTab(unittest.TestCase):

    def setUp(self):
        self._mzml_data_dir = utils.MZML_DATA_DIR
        self._tab_data_dir = utils.TAB_DATA_DIR
        self._tmp_dir = tempfile.mkdtemp()

    # def tearDown(self):
    #     shutil.rmtree(self._tmp_dir)

    def test_mzml2isa_convert_investigation(self):
        study_id = 'MTBLS267'
        report = mzml2isa.convert(os.path.join(self._mzml_data_dir, study_id + '-partial'), self._tmp_dir, study_id,
                                  validate_output=True)
        self.assertTrue(report['validation_finished'])
        self.assertEqual(len(report['errors']), 0)
        # Strip out the line with Comment[Created With Tool] to avoid changes in version number generated by mzml2isa
        with open(os.path.join(self._tmp_dir, 'i_Investigation.txt')) as in_fp, StringIO() as stripped_actual_file:
            stripped_actual_file.name = 'i_Investigation.txt'
            for row in in_fp:
                if row.startswith('Comment[Created With Tool]'):
                    pass
                else:
                    stripped_actual_file.write(row)
            stripped_actual_file.seek(0)
            with open(os.path.join(self._tab_data_dir, study_id + '-partial', 'i_Investigation.txt')) as reference_fp:
                self.assertTrue(assert_tab_content_equal(stripped_actual_file, reference_fp))

    def test_mzml2isa_convert_study_table(self):
        study_id = 'MTBLS267'
        report = mzml2isa.convert(os.path.join(self._mzml_data_dir, study_id + '-partial'), self._tmp_dir, study_id,
                                  validate_output=True)
        self.assertTrue(report['validation_finished'])
        self.assertEqual(len(report['errors']), 0)
        with open(os.path.join(self._tmp_dir, 's_{}.txt'.format(study_id))) as out_fp:
            with open(os.path.join(self._tab_data_dir, study_id + '-partial', 's_{}.txt'.format(study_id))) as reference_fp:
                self.assertTrue(assert_tab_content_equal(out_fp, reference_fp))

    def test_mzml2isa_convert_assay_table(self):
        study_id = 'MTBLS267'
        report = mzml2isa.convert(os.path.join(self._mzml_data_dir, study_id + '-partial'), self._tmp_dir, study_id,
                                  validate_output=True)
        self.assertTrue(report['validation_finished'])
        self.assertEqual(len(report['errors']), 0)
        with open(os.path.join(self._tmp_dir, 'a_{}_metabolite_profiling_mass_spectrometry.txt'.format(study_id))) as out_fp:
            with open(os.path.join(self._tab_data_dir, study_id + '-partial', 'a_{}_metabolite_profiling_mass_spectrometry.txt'.format(study_id))) as reference_fp:
                self.assertTrue(assert_tab_content_equal(out_fp, reference_fp))
