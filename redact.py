#!/usr/bin/env python3
"""PII Redaction Tool - Main Script.

Reads a .docx document, detects PII, replaces with fake alternatives,
and saves a redacted version.

Usage:
    python redact.py --input input.docx --output output_redacted.docx
"""
import argparse
import json
import sys
import os
from datetime import datetime

from pii_detector import PIIDetector, PIIEntity
from pii_replacer import PIIReplacer
from docx_handler import DocxHandler


def main():
    parser = argparse.ArgumentParser(
        description='PII Redaction Tool - Detects and replaces PII in DOCX files'
    )
    parser.add_argument(
        '--input', '-i',
        default='input.docx',
        help='Path to input DOCX file (default: input.docx)'
    )
    parser.add_argument(
        '--output', '-o',
        default='output_redacted.docx',
        help='Path to output redacted DOCX file (default: output_redacted.docx)'
    )
    parser.add_argument(
        '--mapping', '-m',
        default='pii_mapping.json',
        help='Path to save PII mapping JSON (default: pii_mapping.json)'
    )
    parser.add_argument(
        '--report', '-r',
        default='detection_report.json',
        help='Path to save detection report (default: detection_report.json)'
    )
    args = parser.parse_args()

    print("=" * 70)
    print("PII REDACTION TOOL")
    print("=" * 70)
    print(f"Input:  {args.input}")
    print(f"Output: {args.output}")
    print()

    # Step 1: Load document
    print("[1/5] Loading document...")
    if not os.path.exists(args.input):
        print(f"ERROR: Input file '{args.input}' not found.")
        sys.exit(1)
    handler = DocxHandler(args.input)
    full_text = handler.get_full_text()
    print(f"       Loaded {len(full_text):,} characters")

    # Step 2: Detect PII
    print("[2/5] Detecting PII entities...")
    detector = PIIDetector()
    entities = detector.detect(full_text)

    # Count by type
    type_counts = {}
    for entity in entities:
        type_counts[entity.entity_type] = type_counts.get(entity.entity_type, 0) + 1

    print(f"       Found {len(entities)} PII entities:")
    for pii_type, count in sorted(type_counts.items()):
        print(f"         - {pii_type}: {count}")

    # Step 3: Generate replacements
    print("[3/5] Generating fake replacements...")
    replacer = PIIReplacer(seed=42)

    replacement_pairs = []
    unique_entities = {}

    for entity in entities:
        original = entity.text
        if original not in unique_entities:
            fake = replacer.get_replacement(original, entity.entity_type)
            unique_entities[original] = {
                'type': entity.entity_type,
                'replacement': fake
            }
            replacement_pairs.append((original, fake))

    print(f"       Generated {len(replacement_pairs)} unique replacements")

    # Step 4: Apply redactions to document
    print("[4/5] Applying redactions to document...")
    handler.redact_and_save(replacement_pairs, args.output)
    print(f"       Saved redacted document to: {args.output}")

    # Step 5: Save mapping and report
    print("[5/5] Saving mapping and report...")

    mapping_output = {
        'metadata': {
            'tool': 'PII Redaction Tool',
            'timestamp': datetime.now().isoformat(),
            'input_file': args.input,
            'output_file': args.output,
            'total_entities_detected': len(entities),
            'unique_entities': len(unique_entities),
        },
        'entity_counts': type_counts,
        'replacements': [
            {
                'original': orig,
                'replacement': info['replacement'],
                'type': info['type']
            }
            for orig, info in unique_entities.items()
        ]
    }

    with open(args.mapping, 'w', encoding='utf-8') as f:
        json.dump(mapping_output, f, indent=2, ensure_ascii=False)
    print(f"       Saved PII mapping to: {args.mapping}")

    report = {
        'summary': {
            'total_entities': len(entities),
            'unique_entities': len(unique_entities),
            'entity_types_found': list(type_counts.keys()),
            'entity_counts': type_counts,
        },
        'all_detections': [
            {
                'text': e.text,
                'type': e.entity_type,
                'score': e.score,
                'source': e.source,
                'start': e.start,
                'end': e.end,
            }
            for e in entities
        ]
    }

    with open(args.report, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"       Saved detection report to: {args.report}")

    print()
    print("=" * 70)
    print("REDACTION COMPLETE")
    print("=" * 70)
    print()

    # Print sample replacements
    print("Sample Replacements:")
    print("-" * 70)
    samples = list(unique_entities.items())[:25]
    for orig, info in samples:
        display_orig = orig[:40] + '...' if len(orig) > 40 else orig
        display_repl = info['replacement'][:35] + '...' if len(info['replacement']) > 35 else info['replacement']
        print(f"  [{info['type']:15s}] {display_orig:42s} -> {display_repl}")
    if len(unique_entities) > 25:
        print(f"  ... and {len(unique_entities) - 25} more")


if __name__ == '__main__':
    main()
