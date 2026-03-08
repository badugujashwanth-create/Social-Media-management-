import enum


class Platform(str, enum.Enum):
    facebook = 'facebook'
    linkedin = 'linkedin'
    x = 'x'
    instagram = 'instagram'


class PostTargetStatus(str, enum.Enum):
    queued = 'queued'
    publishing = 'publishing'
    success = 'success'
    failed = 'failed'
    rate_limited = 'rate_limited'
    needs_reauth = 'needs_reauth'
