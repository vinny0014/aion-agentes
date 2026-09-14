"""Transactional Shopee store. No network access or implicit publication.

Prices are BRL integer cents; timestamps are Unix UTC seconds. Tables are
namespaced to preserve the existing newsroom and its authentication records.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from .guardrails import LinkStatus, validate_shopee_url_structure

SCHEMA = """
CREATE TABLE IF NOT EXISTS cp_products (
 id TEXT PRIMARY KEY, title TEXT NOT NULL, category TEXT NOT NULL,
 current_hash TEXT NOT NULL, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS cp_offers (
 id INTEGER PRIMARY KEY, product_id TEXT NOT NULL REFERENCES cp_products(id),
 input_hash TEXT NOT NULL, payload TEXT NOT NULL,
 affiliate_url_exact TEXT NOT NULL, source TEXT NOT NULL,
 price_cents INTEGER NOT NULL CHECK(price_cents>0), observed_at INTEGER NOT NULL,
 expires_at INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'draft'
 CHECK(status IN ('draft','active','paused')),
 reason TEXT NOT NULL DEFAULT 'verification_required', created_at INTEGER NOT NULL,
 UNIQUE(product_id,input_hash)
);
CREATE TABLE IF NOT EXISTS cp_link_checks (
 id INTEGER PRIMARY KEY, offer_id INTEGER NOT NULL REFERENCES cp_offers(id),
 input_hash TEXT NOT NULL, status TEXT NOT NULL, destination_product_id TEXT,
 image_valid INTEGER NOT NULL, stock_valid INTEGER NOT NULL,
 official_provenance INTEGER NOT NULL, tracking_verified INTEGER NOT NULL,
 checked_at INTEGER NOT NULL, expires_at INTEGER NOT NULL, evidence_ref TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cp_scores (
 offer_id INTEGER PRIMARY KEY REFERENCES cp_offers(id), input_hash TEXT NOT NULL,
 score REAL NOT NULL, eligible INTEGER NOT NULL, evidence_ref TEXT NOT NULL,
 checked_at INTEGER NOT NULL, expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS cp_price_history (
 offer_id INTEGER PRIMARY KEY REFERENCES cp_offers(id), product_id TEXT NOT NULL,
 price_cents INTEGER NOT NULL, observed_at INTEGER NOT NULL, source TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cp_jobs (
 id INTEGER PRIMARY KEY, job_type TEXT NOT NULL, entity_id TEXT NOT NULL,
 input_hash TEXT NOT NULL, cycle INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'queued',
 attempt INTEGER NOT NULL DEFAULT 0, available_at INTEGER NOT NULL,
 lease_until INTEGER, lease_token TEXT, finished_at INTEGER, error_code TEXT,
 UNIQUE(job_type,entity_id,input_hash,cycle)
);
CREATE INDEX IF NOT EXISTS cp_jobs_due ON cp_jobs(status,available_at);
CREATE TABLE IF NOT EXISTS cp_events (
 event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, offer_id INTEGER,
 price_cents INTEGER, placement TEXT NOT NULL, occurred_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS cp_commissions (
 entry_id TEXT PRIMARY KEY, order_id TEXT NOT NULL, status TEXT NOT NULL,
 amount_cents INTEGER NOT NULL CHECK(amount_cents>=0), occurred_at INTEGER NOT NULL,
 source TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cp_costs (
 entry_id TEXT PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('ads','variable')),
 amount_cents INTEGER NOT NULL CHECK(amount_cents>=0), occurred_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS cp_audit (
 id INTEGER PRIMARY KEY, action TEXT NOT NULL, entity_id TEXT NOT NULL,
 reason TEXT NOT NULL, occurred_at INTEGER NOT NULL
);
"""
JOB_TYPES = frozenset(('discover_products','refresh_offer','validate_affiliate_link',
 'validate_image','calculate_pulse_score','publish_offer','unpublish_offer',
 'import_commissions','reconcile_attribution'))
CLIENT_EVENTS = frozenset(('landing_view','category_view','product_view','merchant_click'))


def integer(value, name, minimum=0):
    if type(value) is not int or value < minimum or value > 10**12:
        raise ValueError(name)
    return value


def short_text(value, name, maximum=200):
    if not isinstance(value, str) or not value.strip() or len(value)>maximum:
        raise ValueError(name)
    return value


def normalized_offer(payload, now):
    if not isinstance(payload, dict):
        raise ValueError('object_required')
    # Explicit schema: arbitrary imported fields/secrets never reach persistence.
    allowed = {'product_id','title','category','price_cents','observed_at','expires_at',
               'affiliate_url','source_url','image_url','image_source','source'}
    if set(payload) != allowed:
        raise ValueError('invalid_offer_fields')
    p = dict(payload)
    for key in ('product_id','title','category','source','image_source'):
        short_text(p[key],key)
    if p['source'] not in ('shopee_official_export','shopee_official_api'):
        raise ValueError('official_source_required')
    for key in ('affiliate_url','source_url'):
        short_text(p[key],key,4096)
        if validate_shopee_url_structure(p[key]).status == LinkStatus.INVALID:
            raise ValueError('invalid_'+key)
    from urllib.parse import urlsplit
    image = urlsplit(short_text(p['image_url'],'image_url',4096))
    if image.scheme != 'https' or not image.hostname or image.username or image.password:
        raise ValueError('invalid_image_url')
    integer(p['price_cents'],'price_cents',1)
    integer(p['observed_at'],'observed_at',1)
    integer(p['expires_at'],'expires_at',1)
    if not now-86400 <= p['observed_at'] <= now or not now < p['expires_at'] <= p['observed_at']+86400:
        raise ValueError('invalid_freshness')
    return p


class CommerceStore:
    def __init__(self, path):
        self.path = Path(path)

    @contextmanager
    def transaction(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
        conn.execute('BEGIN IMMEDIATE')
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self):
        with self.transaction() as c:
            for statement in SCHEMA.split(';'):
                if statement.strip():
                    c.execute(statement)

    def ingest(self, payload, now=None):
        now = int(time.time()) if now is None else now
        p = normalized_offer(payload, now)
        raw = json.dumps(p, sort_keys=True, separators=(',',':'), ensure_ascii=False)
        digest = hashlib.sha256(raw.encode()).hexdigest()
        with self.transaction() as c:
            existing = c.execute('SELECT id FROM cp_offers WHERE product_id=? AND input_hash=?',
                                 (p['product_id'],digest)).fetchone()
            if existing:
                return {'offer_id':existing['id'],'created':False}
            previous = c.execute('SELECT MAX(observed_at) FROM cp_offers WHERE product_id=?',
                                 (p['product_id'],)).fetchone()[0]
            if previous is not None and p['observed_at'] <= previous:
                raise ValueError('older_or_ambiguous_observation')
            c.execute('''INSERT INTO cp_products VALUES(?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET title=excluded.title,category=excluded.category,
                current_hash=excluded.current_hash,updated_at=excluded.updated_at''',
                (p['product_id'],p['title'],p['category'],digest,now,now))
            # A changed product cannot inherit the old link/image validation.
            c.execute("UPDATE cp_offers SET status='paused',reason='superseded' WHERE product_id=?",(p['product_id'],))
            cur = c.execute('''INSERT INTO cp_offers(product_id,input_hash,payload,affiliate_url_exact,
                source,price_cents,observed_at,expires_at,created_at) VALUES(?,?,?,?,?,?,?,?,?)''',
                (p['product_id'],digest,raw,p['affiliate_url'],p['source'],p['price_cents'],
                 p['observed_at'],p['expires_at'],now))
            oid = cur.lastrowid
            c.execute('INSERT INTO cp_price_history VALUES(?,?,?,?,?)',
                      (oid,p['product_id'],p['price_cents'],p['observed_at'],p['source']))
            c.execute('INSERT INTO cp_audit(action,entity_id,reason,occurred_at) VALUES(?,?,?,?)',
                      ('import',str(oid),'verification_required',now))
            return {'offer_id':oid,'created':True}

    def record_check(self, offer_id, *, status, destination_product_id, image_valid,
                     stock_valid, official_provenance, tracking_verified, evidence_ref,
                     checked_at, expires_at, input_hash, now=None):
        """Internal evidence writer; never expose this as a public/admin attestation API.

        Only a trusted, tested adapter can call this after checking official source,
        redirect chain, tracking, exact product/variation and the decoded real image.
        """
        now = int(time.time()) if now is None else now
        status = LinkStatus(status)
        short_text(evidence_ref,'evidence_ref',200)
        for value in (image_valid,stock_valid,official_provenance,tracking_verified):
            if type(value) is not bool:
                raise ValueError('boolean_required')
        if not now-3600 <= checked_at <= now or not now < expires_at <= checked_at+3600:
            raise ValueError('invalid_check_freshness')
        with self.transaction() as c:
            row = c.execute('SELECT * FROM cp_offers WHERE id=?',(offer_id,)).fetchone()
            if not row or row['input_hash'] != input_hash:
                raise ValueError('stale_check')
            c.execute('''INSERT INTO cp_link_checks(offer_id,input_hash,status,destination_product_id,
                image_valid,stock_valid,official_provenance,tracking_verified,checked_at,expires_at,evidence_ref)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
                (offer_id,input_hash,status.value,destination_product_id,image_valid,stock_valid,
                 official_provenance,tracking_verified,checked_at,expires_at,evidence_ref))
            # Any new evidence requires a fresh publication decision, even if VALID.
            c.execute("UPDATE cp_offers SET status='paused',reason='check_changed' WHERE id=?",(offer_id,))

    @staticmethod
    def eligibility(c, oid, now):
        row = c.execute('''SELECT o.*,p.current_hash FROM cp_offers o JOIN cp_products p
                           ON p.id=o.product_id WHERE o.id=?''',(oid,)).fetchone()
        if not row or row['input_hash'] != row['current_hash']:
            return False, 'superseded'
        check = c.execute('SELECT * FROM cp_link_checks WHERE offer_id=? ORDER BY id DESC LIMIT 1',(oid,)).fetchone()
        if row['expires_at'] <= now:
            return False, 'price_expired'
        if not check or check['expires_at'] <= now or check['checked_at'] > now:
            return False, 'verification_expired'
        score=c.execute('SELECT * FROM cp_scores WHERE offer_id=?',(oid,)).fetchone()
        if not score or not score['eligible'] or score['expires_at']<=now or score['input_hash']!=row['input_hash']:
            return False,'score_not_eligible'
        valid = (check['status']=='VALID' and check['destination_product_id']==row['product_id']
            and check['input_hash']==row['input_hash'] and check['image_valid'] and check['stock_valid']
            and check['official_provenance'] and check['tracking_verified'])
        return (True,'verified') if valid else (False,'verification_failed')

    def record_score(self, offer_id, components, *, evidence_ref, now=None):
        from .scoring import pulse_score
        now=int(time.time()) if now is None else now
        short_text(evidence_ref,'evidence_ref')
        score=pulse_score(components)
        with self.transaction() as c:
            row=c.execute('SELECT input_hash FROM cp_offers WHERE id=?',(offer_id,)).fetchone()
            if not row:
                raise ValueError('missing_offer')
            c.execute('INSERT OR REPLACE INTO cp_scores VALUES(?,?,?,?,?,?,?)',
                (offer_id,row['input_hash'],score['score'],score['eligible'],evidence_ref,now,now+3600))
            c.execute("UPDATE cp_offers SET status='paused',reason='score_changed' WHERE id=?",(offer_id,))
        return score

    def publish(self, offer_id, *, now=None):
        now = int(time.time()) if now is None else now
        with self.transaction() as c:
            valid, reason = self.eligibility(c,offer_id,now)
            c.execute('UPDATE cp_offers SET status=?,reason=? WHERE id=?',
                      ('active' if valid else 'paused',reason,offer_id))
            return valid

    def catalog(self, now=None):
        now = int(time.time()) if now is None else now
        with self.transaction() as c:
            result=[]
            for row in c.execute("SELECT * FROM cp_offers WHERE status='active' ORDER BY id DESC").fetchall():
                valid,reason=self.eligibility(c,row['id'],now)
                if not valid:
                    c.execute("UPDATE cp_offers SET status='paused',reason=? WHERE id=?",(reason,row['id']))
                    continue
                p=json.loads(row['payload'])
                result.append({'offer_id':row['id'],**p})
            return result

    def enqueue(self, job_type, entity_id, input_hash, cycle, now=None):
        if job_type not in JOB_TYPES:
            raise ValueError('unsupported_job')
        short_text(entity_id,'entity_id'); short_text(input_hash,'input_hash')
        integer(cycle,'cycle')
        now=int(time.time()) if now is None else now
        with self.transaction() as c:
            c.execute('''INSERT OR IGNORE INTO cp_jobs(job_type,entity_id,input_hash,cycle,available_at)
                         VALUES(?,?,?,?,?)''',(job_type,entity_id,input_hash,cycle,now))
            return c.execute('SELECT id FROM cp_jobs WHERE job_type=? AND entity_id=? AND input_hash=? AND cycle=?',
                             (job_type,entity_id,input_hash,cycle)).fetchone()['id']

    def claim(self, now=None):
        import secrets
        now=int(time.time()) if now is None else now
        with self.transaction() as c:
            c.execute("UPDATE cp_jobs SET status='failed',error_code='lease_exhausted' WHERE status='working' AND lease_until<=? AND attempt>=3",(now,))
            row=c.execute('''SELECT * FROM cp_jobs WHERE attempt<3 AND
                ((status='queued' AND available_at<=?) OR (status='working' AND lease_until<=?))
                ORDER BY available_at,id LIMIT 1''',(now,now)).fetchone()
            if not row:
                return None
            token=secrets.token_hex(16)
            c.execute("UPDATE cp_jobs SET status='working',attempt=attempt+1,lease_until=?,lease_token=? WHERE id=?",(now+120,token,row['id']))
            return dict(c.execute('SELECT * FROM cp_jobs WHERE id=?',(row['id'],)).fetchone())

    def finish(self, job_id, lease_token, *, error_code=None, blocked=False, now=None):
        now=int(time.time()) if now is None else now
        if error_code and (not error_code.replace('_','').isalnum() or len(error_code)>80):
            raise ValueError('sanitized_error_code_required')
        with self.transaction() as c:
            r=c.execute("SELECT * FROM cp_jobs WHERE id=? AND lease_token=? AND status='working' AND lease_until>?",(job_id,lease_token,now)).fetchone()
            if not r:
                return False
            status='done' if not error_code else ('blocked' if blocked else ('failed' if r['attempt']>=3 else 'queued'))
            c.execute('''UPDATE cp_jobs SET status=?,error_code=?,available_at=?,finished_at=?,lease_until=NULL,lease_token=NULL WHERE id=?''',
                      (status,error_code,now+60*2**r['attempt'],now if status!='queued' else None,job_id))
            return True

    def record_event(self, event_id, event_type, *, offer_id=None, placement='catalog', now=None):
        short_text(event_id,'event_id',64)
        if event_type not in CLIENT_EVENTS or placement not in ('catalog','product','category'):
            raise ValueError('invalid_event')
        now=int(time.time()) if now is None else now
        with self.transaction() as c:
            price=None
            if event_type in ('product_view','merchant_click'):
                valid,_=self.eligibility(c,offer_id,now)
                row=c.execute('SELECT status,price_cents FROM cp_offers WHERE id=?',(offer_id,)).fetchone()
                if not valid or row['status']!='active':
                    raise ValueError('unavailable_offer')
                price=row['price_cents']
            c.execute('INSERT OR IGNORE INTO cp_events VALUES(?,?,?,?,?,?)',
                      (event_id,event_type,offer_id,price,placement,now))

    def metrics(self):
        with self.transaction() as c:
            counts={r['event_type']:r['n'] for r in c.execute('SELECT event_type,COUNT(*) n FROM cp_events GROUP BY event_type')}
            approved=c.execute("""SELECT COALESCE(SUM(amount_cents),0) FROM cp_commissions a
                WHERE status='approved' AND NOT EXISTS(SELECT 1 FROM cp_commissions b
                WHERE b.order_id=a.order_id AND (b.occurred_at>a.occurred_at OR
                (b.occurred_at=a.occurred_at AND b.rowid>a.rowid)))""").fetchone()[0]
            costs={r['kind']:r['amount'] for r in c.execute('SELECT kind,SUM(amount_cents) amount FROM cp_costs GROUP BY kind')}
            return {'events':counts,'approved_commission_cents':approved,
                    'ads_cents':costs.get('ads',0),'variable_cents':costs.get('variable',0),
                    'net_profit_cents':approved-sum(costs.values()),
                    'shopee_attributed_clicks':None,'orders':None,'approved_orders':None,
                    'commission_feed_connected':False}
