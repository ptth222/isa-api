from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from isatools.model import Sample as SampleModel
from isatools.database.models.relationships import (
    study_samples,
    sample_characteristics,
    sample_derives_from,
    sample_factor_values
)
from isatools.database.models.inputs_outputs import InputOutput
from isatools.database.models.utils import make_get_table_method


class Sample(InputOutput):
    __tablename__: str = 'sample'
    __mapper_args__ = {
        "polymorphic_identity": "sample",
        "concrete": True,
    }

    # Base fields
    id: str = Column(String, primary_key=True)
    name: str = Column(String)

    # Relationships back-ref
    studies: relationship = relationship('Study', secondary=study_samples, back_populates='samples')

    # Relationships: many-to-many
    characteristics: relationship = relationship(
        'Characteristic', secondary=sample_characteristics, back_populates='samples'
    )
    derives_from: relationship = relationship(
        'Source', secondary=sample_derives_from, back_populates='samples'
    )
    factor_values: relationship = relationship('FactorValue', secondary=sample_factor_values, back_populates='samples')

    # Factor values, derives from
    comments = relationship('Comment', back_populates='sample')

    def to_json(self) -> dict:
        return {
            '@id': self.id,
            'name': self.name,
            'characteristics': [c.to_json() for c in self.characteristics],
            'factorValues': [fv.to_json() for fv in self.factor_values],
            'derives_from': [{"@id": s.id} for s in self.derives_from],
            'comments': [c.to_json() for c in self.comments]
        }


def make_sample_methods():
    def to_sql(self, session):
        return Sample(
            id=self.id,
            name=self.name,
            characteristics=[c.to_sql(session) for c in self.characteristics],
            derives_from=[s.to_sql(session) for s in self.derives_from],
            factor_values=[fv.to_sql(session) for fv in self.factor_values],
            comments=[c.to_sql() for c in self.comments]
        )

    setattr(SampleModel, 'to_sql', to_sql)
    setattr(SampleModel, 'get_table', make_get_table_method(Sample))
