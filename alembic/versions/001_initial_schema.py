"""Initial schema with api_keys, lexicon_terms, jobs, and feedback tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all core tables for the speech-to-text application.
    
    Order of creation respects foreign key dependencies:
    1. api_keys (no dependencies)
    2. lexicon_terms (no dependencies)
    3. jobs (no dependencies, but referenced by feedback)
    4. feedback (depends on jobs)
    """
    
    # ============================================================================
    # Table 1: api_keys
    # Stores API authentication keys for accessing the application
    # ============================================================================
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('key_hash', sa.String(length=128), nullable=False, comment='SHA256 hash of the API key'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='Descriptive name for the key'),
        sa.Column('description', sa.Text(), nullable=True, comment='Optional description of key usage'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, server_default='true', comment='Whether the key is currently active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True, comment='Last time this key was used'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True, comment='Optional expiration date'),
        sa.Column('rate_limit', sa.Integer(), nullable=True, comment='Optional rate limit per hour'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional metadata'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash', name='uq_api_keys_key_hash'),
        sa.UniqueConstraint('name', name='uq_api_keys_name'),
        comment='API keys for authentication and authorization'
    )
    
    # Create indexes for api_keys
    op.create_index('ix_api_keys_is_active', 'api_keys', ['is_active'])
    op.create_index('ix_api_keys_created_at', 'api_keys', ['created_at'])
    op.create_index('ix_api_keys_expires_at', 'api_keys', ['expires_at'])
    
    # ============================================================================
    # Table 2: lexicon_terms
    # Stores domain-specific terms for improving transcription accuracy
    # ============================================================================
    op.create_table(
        'lexicon_terms',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('term', sa.String(length=255), nullable=False, comment='The lexicon term (e.g., drug name, brand name)'),
        sa.Column('normalized_term', sa.String(length=255), nullable=False, comment='Normalized/lowercased version for matching'),
        sa.Column('category', sa.String(length=100), nullable=True, comment='Category (e.g., drug, brand, medical)'),
        sa.Column('language', sa.String(length=10), nullable=True, comment='ISO language code (e.g., en, es, zh)'),
        sa.Column('frequency', sa.Integer(), nullable=False, default=0, server_default='0', comment='Usage frequency counter'),
        sa.Column('confidence_boost', sa.Float(), nullable=True, comment='Confidence boost factor for this term'),
        sa.Column('alternatives', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Alternative spellings or variations'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional metadata'),
        sa.Column('source', sa.String(length=100), nullable=True, comment='Source of the term (manual, learned, imported)'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.String(length=100), nullable=True, comment='User or system that created the term'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('term', name='uq_lexicon_terms_term'),
        comment='Domain-specific lexicon terms for transcription improvement'
    )
    
    # Create indexes for lexicon_terms
    op.create_index('ix_lexicon_terms_normalized_term', 'lexicon_terms', ['normalized_term'])
    op.create_index('ix_lexicon_terms_category', 'lexicon_terms', ['category'])
    op.create_index('ix_lexicon_terms_language', 'lexicon_terms', ['language'])
    op.create_index('ix_lexicon_terms_is_active', 'lexicon_terms', ['is_active'])
    op.create_index('ix_lexicon_terms_frequency', 'lexicon_terms', ['frequency'], postgresql_using='btree')
    op.create_index('ix_lexicon_terms_source', 'lexicon_terms', ['source'])
    
    # ============================================================================
    # Table 3: jobs
    # Stores transcription job information
    # ============================================================================
    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('job_id', sa.String(length=100), nullable=False, comment='Unique job identifier (UUID)'),
        sa.Column('status', sa.String(length=50), nullable=False, comment='Job status: pending, processing, completed, failed'),
        sa.Column('audio_filename', sa.String(length=500), nullable=True, comment='Original audio filename'),
        sa.Column('audio_format', sa.String(length=10), nullable=True, comment='Audio format: wav, mp3, m4a'),
        sa.Column('audio_duration', sa.Float(), nullable=True, comment='Audio duration in seconds'),
        sa.Column('audio_size_bytes', sa.BigInteger(), nullable=True, comment='Audio file size in bytes'),
        sa.Column('audio_storage_path', sa.String(length=1000), nullable=True, comment='Path to stored audio file'),
        sa.Column('language', sa.String(length=10), nullable=True, comment='Primary language code'),
        sa.Column('model_name', sa.String(length=100), nullable=True, comment='OpenAI model used (gpt-4o-transcribe, whisper-1)'),
        sa.Column('transcription_text', sa.Text(), nullable=True, comment='Raw transcription output'),
        sa.Column('lexicon_version', sa.String(length=50), nullable=True, comment='Version of lexicon used'),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True, comment='Total processing time'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='Error message if job failed'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional job metadata'),
        sa.Column('api_key_id', sa.Integer(), nullable=True, comment='API key used for this job'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True, comment='When processing started'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='When job completed or failed'),
        sa.Column('submitted_by', sa.String(length=100), nullable=True, comment='User who submitted the job'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id', name='uq_jobs_job_id'),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], name='fk_jobs_api_key_id', ondelete='SET NULL'),
        comment='Transcription jobs and their processing status'
    )
    
    # Create indexes for jobs
    op.create_index('ix_jobs_job_id', 'jobs', ['job_id'])
    op.create_index('ix_jobs_status', 'jobs', ['status'])
    op.create_index('ix_jobs_created_at', 'jobs', ['created_at'], postgresql_using='btree')
    op.create_index('ix_jobs_completed_at', 'jobs', ['completed_at'])
    op.create_index('ix_jobs_api_key_id', 'jobs', ['api_key_id'])
    op.create_index('ix_jobs_submitted_by', 'jobs', ['submitted_by'])
    op.create_index('ix_jobs_language', 'jobs', ['language'])
    op.create_index('ix_jobs_model_name', 'jobs', ['model_name'])
    # Composite index for common queries
    op.create_index('ix_jobs_status_created_at', 'jobs', ['status', 'created_at'])
    
    # ============================================================================
    # Table 4: feedback
    # Stores reviewer edits and corrections for learning
    # ============================================================================
    op.create_table(
        'feedback',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('job_id', sa.Integer(), nullable=False, comment='Reference to the transcription job'),
        sa.Column('original_text', sa.Text(), nullable=False, comment='Original transcription text'),
        sa.Column('corrected_text', sa.Text(), nullable=False, comment='Corrected text by reviewer'),
        sa.Column('diff_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Detailed diff information'),
        sa.Column('edit_distance', sa.Integer(), nullable=True, comment='Levenshtein edit distance'),
        sa.Column('accuracy_score', sa.Float(), nullable=True, comment='Calculated accuracy score (0-1)'),
        sa.Column('review_time_seconds', sa.Integer(), nullable=True, comment='Time spent reviewing'),
        sa.Column('reviewer', sa.String(length=100), nullable=True, comment='User who provided feedback'),
        sa.Column('review_notes', sa.Text(), nullable=True, comment='Additional notes from reviewer'),
        sa.Column('extracted_terms', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='New terms extracted from corrections'),
        sa.Column('feedback_type', sa.String(length=50), nullable=True, comment='Type: correction, validation, quality_issue'),
        sa.Column('is_processed', sa.Boolean(), nullable=False, default=False, server_default='false', comment='Whether feedback has been processed for learning'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional feedback metadata'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True, comment='When feedback was processed'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], name='fk_feedback_job_id', ondelete='CASCADE'),
        comment='Reviewer feedback and corrections for continuous learning'
    )
    
    # Create indexes for feedback
    op.create_index('ix_feedback_job_id', 'feedback', ['job_id'])
    op.create_index('ix_feedback_reviewer', 'feedback', ['reviewer'])
    op.create_index('ix_feedback_created_at', 'feedback', ['created_at'], postgresql_using='btree')
    op.create_index('ix_feedback_is_processed', 'feedback', ['is_processed'])
    op.create_index('ix_feedback_feedback_type', 'feedback', ['feedback_type'])
    op.create_index('ix_feedback_accuracy_score', 'feedback', ['accuracy_score'])
    # Composite index for common queries
    op.create_index('ix_feedback_is_processed_created_at', 'feedback', ['is_processed', 'created_at'])


def downgrade() -> None:
    """Drop all tables in reverse order of creation.
    
    Order respects foreign key dependencies:
    1. feedback (has foreign key to jobs)
    2. jobs (has foreign key to api_keys)
    3. lexicon_terms (no dependencies)
    4. api_keys (no dependencies)
    """
    
    # Drop feedback table and its indexes
    op.drop_index('ix_feedback_is_processed_created_at', table_name='feedback')
    op.drop_index('ix_feedback_accuracy_score', table_name='feedback')
    op.drop_index('ix_feedback_feedback_type', table_name='feedback')
    op.drop_index('ix_feedback_is_processed', table_name='feedback')
    op.drop_index('ix_feedback_created_at', table_name='feedback')
    op.drop_index('ix_feedback_reviewer', table_name='feedback')
    op.drop_index('ix_feedback_job_id', table_name='feedback')
    op.drop_table('feedback')
    
    # Drop jobs table and its indexes
    op.drop_index('ix_jobs_status_created_at', table_name='jobs')
    op.drop_index('ix_jobs_model_name', table_name='jobs')
    op.drop_index('ix_jobs_language', table_name='jobs')
    op.drop_index('ix_jobs_submitted_by', table_name='jobs')
    op.drop_index('ix_jobs_api_key_id', table_name='jobs')
    op.drop_index('ix_jobs_completed_at', table_name='jobs')
    op.drop_index('ix_jobs_created_at', table_name='jobs')
    op.drop_index('ix_jobs_status', table_name='jobs')
    op.drop_index('ix_jobs_job_id', table_name='jobs')
    op.drop_table('jobs')
    
    # Drop lexicon_terms table and its indexes
    op.drop_index('ix_lexicon_terms_source', table_name='lexicon_terms')
    op.drop_index('ix_lexicon_terms_frequency', table_name='lexicon_terms')
    op.drop_index('ix_lexicon_terms_is_active', table_name='lexicon_terms')
    op.drop_index('ix_lexicon_terms_language', table_name='lexicon_terms')
    op.drop_index('ix_lexicon_terms_category', table_name='lexicon_terms')
    op.drop_index('ix_lexicon_terms_normalized_term', table_name='lexicon_terms')
    op.drop_table('lexicon_terms')
    
    # Drop api_keys table and its indexes
    op.drop_index('ix_api_keys_expires_at', table_name='api_keys')
    op.drop_index('ix_api_keys_created_at', table_name='api_keys')
    op.drop_index('ix_api_keys_is_active', table_name='api_keys')
    op.drop_table('api_keys')
