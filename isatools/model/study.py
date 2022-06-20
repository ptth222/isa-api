from typing import List
from collections.abc import Iterable

from isatools.model.assay import Assay
from isatools.model.comments import Commentable
from isatools.model.mixins import StudyAssayMixin, MetadataMixin
from isatools.model.ontology_annotation import OntologyAnnotation
from isatools.model.protocol import Protocol
from isatools.model.protocol_parameter import ProtocolParameter
from isatools.model.factor_value import StudyFactor
from isatools.model.publication import Publication
from isatools.model.person import Person
from isatools.model.source import Source
from isatools.model.sample import Sample
from isatools.model.process import Process
from isatools.model.logger import log
from isatools.model.loader_indexes import loader_states as indexes


class Study(Commentable, StudyAssayMixin, MetadataMixin, object):
    """Study is the central unit, containing information on the subject under
    study, its characteristics and any treatments applied.

    Attributes:
        identifier: A unique identifier: either a temporary identifier
        supplied by users or one generated by a repository or other database.
        title: A concise phrase used to encapsulate the purpose and goal of
        the study.
        description: A textual description of the study, with components such
            as objective or goals.
        submission_date: The date on which the study was reported to the
            repository. This should be ISO8601 formatted.
        public_release_date: The date on which the study should be released
            publicly. This should be ISO8601 formatted.
        filename: A field to specify the name of the Study file corresponding
            the definition of that Study.
        design_descriptors: Classifications of the study based on the overall
            experimental design.
        publications: A list of Publications associated with the Study.
        contacts: A list of People/contacts associated with the Study.
        factors: A factor corresponds to an independent variable manipulated by
            the experimentalist with the intention to affect biological systems
            in a way that can be measured by an assay.
        protocols: Protocols used within the ISA artifact.
        assays: An Assay represents a portion of the experimental design.
        materials: Materials associated with the study, contains lists of
            'sources', 'samples' and 'other_material'. DEPRECATED.
        sources: Sources associated with the study, is equivalent to
            materials['sources'].
        samples: Samples associated with the study, is equivalent to
            materials['samples'].
        other_material: Other Materials associated with the study, is
            equivalent to materials['other_material'].
        units: A list of Units used in the annotation of material units in the
            study.
        characteristic_categories: Annotations of material characteristics used
            in the study.
        process_sequence: A list of Process objects representing the
            experimental graphs at the study level.
        comments: Comments associated with instances of this class.
        graph: Graph representation of the study graph.
    """

    def __init__(self, id_='', filename='', identifier='', title='',
                 description='', submission_date='', public_release_date='',
                 contacts=None, design_descriptors=None, publications=None,
                 factors=None, protocols=None, assays=None, sources=None,
                 samples=None, process_sequence=None, other_material=None,
                 characteristic_categories=None, comments=None, units=None):
        MetadataMixin.__init__(self, filename=filename, identifier=identifier,
                               title=title, description=description,
                               submission_date=submission_date,
                               public_release_date=public_release_date,
                               publications=publications, contacts=contacts)
        StudyAssayMixin.__init__(
            self, filename=filename, sources=sources,
            samples=samples,
            other_material=other_material,
            process_sequence=process_sequence,
            characteristic_categories=characteristic_categories,
            units=units)
        Commentable.__init__(self, comments=comments)

        self.id = id_

        if design_descriptors is None:
            self.__design_descriptors = []
        else:
            self.__design_descriptors = design_descriptors

        if protocols is None:
            self.__protocols = []
        else:
            self.__protocols = protocols

        if assays is None:
            self.__assays = []
        else:
            self.__assays = assays

        if factors is None:
            self.__factors = []
        else:
            self.__factors = factors

    @property
    def design_descriptors(self):
        """:obj:`list` of :obj:`OntologyAnnotation`: Container for study design
        descriptors"""
        return self.__design_descriptors

    @design_descriptors.setter
    def design_descriptors(self, val):
        if val is not None and hasattr(val, '__iter__'):
            if val == [] or all(isinstance(x, OntologyAnnotation) for x in val):
                self.__design_descriptors = list(val)
        else:
            raise AttributeError('{}.design_descriptors must be iterable containing OntologyAnnotations'
                                 .format(type(self).__name__))

    @property
    def protocols(self):
        """:obj:`list` of :obj:`Protocol`: Container for study protocols"""
        return self.__protocols

    @protocols.setter
    def protocols(self, val):
        """
        if val is not None and hasattr(val, '__iter__'):
            if val == [] or all(isinstance(x, Protocol) for x in val):
                self.__protocols = list(val)
        else:
            raise ISAModelAttributeError(
                '{}.protocols must be iterable containing Protocol'
                .format(type(self).__name__))
        """
        if not isinstance(val, Iterable) or not all(isinstance(el, Protocol) for el in val):
            raise AttributeError('The object supplied is not an iterable of Protocol objects')
        self.__protocols = [protocol for protocol in val]

    def add_protocol(self, protocol):
        if not isinstance(protocol, Protocol):
            raise TypeError('The object supplied is not an instance of Protocol')
        if protocol not in self.protocols:
            self.__protocols.append(protocol)

    @staticmethod
    def __get_default_protocol(protocol_type):
        """Return default Protocol object based on protocol_type and from isaconfig_v2015-07-02"""
        default_protocol = Protocol(protocol_type=OntologyAnnotation(term=protocol_type))
        parameter_list = []

        parameter_list_index = {
            'mass spectrometry': [
                'instrument',
                'ion source',
                'detector',
                'analyzer',
                'chromatography instrument',
                'chromatography column'
            ],
            'nmr spectroscopy': [
                'instrument',
                'NMR probe',
                'number of acquisition',
                'magnetic field strength',
                'pulse sequence'
            ],
            'nucleic acid hybridization': ['Array Design REF'],
            'nucleic acid sequencing': ['sequencing instrument', 'quality scorer', 'base caller']
        }
        if protocol_type in parameter_list_index:
            parameter_list = parameter_list_index[protocol_type]
        default_protocol.parameters = [ProtocolParameter(parameter_name=OntologyAnnotation(term=x))
                                       for x in parameter_list]
        # TODO: Implement this for other defaults OR generate from config #51
        return default_protocol

    def add_prot(self,
                 protocol_name='',
                 protocol_type=None,
                 use_default_params=True):
        if self.get_prot(protocol_name=protocol_name) is not None:
            log.warning('A protocol with name "{}" has already been declared in the study'.format(protocol_name))
        else:
            if isinstance(protocol_type, str) and use_default_params:
                default_protocol = self.__get_default_protocol(protocol_type)
                default_protocol.name = protocol_name
                self.protocols.append(default_protocol)
            else:
                self.protocols.append(Protocol(name=protocol_name,
                                               protocol_type=OntologyAnnotation(term=protocol_type)))

    def get_prot(self, protocol_name):
        prot = None
        try:
            prot = next(x for x in self.protocols if x.name == protocol_name)
        except StopIteration:
            pass
        return prot

    def add_factor(self, name, factor_type):
        if self.get_factor(name=name) is not None:
            log.warning('A factor with name "{}" has already been declared in the study'.format(name))
        else:
            self.factors.append(StudyFactor(name=name, factor_type=OntologyAnnotation(term=factor_type)))

    def del_factor(self, name, are_you_sure=False):
        if self.get_factor(name=name) is None:
            log.warning('A factor with name "{}" has not been found in the study'.format(name))
        else:
            if are_you_sure:  # force user to say yes, to be sure to be sure
                self.factors.remove(self.get_factor(name=name))

    def get_factor(self, name):
        factor = None
        try:
            factor = next(x for x in self.factors if x.name == name)
        except StopIteration:
            pass
        return factor

    @property
    def assays(self):
        """:obj:`list` of :obj:`Assay`: Container for study Assays"""
        return self.__assays

    @assays.setter
    def assays(self, val):
        if val is not None and hasattr(val, '__iter__'):
            if val == [] or all(isinstance(x, Assay) for x in val):
                self.__assays = list(val)
        else:
            raise AttributeError('{}.assays must be iterable containing Assays'.format(type(self).__name__))

    @property
    def factors(self):
        """:obj:`list` of :obj:`StudyFactor`: Container for study
        StudyFactors"""
        return self.__factors

    @factors.setter
    def factors(self, val):
        if val is not None and hasattr(val, '__iter__'):
            if val == [] or all(isinstance(x, StudyFactor) for x in val):
                self.__factors = list(val)
        else:
            raise AttributeError('{}.factors must be iterable containing StudyFactors'.format(type(self).__name__))

    def __repr__(self):
        return "isatools.model.Study(filename='{study.filename}', " \
               "identifier='{study.identifier}', title='{study.title}', " \
               "description='{study.description}', " \
               "submission_date='{study.submission_date}', " \
               "public_release_date='{study.public_release_date}', " \
               "contacts={study.contacts}, " \
               "design_descriptors={study.design_descriptors}, " \
               "publications={study.publications}, factors={study.factors}, " \
               "protocols={study.protocols}, assays={study.assays}, " \
               "sources={study.sources}, samples={study.samples}, " \
               "process_sequence={study.process_sequence}, " \
               "other_material={study.other_material}, " \
               "characteristic_categories={study.characteristic_categories}," \
               " comments={study.comments}, units={study.units})" \
            .format(study=self)

    def __str__(self):
        return """Study(
    identifier={study.identifier}
    filename={study.filename}
    title={study.title}
    description={study.description}
    submission_date={study.submission_date}
    public_release_date={study.public_release_date}
    contacts={num_contacts} Person objects
    design_descriptors={num_design_descriptors} OntologyAnnotation objects
    publications={num_publications} Publication objects
    factors={num_study_factors} StudyFactor objects
    protocols={num_protocols} Protocol objects
    assays={num_assays} Assay objects
    sources={num_sources} Source objects
    samples={num_samples} Sample objects
    process_sequence={num_processes} Process objects
    other_material={num_other_material} Material objects
    characteristic_categories={num_characteristic_categories} OntologyAnnots
    comments={num_comments} Comment objects
    units={num_units} Unit objects
)""".format(study=self, num_contacts=len(self.contacts),
            num_design_descriptors=len(self.design_descriptors),
            num_publications=len(self.publications),
            num_study_factors=len(self.factors),
            num_protocols=len(self.protocols),
            num_assays=len(self.assays),
            num_sources=len(self.sources),
            num_samples=len(self.samples),
            num_processes=len(self.process_sequence),
            num_other_material=len(self.other_material),
            num_characteristic_categories=len(self.characteristic_categories),
            num_comments=len(self.comments),
            num_units=len(self.units))

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other):
        return isinstance(other, Study) \
               and self.filename == other.filename \
               and self.identifier == other.identifier \
               and self.title == other.title \
               and self.description == other.description \
               and self.submission_date == other.submission_date \
               and self.public_release_date == other.public_release_date \
               and self.contacts == other.contacts \
               and self.design_descriptors == other.design_descriptors \
               and self.publications == other.publications \
               and self.factors == other.factors \
               and self.protocols == other.protocols \
               and self.assays == other.assays \
               and self.sources == other.sources \
               and self.samples == other.samples \
               and self.process_sequence == other.process_sequence \
               and self.other_material == other.other_material \
               and self.characteristic_categories == other.characteristic_categories \
               and self.comments == other.comments \
               and self.units == other.units

    def __ne__(self, other):
        return not self == other

    def shuffle_assays(self, targets: List) -> None:
        """
        Given a material type, provides a randomisation order for the materials of that type in each assay
        :param targets: a list of material types
        """
        for assay in self.assays:
            for target in targets:
                assay.shuffle_materials(target)

    def to_dict(self):
        return {
            "filename": self.filename,
            "identifier": self.identifier,
            "title": self.title,
            "description": self.description,
            "submissionDate": self.submission_date,
            "publicReleaseDate": self.public_release_date,
            "publications": [publication.to_dict() for publication in self.publications],
            "people": [person.to_dict() for person in self.contacts],
            "studyDesignDescriptors": [descriptor.to_dict() for descriptor in self.design_descriptors],
            "protocols": [protocol.to_dict() for protocol in self.protocols],
            "materials": {
                "sources": [source.to_dict() for source in self.sources],
                "samples": [sample.to_dict() for sample in self.samples],
                "otherMaterials": [mat.to_dict() for mat in self.other_material],
            },
            "processSequence": [process.to_dict() for process in self.process_sequence],
            "factors": [factor.to_dict() for factor in self.factors],
            "characteristicCategories": self.categories_to_dict(),
            "unitCategories": [unit.to_dict() for unit in self.units],
            "comments": [comment.to_dict() for comment in self.comments],
            "assays": [assay.to_dict() for assay in self.assays]
        }

    def from_dict(self, study):
        self.filename = study.get('filename', '')
        self.identifier = study.get('identifier', '')
        self.title = study.get('title', '')
        self.description = study.get('description', '')
        self.submission_date = study.get('submissionDate', '')
        self.public_release_date = study.get('publicReleaseDate', '')
        self.load_comments(study.get('comments', []))

        # Build characteristic categories index
        for assay in study.get('assays', []):
            for characteristic_category in assay['characteristicCategories']:
                category = OntologyAnnotation()
                category.from_dict(characteristic_category)
                indexes.add_characteristic_category(category)
        for characteristic_category in study.get('characteristicCategories', []):
            category = OntologyAnnotation()
            category.from_dict(characteristic_category)
            self.characteristic_categories.append(category)
            indexes.add_characteristic_category(category)

        # Units
        for unit_data in study.get('unitCategories', []):
            unit = OntologyAnnotation()
            unit.from_dict(unit_data)
            self.units.append(unit)
            indexes.add_unit(unit)

        # Publications
        for publication_data in study.get('publications', []):
            publication = Publication()
            publication.from_dict(publication_data)
            self.publications.append(publication)

        # People
        for person_data in study.get('people', []):
            person = Person()
            person.from_dict(person_data)
            self.contacts.append(person)

        # Design descriptors
        for descriptor_data in study.get('studyDesignDescriptors', []):
            descriptor = OntologyAnnotation()
            descriptor.from_dict(descriptor_data)
            self.design_descriptors.append(descriptor)

        # Protocols
        for protocol_data in study.get('protocols', []):
            protocol = Protocol()
            protocol.from_dict(protocol_data)
            self.protocols.append(protocol)
            indexes.add_protocol(protocol)

        # Factors
        for factor_data in study.get('factors', []):
            factor = StudyFactor()
            factor.from_dict(factor_data)
            self.factors.append(factor)
            indexes.add_factor(factor)

        # Source
        for source_data in study.get('materials', {}).get('sources', []):
            source = Source()
            source.from_dict(source_data)
            self.sources.append(source)
            indexes.add_source(source)

        # Sample
        for sample_data in study.get('materials', {}).get('samples', []):
            sample = Sample()
            sample.from_dict(sample_data)
            self.samples.append(sample)
            indexes.add_sample(sample)

        # Process
        for process_data in study.get('processSequence', []):
            process = Process()
            process.from_dict(process_data)
            self.process_sequence.append(process)
            indexes.add_process(process)
        for process_data in study.get('processSequence', []):
            try:
                current_process = indexes.get_process(process_data['@id'])
                previous_process_id = process_data['previousProcess']['@id']
                previous_process = indexes.get_process(previous_process_id)
                current_process.prev_process = previous_process

                next_process_id = process_data['nextProcess']['@id']
                next_process = indexes.get_process(next_process_id)
                current_process.next_process = next_process
            except KeyError:
                pass

        # Assay
        for assay_data in study.get('assays', []):
            indexes.processes = []
            assay = Assay()
            assay.from_dict(assay_data)
            self.assays.append(assay)

        indexes.reset_store()