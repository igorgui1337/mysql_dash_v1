from datetime import datetime, timedelta, timezone

TZ_BRT = timezone(timedelta(hours=-3))

def today_utc_bounds_v2():
    now_utc = datetime.now(timezone.utc)
    now_brt = now_utc.astimezone(TZ_BRT)
    start_brt = now_brt.replace(hour=0, minute=0, second=0, microsecond=0)
    end_brt   = start_brt + timedelta(days=1)
    start_utc = start_brt.astimezone(timezone.utc)
    end_utc   = end_brt.astimezone(timezone.utc)
    return start_utc, end_utc

def range_days_to_utc_v2(days):
    # últimos N dias (janela em BRT) → UTC
    now_utc = datetime.now(timezone.utc)
    now_brt = now_utc.astimezone(TZ_BRT)
    end_brt = now_brt.replace(hour=23, minute=59, second=59, microsecond=0)
    start_brt = (end_brt - timedelta(days=days-1)).replace(hour=0, minute=0, second=0, microsecond=0)
    start_utc = start_brt.astimezone(timezone.utc)
    end_utc   = end_brt.astimezone(timezone.utc) + timedelta(seconds=1)
    return start_utc, end_utc

def to_params(start_dt, end_dt):
    """Formata datetimes para strings usadas nos placeholders :start_utc / :end_utc."""
    return {
        "start_utc": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "end_utc":   end_dt.strftime("%Y-%m-%d %H:%M:%S"),
    }
