"""Bounded deterministic worker. Unsupported integrations report BLOCKED."""
import hashlib
import time

from .store import CommerceStore


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


def run_once(store: CommerceStore, handlers=None, now=None):
    handlers=handlers or {}
    job=store.claim(now)
    if not job:
        return None
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
