"""Guard Core wiring for AleDB: one config, one decorator instance.

Built against the traffic documented in issue #84: 3.32M requests in a
month, ~96% automated, including a residential-proxy scraping operation
spread over 433k one-shot IPs hammering /mutations/details. Human traffic
is a few dozen researchers a day, so these limits sit far above human
behavior.
"""
import os

from guard_core.models import BehaviorRuleConfig, SecurityConfig
from guard_core.sync.decorators import SecurityDecorator

guard_config = SecurityConfig(
    enable_penetration_detection=True,
    enable_rate_limiting=True,
    enable_rate_limit_auto_ban=True,
    rate_limit=300,
    rate_limit_window=60,
    auto_ban_threshold=40,
    auto_ban_duration=86400,
    enable_ip_banning=True,
    fail_secure=True,
    enable_redis=True,
    redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    global_behavior_rules=(
        # per-IP request cap: one-shot proxy IPs rotate identity, not volume
        BehaviorRuleConfig(
            rule_type="usage",
            threshold=2000,
            window=3600,
            action="throttle",
            correlate_with_detection=True,
        ),
        # anything already flagged by the detector gets held to half that
        BehaviorRuleConfig(
            rule_type="usage",
            threshold=500,
            window=3600,
            action="throttle",
            correlate_with_detection=True,
        ),
    ),
    behavior_scan_response_body=False,
)

guard_deco = SecurityDecorator(guard_config)
