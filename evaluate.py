#!/usr/bin/env python3
"""Evaluation Script for PII Redaction Tool.

Computes precision, recall, and F1 score by comparing detected PII
against a manually curated ground truth.

Usage:
    python evaluate.py
"""
import json
import os
from collections import defaultdict


def load_ground_truth():
    """Load or generate ground truth PII annotations."""
    gt_path = 'ground_truth.json'
    # Always regenerate to pick up any updates
    if os.path.exists(gt_path):
        os.remove(gt_path)

    # Hard-coded ground truth based on manual document review
    ground_truth = {
        'PERSON': [
            'Kushal Subbayya Hegde', 'Pushpa Kushal Hegde',
            'Rajesh Kushal Hegde', 'Rohit Kushal Hegde',
            'Rakhi Girija Shetty', 'Sarthak Malvadkar',
            'Sandesh Bhagwat', 'Amod Joshi', 'Ganesh Prasad',
            'Lokesh Shah', 'Soumavo Sarkar',
            'Kishan Rastogi', 'Abhijit Diwan',
            'Prakash Boricha',
            'Eric Bacha', 'Sachin Gawade', 'Pravin Teli',
            'Siddharth Jadhav', 'Tushar Gavankar',
            'Varun Badai', 'Hitesh Ramani',
            'Chitra Raste', 'Sharmila Joshi', 'Cherag Gyara',
            'Manisha Shukla', 'Tushar Wakhele',
            'Ashish Mathew Pulloor', 'Anand Soni',
            'Shanti Gopalkrishnan', 'Lalit Muljibhai Sarvaiya',
        ],
        'EMAIL_ADDRESS': [
            'cs.connect@kshinternational.com',
            'Sarthak.malvadkar@kshinterantional.com',
            'ksh.ipo@nuvama.com', 'customerservice.mb@nuvama.com',
            'ksh@icicisecurities.com', 'customercare@icicisecurities.com',
            'prakash.boricha@nuvama.com', 'sheetal.parab@nuvama.com',
            'ipo@trilegal.com', 'kshinternational.ipo@in.mpms.mufg.com',
            'siddharth.jadhav@hdfcbank.com', 'sachin.gawade@hdfcbank.com',
            'eric.bacha@hdfcbank.com', 'tushar.gavankar@hdfcbank.com',
            'pravin.teli2@hdfcbank.com', 'Ipocmg@icicibank.com',
            'parag.pansare@kirtanepandit.com', 'hitesh.ramani@citi.com',
            'pro@eximbankindia.in', 'sharmila.joshi@indusind.com',
            'cherag.gyara@icicibank.com', 'manisha.shukla@hdfcbank.com',
            'rm6.ifbpune@sbi.co.in', 'ashishmp@federalbank.co.in',
            'anand.soni@bajajfinserv.in',
        ],
        'PHONE_NUMBER': [
            '+91 20 45053237', '+91 22 40094400', '+91 22 6807 7100',
            '+91 81081 14949', '+91 22 30752929', '+91 22 30752928',
            '+91 22 30752914', '022-68052182', '+91 22 4079 1000',
            '+91 20 6606 4494', '+91 20 2640 3100', '+91-20-26234000',
            '+91 8879770456', '+91 20 6769 4648', '+91 20 2561 8211',
            '+91 91586 40360', '+91 20 7157 6403', '+91 (20) 6729 5100',
        ],
        'ORGANIZATION': [
            'KSH International Limited',
            'KSH International Private Limited',
            'Bhandary Metal Extrusion Private Limited',
            'Waterloo Industrial Park VI Private Limited',
            'Nuvama Wealth Management Limited',
            'ICICI Securities Limited',
            'MUFG Intime India Private Limited',
            'Kirtane & Pandit, LLP', 'Trilegal',
            'HDFC Bank Limited', 'ICICI Bank Limited',
            'Citibank N.A.', 'IndusInd Bank Limited',
            'State Bank of India', 'The Federal Bank Limited',
            'Bajaj Finance Limited', 'Export-Import Bank of India',
            'CARE Analytics and Advisory Private Limited',
            'CareEdge Research', 'Kanj & Co. LLP',
            'CARE Ratings Limited',
        ],
        'ADDRESS': [
            'Village Birdewadi', 'Birdewadi',
            'Montreal Business Centre', 'Pallod Farms',
            'Inspire BKC', 'Bandra Kurla Complex',
            'ICICI Venture House', 'Appasaheb Marathe Marg',
            'C-101, Embassy 247', 'Embassy 247',
            'L B S Marg, Vikhroli', 'Vikhroli (West)',
            'Lodha I Think Techno Campus',
            'Kanjurmarg Railway Station', 'Kanjurmarg (East)',
            'H.T.Parekh Marg', 'Backbay Reclamation Churchgate',
            'Gopal House', 'Harshal Hall',
            'PCNTDA Green Building', 'Akurdi Railway Station',
            'One World Centre', 'Senapati Bapat Marg',
            'Onyx Tower', 'Koregaon Park, Pune',
            'Bhandarkar road', 'Gen Thimmayya Road',
            'Satguru House', 'Bund Garden Road',
            'Marathon IT Park', 'Tara Chambers', 'Wakdewadi',
        ],
        'WEBSITE': [
            'www.kshinternational.com', 'www.nuvama.com',
            'www.icicisecurities.com', 'www.hdfcbank.com',
            'www.icicibank.com', 'www.in.mpms.mufg.com',
            'www.indusind.com/', 'www.bajajfinance.com',
            'www.federalbank.co.in', 'www.sbi.co.in',
            'www.eximbankindia.in/',
        ],
        'CIN': [
            'U28129PN1979PLC141032', 'L65920MH1994PLC080618',
            'L65190GJ1994PLC021012', 'U67190MH1999PTC118368',
        ],
        'SEBI_REG': [
            'INM000013004', 'INM000011179',
            'INZ000166136', 'INR000004058',
            'INBI00000063', 'INBI00000004',
        ],
    }

    with open(gt_path, 'w', encoding='utf-8') as f:
        json.dump(ground_truth, f, indent=2)

    return ground_truth


