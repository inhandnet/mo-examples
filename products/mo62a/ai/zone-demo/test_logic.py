import json
from pathlib import Path
import unittest

from logic import Occupancy, inside_polygon, validate_config


def config():
    return json.loads(Path(__file__).with_name('zone.json').read_text())


class ZoneTests(unittest.TestCase):
    def test_membership_including_boundary(self):
        polygon = validate_config(config())['polygon']
        for point in ((0.68, 0.7), (0.62, 0.55), (0.74, 0.8)):
            self.assertTrue(inside_polygon(point, polygon))
        self.assertFalse(inside_polygon((0.2, 0.7), polygon))
        self.assertFalse(inside_polygon((0.5, 0.95), polygon))

    def test_dwell_and_clear_hysteresis(self):
        state = Occupancy(config())
        self.assertIsNone(state.update(0, 1))
        self.assertEqual(state.state, 'pending')
        self.assertIsNone(state.update(0.4, 2))
        self.assertEqual(state.update(0.5, 2)['event'], 'zone_occupied')
        self.assertIsNone(state.update(0.6, 0))
        self.assertEqual(state.state, 'occupied')
        self.assertIsNone(state.update(0.9, 1))
        self.assertIsNone(state.update(1, 0))
        event = state.update(1.5, 0)
        self.assertEqual(event['event'], 'zone_cleared')
        self.assertEqual(event['occupancy_duration_s'], 1)
        self.assertEqual(state.state, 'clear')

    def test_short_detection_does_not_trigger(self):
        state = Occupancy(config())
        self.assertIsNone(state.update(0, 1))
        self.assertIsNone(state.update(0.4, 0))
        self.assertEqual(state.state, 'clear')
        self.assertIsNone(state.update(1, 1))
        self.assertIsNone(state.update(1.4, 1))
        self.assertEqual(state.update(1.5, 1)['event'], 'zone_occupied')

    def test_no_duplicate_or_synthetic_clear_at_end(self):
        state = Occupancy(config())
        state.update(0, 1)
        state.update(0.5, 1)
        self.assertIsNone(state.update(2, 3))
        self.assertEqual(state.state, 'occupied')

    def test_invalid_config(self):
        for key, value in (('score_threshold', 0.1), ('dwell_seconds', -1),
                           ('clear_seconds', float('nan')), ('zone_id', '<script>'),
                           ('polygon', [[0, 0], [1, 1], [0, 1], [1, 0]])):
            settings = config()
            settings[key] = value
            with self.assertRaises(ValueError):
                validate_config(settings)

    def test_invalid_time_and_count(self):
        state = Occupancy(config())
        state.update(1, 0)
        for timestamp, count in ((1, 0), (0, 0), (float('nan'), 0), (2, -1)):
            with self.assertRaises(ValueError):
                state.update(timestamp, count)


if __name__ == '__main__':
    unittest.main()
