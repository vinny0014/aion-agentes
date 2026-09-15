"""Bounded deterministic worker. Unsupported integrations report BLOCKED."""
import hashlib
import time

from .store import CommerceStore

MAX_AUTO_PUBLISH_PER_HOUR = 10


def schedule(store: CommerceStore, now=None):
    now=int(time.time()) if now is None else now
    # Expiration is also enforced on every catalog read, independently of cron.
    store.catalog(now=now)
    with store.transaction() as c:
        rows=c.execute('''SELECT o.id,o.input_hash FROM cp_offers o JOIN cp_products p
            ON o.product_id=p.id AND o.input_hash=p.current_hash WHERE o.expires_at>?''',(now,)).fetchall()
    for row in rows:
        store.enqueue('refresh_offer',str(row['id']),row['input_hash'],now//3600,now)
    store.enqueue('discover_products','shopee',hashlib.sha256(b'shopee-only-v1').hexdigest(),now//3600,now)


def enqueue_publish_candidates(store: CommerceStore, offer_ids, now=None, limit=MAX_AUTO_PUBLISH_PER_HOUR):
    """Atomically queue at most ``limit`` auto-publications per UTC hour.

    Repeated schedulers share the same database-backed hourly budget, so a retry or
    overlapping worker cannot enqueue another batch and accidentally exceed it.
    Eligibility is still re-checked fail-closed when the publish job actually runs.
    """
    now=int(time.time()) if now is None else now
    if type(limit) is not int or limit < 1 or limit > MAX_AUTO_PUBLISH_PER_HOUR:
        raise ValueError('invalid_publication_limit')
    if not isinstance(offer_ids,(list,tuple)):
        raise ValueError('offer_ids_required')
    cycle=now//3600
    queued=[]
    seen=set()
    with store.transaction() as c:
        used=c.execute("SELECT COUNT(*) FROM cp_jobs WHERE job_type='publish_offer' AND cycle=?",(cycle,)).fetchone()[0]
        remaining=max(0,limit-used)
        for oid in offer_ids:
            if remaining == 0:
                break
            if type(oid) is not int or oid < 1 or oid in seen:
                continue
            seen.add(oid)
            row=c.execute('SELECT input_hash FROM cp_offers WHERE id=?',(oid,)).fetchone()
            if not row:
                continue
            cur=c.execute('''INSERT OR IGNORE INTO cp_jobs(job_type,entity_id,input_hash,cycle,available_at)
                             VALUES('publish_offer',?,?,?,?)''',(str(oid),row['input_hash'],cycle,now))
            if cur.rowcount:
                queued.append(oid)
                remaining-=1
    return queued


def run_once(store: CommerceStore, handlers=None, now=None):
    handlers=handlers or {}
    job=store.claim(now)
    if not job:
        return None
    # Publication is deterministic and local: it never requires provider access.
    # The store re-checks fresh official evidence, exact product, image, stock,
    # tracking and PulseScore before switching an offer to active.
    if job['job_type']=='publish_offer':
        try:
            published=store.publish(int(job['entity_id']),now=now)
        except (TypeError,ValueError):
            published=False
        if not published:
            store.finish(job['id'],job['lease_token'],error_code='publication_guardrail_failed',blocked=True,now=now)
            return 'blocked'
        store.finish(job['id'],job['lease_token'],now=now)
        return 'done'
    handler=handlers.get(job['job_type'])
    if handler is None:
        store.finish(job['id'],job['lease_token'],error_code='official_adapter_not_connected',blocked=True,now=now)
        return 'blocked'
    try:
        # Registered handlers must have their own I/O timeout < the 120s lease.
        # Handler publication uses store.publish; never direct status writes.
        handler(job)
    except Exception:
        # Never persist raw provider responses, URLs, tokens, or exception text.
        store.finish(job['id'],job['lease_token'],error_code='handler_failed',now=now)
        return 'retry_or_failed'
    store.finish(job['id'],job['lease_token'],now=now)
    return 'done'