def normalize_phone(phone: str) -> str:
    """Normalize phone numbers for comparison by extracting just digits."""
    import re
    digits = re.sub(r'\D', '', phone)
    # Remove leading country code 91
    if digits.startswith('91') and len(digits) > 10:
        digits = digits[2:]
    # Remove leading 0
    if digits.startswith('0') and len(digits) > 10:
        digits = digits[1:]
    return digits


def evaluate(detection_report_path: str = 'detection_report.json'):
    """Run evaluation and compute metrics."""
    if not os.path.exists(detection_report_path):
        print(f"Error: {detection_report_path} not found. Run redact.py first.")
        return

    with open(detection_report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)

    ground_truth = load_ground_truth()

    # Group detections by type
    detected_by_type = defaultdict(set)
    for det in report['all_detections']:
        detected_by_type[det['type']].add(det['text'].strip().lower())

    print("=" * 70)
    print("EVALUATION REPORT")
    print("=" * 70)
    print()

    overall_tp = 0
    overall_fp = 0
    overall_fn = 0
    results = {}

    for pii_type in sorted(set(list(ground_truth.keys()) + list(detected_by_type.keys()))):
        gt_set = {item.strip().lower().rstrip('/') for item in ground_truth.get(pii_type, [])}
        det_set = {item.rstrip('/') for item in detected_by_type.get(pii_type, set())}

        if pii_type == 'PHONE_NUMBER':
            # Normalize phone comparison
            gt_normalized = {normalize_phone(p) for p in ground_truth.get(pii_type, [])}
            det_normalized = set()
            for d in det_set:
                det_normalized.add(normalize_phone(d))
            tp = len(gt_normalized & det_normalized)
            fp = max(0, len(det_normalized) - tp)
            fn = len(gt_normalized - det_normalized)
        elif pii_type == 'ADDRESS':
            # Use substring containment for addresses since fragments may differ
            # e.g. GT "Pallod Farms" matches detection "Off Pallod Farms"
            matched_gt = set()
            matched_det = set()
            for gt_item in gt_set:
                for det_item in det_set:
                    if gt_item in det_item or det_item in gt_item:
                        matched_gt.add(gt_item)
                        matched_det.add(det_item)
                        break
            tp = len(matched_gt)
            fp = len(det_set - matched_det)
            fn = len(gt_set - matched_gt)
        else:
            tp = len(gt_set & det_set)
            fp = len(det_set - gt_set)
            fn = len(gt_set - det_set)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        overall_tp += tp
        overall_fp += fp
        overall_fn += fn

        results[pii_type] = {
            'true_positives': tp,
            'false_positives': fp,
            'false_negatives': fn,
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1_score': round(f1, 4),
        }

        print(f"  {pii_type}:")
        print(f"    TP={tp}, FP={fp}, FN={fn}")
        print(f"    Precision: {precision:.2%}, Recall: {recall:.2%}, F1: {f1:.2%}")

        if fn > 0:
            if pii_type == 'PHONE_NUMBER':
                missed_norm = gt_normalized - det_normalized
                print(f"    Missed (normalized digits): {list(missed_norm)[:5]}")
            else:
                missed = gt_set - det_set
                print(f"    Missed: {list(missed)[:5]}")
        print()

    # Overall metrics
    overall_precision = overall_tp / (overall_tp + overall_fp) if (overall_tp + overall_fp) > 0 else 0.0
    overall_recall = overall_tp / (overall_tp + overall_fn) if (overall_tp + overall_fn) > 0 else 0.0
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0.0
    overall_accuracy = overall_tp / (overall_tp + overall_fp + overall_fn) if (overall_tp + overall_fp + overall_fn) > 0 else 0.0

    print("=" * 70)
    print("OVERALL METRICS:")
    print(f"  True Positives:  {overall_tp}")
    print(f"  False Positives: {overall_fp}")
    print(f"  False Negatives: {overall_fn}")
    print(f"  Accuracy:        {overall_accuracy:.2%}")
    print(f"  Precision:       {overall_precision:.2%}")
    print(f"  Recall:          {overall_recall:.2%}")
    print(f"  F1 Score:        {overall_f1:.2%}")
    print("=" * 70)

    eval_report = {
        'per_type': results,
        'overall': {
            'true_positives': overall_tp,
            'false_positives': overall_fp,
            'false_negatives': overall_fn,
            'accuracy': round(overall_accuracy, 4),
            'precision': round(overall_precision, 4),
            'recall': round(overall_recall, 4),
            'f1_score': round(overall_f1, 4),
        }
    }

    with open('evaluation_results.json', 'w', encoding='utf-8') as f:
        json.dump(eval_report, f, indent=2)
    print(f"\nResults saved to: evaluation_results.json")


if __name__ == '__main__':
    evaluate()
