"""Pure, testable zone-occupancy rules; no identity tracking or safety control."""
import math
import re


def validate_config(config):
    if config.get('schema_version') != 1 or not re.fullmatch(r'[a-z0-9_-]{1,40}', config.get('zone_id', '')):
        raise ValueError('Expected schema_version=1 and a short zone_id')
    for key in ('score_threshold', 'dwell_seconds', 'clear_seconds'):
        value = config.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError('Invalid numeric setting: ' + key)
    if not 0.3 <= config['score_threshold'] <= 1:
        raise ValueError('Threshold must be >= the compiled detector floor (0.3), and <= 1')
    if not 0 <= config['dwell_seconds'] <= 60 or not 0 <= config['clear_seconds'] <= 60:
        raise ValueError('Durations must be between 0 and 60 seconds')
    points = config.get('polygon', [])
    if not 3 <= len(points) <= 12:
        raise ValueError('Use 3..12 normalized vertices, ordered around a convex polygon')
    for point in points:
        if len(point) != 2 or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1 for v in point):
            raise ValueError('Polygon coordinates must be finite values in [0,1]')
    # A strict convexity check also rejects duplicate vertices and self-crossing order.
    signs = []
    for i, a in enumerate(points):
        b = points[(i + 1) % len(points)]
        edge_signs = []
        for j, c in enumerate(points):
            if j in (i, (i + 1) % len(points)):
                continue
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if abs(cross) < 1e-10:
                raise ValueError('Polygon must be strictly convex and non-degenerate')
            edge_signs.append(cross > 0)
        if len(set(edge_signs)) != 1:
            raise ValueError('Polygon must be convex and ordered')
        signs += edge_signs
    if len(set(signs)) != 1:
        raise ValueError('Polygon vertex order is inconsistent')
    return config


def inside_polygon(point, polygon):
    """Convex polygon membership, including the boundary; normalized coordinates."""
    signs = set()
    for i, a in enumerate(polygon):
        b = polygon[(i + 1) % len(polygon)]
        cross = (b[0] - a[0]) * (point[1] - a[1]) - (b[1] - a[1]) * (point[0] - a[0])
        if abs(cross) > 1e-10:
            signs.add(cross > 0)
    return len(signs) <= 1


class Occupancy:
    """One event per zone occupancy interval, not one event per tracked person."""
    def __init__(self, config):
        self.config = validate_config(config)
        self.pending_since = self.active_since = self.clear_since = self.last_time = None

    @property
    def state(self):
        return 'occupied' if self.active_since is not None else 'pending' if self.pending_since is not None else 'clear'

    def update(self, timestamp, count):
        if not math.isfinite(timestamp) or timestamp < 0 or (self.last_time is not None and timestamp <= self.last_time):
            raise ValueError('Source timestamps must be finite and strictly increasing')
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError('Person count must be a nonnegative integer')
        self.last_time = timestamp
        event = None
        if count:
            self.clear_since = None
            if self.active_since is None:
                if self.pending_since is None:
                    self.pending_since = timestamp
                if timestamp - self.pending_since + 1e-9 >= self.config['dwell_seconds']:
                    self.active_since = self.pending_since
                    self.pending_since = None
                    event = {'event': 'zone_occupied', 'detected_since_s': self.active_since}
        else:
            self.pending_since = None
            if self.active_since is not None:
                if self.clear_since is None:
                    self.clear_since = timestamp
                if timestamp - self.clear_since + 1e-9 >= self.config['clear_seconds']:
                    event = {'event': 'zone_cleared', 'detected_since_s': self.active_since,
                             'occupancy_duration_s': self.clear_since - self.active_since}
                    self.active_since = self.clear_since = None
        if event:
            event.update({'zone_id': self.config['zone_id'], 'source_time_s': timestamp, 'people_inside': count})
        return event
