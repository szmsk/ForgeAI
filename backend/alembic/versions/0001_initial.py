from alembic import op
import sqlalchemy as sa
revision='0001_initial'; down_revision=None; branch_labels=None; depends_on=None

def upgrade():
    op.create_table('tenants',sa.Column('id',sa.String(36),primary_key=True),sa.Column('name',sa.String(160),nullable=False),sa.Column('plan',sa.String(40),nullable=False),sa.Column('max_concurrent_runs',sa.Integer,nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_table('users',sa.Column('id',sa.String(36),primary_key=True),sa.Column('tenant_id',sa.String(36),sa.ForeignKey('tenants.id',ondelete='CASCADE'),nullable=False),sa.Column('email',sa.String(320),unique=True,nullable=False),sa.Column('password_hash',sa.String(255),nullable=False),sa.Column('role',sa.String(40),nullable=False),sa.Column('is_active',sa.Boolean,nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_table('runs',sa.Column('id',sa.String(36),primary_key=True),sa.Column('tenant_id',sa.String(36),sa.ForeignKey('tenants.id',ondelete='CASCADE'),nullable=False),sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id',ondelete='SET NULL')),sa.Column('idempotency_key',sa.String(200)),sa.Column('repository',sa.Text,nullable=False),sa.Column('task',sa.Text,nullable=False),sa.Column('status',sa.String(30),nullable=False),sa.Column('iterations',sa.Integer,nullable=False),sa.Column('tests_passed',sa.Integer,nullable=False),sa.Column('tests_total',sa.Integer,nullable=False),sa.Column('duration_ms',sa.Integer,nullable=False),sa.Column('cost_usd',sa.Float,nullable=False),sa.Column('input_tokens',sa.Integer,nullable=False),sa.Column('output_tokens',sa.Integer,nullable=False),sa.Column('summary',sa.Text,nullable=False),sa.Column('pull_request_url',sa.Text),sa.Column('error',sa.Text),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('started_at',sa.DateTime(timezone=True)),sa.Column('finished_at',sa.DateTime(timezone=True)))
    op.create_table('run_events',sa.Column('id',sa.String(36),primary_key=True),sa.Column('tenant_id',sa.String(36),sa.ForeignKey('tenants.id',ondelete='CASCADE'),nullable=False),sa.Column('run_id',sa.String(36),sa.ForeignKey('runs.id',ondelete='CASCADE'),nullable=False),sa.Column('type',sa.String(40),nullable=False),sa.Column('message',sa.Text,nullable=False),sa.Column('iteration',sa.Integer,nullable=False),sa.Column('metadata_json',sa.JSON,nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_table('api_keys',sa.Column('id',sa.String(36),primary_key=True),sa.Column('tenant_id',sa.String(36),sa.ForeignKey('tenants.id',ondelete='CASCADE'),nullable=False),sa.Column('name',sa.String(120),nullable=False),sa.Column('prefix',sa.String(16),nullable=False),sa.Column('key_hash',sa.String(128),unique=True,nullable=False),sa.Column('revoked',sa.Boolean,nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    for t in ['users','runs','run_events','api_keys']:
        op.execute(sa.text(f'ALTER TABLE {t} ENABLE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE {t} FORCE ROW LEVEL SECURITY'))
        op.execute(sa.text(f"CREATE POLICY {t}_tenant_isolation ON {t} USING (tenant_id = current_setting('app.tenant_id', true) OR current_setting('app.bootstrap', true) = 'true') WITH CHECK (tenant_id = current_setting('app.tenant_id', true) OR current_setting('app.bootstrap', true) = 'true')"))
    op.execute("CREATE UNIQUE INDEX uq_runs_tenant_idempotency ON runs(tenant_id,idempotency_key) WHERE idempotency_key IS NOT NULL")
    op.execute("CREATE INDEX ix_runs_tenant_created ON runs(tenant_id,created_at)")
    op.execute("CREATE INDEX ix_events_tenant_run ON run_events(tenant_id,run_id,created_at)")

def downgrade():
    for t in ['api_keys','run_events','runs','users','tenants']: op.drop_table(t)
