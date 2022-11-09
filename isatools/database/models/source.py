from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from isatools.model import Source as SourceModel
from isatools.database.models.relationships import study_sources
from isatools.database.models.relationships import source_characteristics
from isatools.database.utils import Base
from isatools.database.models.utils import make_get_table_method


class Source(Base):
    __tablename__: str = 'source'

    # Base fields
    id: str = Column(String, primary_key=True)
    name: str = Column(String)

    # Relationships back-ref
    studies: relationship = relationship('Study', secondary=study_sources, back_populates='sources')

    # Relationships: many-to-many
    characteristics: relationship = relationship(
        'Characteristic', secondary=source_characteristics, back_populates='sources'
    )

    comments = relationship('Comment', back_populates='source')

    def to_json(self) -> dict:
        return {
            '@id': self.id, 'name': self.name,
            'characteristics': [c.to_json() for c in self.characteristics],
            'comments': [c.to_json() for c in self.comments]
        }


def make_source_methods():
    def to_sql(self, session):
        return Source(
            id=self.id,
            name=self.name,
            characteristics=[c.to_sql(session) for c in self.characteristics],
            comments=[c.to_sql() for c in self.comments]
        )

    setattr(SourceModel, 'to_sql', to_sql)
    setattr(SourceModel, 'get_table', make_get_table_method(Source))