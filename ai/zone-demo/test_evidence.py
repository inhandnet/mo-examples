import copy
import unittest

from compare_detections import compare, iou


def sample():
    return {'source_sha256': 'video', 'samples': [{'file': 'frame.png',
        'input_sha256': 'frame', 'detections': [
            {'label': 0, 'score': 0.8, 'box': [0, 0, 10, 10]}]}]}


class EvidenceTests(unittest.TestCase):
    def test_iou(self):
        self.assertEqual(iou([0, 0, 10, 10], [0, 0, 10, 10]), 1)
        self.assertEqual(iou([0, 0, 10, 10], [11, 0, 20, 10]), 0)

    def test_agreement_not_accuracy(self):
        report = compare(sample(), sample())
        self.assertIn('not labeled accuracy', report['scope'])
        self.assertEqual(report['frames'][0]['matches_iou_0_5'][0]['iou'], 1)

    def test_unmatched_detections_and_one_to_one(self):
        actual = sample()
        actual['samples'][0]['detections'] *= 2
        report = compare(sample(), actual)['frames'][0]
        self.assertEqual(len(report['matches_iou_0_5']), 1)
        self.assertEqual(report['unmatched_quantized'], 1)
        actual['samples'][0]['detections'] = []
        self.assertEqual(compare(sample(), actual)['frames'][0]['unmatched_cpu'], 1)

    def test_changed_input_is_rejected(self):
        for mutation in ('video', 'frames', 'bytes'):
            actual = copy.deepcopy(sample())
            if mutation == 'video':
                actual['source_sha256'] = 'changed'
            elif mutation == 'frames':
                actual['samples'] = []
            else:
                actual['samples'][0]['input_sha256'] = 'changed'
            with self.assertRaises(ValueError):
                compare(sample(), actual)


if __name__ == '__main__':
    unittest.main()
