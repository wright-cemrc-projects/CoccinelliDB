"""Rename tables

Revision ID: 14bfdc7f17af
Revises: 06c2fc8db6c0
Create Date: 2025-01-06 15:10:21.939315

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '14bfdc7f17af'
down_revision = '06c2fc8db6c0'
branch_labels = None
depends_on = None

def upgrade():
    op.rename_table('facility_group', 'group')
    op.rename_table('facility_person', 'person')
    op.rename_table('facility_project', 'project')
    op.rename_table('facility_instrument', 'instrument')
    op.rename_table('facility_instrument_issue', 'instrument_issue')
    op.rename_table('facility_instrument_session', 'instrument_session')
    op.rename_table('facility_collection', 'collection')
    op.rename_table('facility_grid_box', 'grid_box')

def downgrade():
    op.rename_table('group', 'facility_group')
    op.rename_table('person', 'facility_person')
    op.rename_table('project', 'facility_project')
    op.rename_table('instrument', 'facility_instrument')
    op.rename_table('instrument_issue', 'facility_instrument_issue')
    op.rename_table('instrument_session', 'facility_instrument_session')
    op.rename_table('collection', 'facility_collection')
    op.rename_table('grid_box', 'facility_grid_box')
