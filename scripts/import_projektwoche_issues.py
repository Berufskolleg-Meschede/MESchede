#!/usr/bin/env python3
"""Preview or publish the prepared MES project-week issue collection.

Uses the authenticated GitHub CLI, never reads or prints credentials. Writes
only issues carrying this collection's exact marker. Reruns reuse remote IDs.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'docs/issues/projektwoche'
MANIFEST = DIRECTORY / 'backlog.json'
STATE = DIRECTORY / 'published.json'


def validate(manifest):
    if manifest['schema_version'] != 1:
        raise ValueError('Unsupported manifest schema')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', manifest['repository']):
        raise ValueError('Invalid repository name')
    entries = [manifest['epic']] + manifest['issues']
    by_id = {entry['id']: entry for entry in entries}
    if len(by_id) != len(entries):
        raise ValueError('Duplicate issue IDs')
    seen, active = set(), set()

    def visit(issue_id):
        if issue_id in active:
            raise ValueError(f'Dependency cycle at {issue_id}')
        if issue_id in seen:
            return
        active.add(issue_id)
        for dependency in by_id[issue_id]['depends_on']:
            if dependency not in by_id:
                raise ValueError(f'Unknown dependency {dependency}')
            visit(dependency)
        active.remove(issue_id)
        seen.add(issue_id)

    for entry in entries:
        marker = f'<!-- {manifest["collection_id"]}:{entry["id"]} -->'
        if entry['body'].count(marker) != 1:
            raise ValueError(f'Missing or repeated marker for {entry["id"]}')
        if len(entry['body']) > 60000:
            raise ValueError(f'Issue body too long: {entry["id"]}')
        visit(entry['id'])
    if sum(entry['estimate_hours'] for entry in manifest['issues']) != 120:
        raise ValueError('Expected exactly 120 team hours')
    return entries


def gh_api(endpoint, method='GET', payload=None, paginate=False):
    command = ['gh', 'api', endpoint, '--method', method]
    if paginate:
        command += ['--paginate', '--slurp']
    if payload is not None:
        command += ['--input', '-']
    result = subprocess.run(
        command, input=json.dumps(payload, ensure_ascii=False) if payload is not None else None,
        capture_output=True, text=True, check=False,
    )
    if result.returncode:
        # GitHub CLI's API diagnostics do not include authorization headers.
        raise RuntimeError(result.stderr.strip() or 'GitHub CLI request failed')
    return json.loads(result.stdout)


def publish(manifest, entries):
    repository = manifest['repository']
    metadata = gh_api(f'repos/{repository}')
    if metadata['full_name'].lower() != repository.lower():
        raise RuntimeError('Repository identity mismatch')
    if metadata.get('archived') or not metadata.get('has_issues'):
        raise RuntimeError('Target repository does not support writable issues')
    pages = gh_api(f'repos/{repository}/issues?state=all&per_page=100', paginate=True)
    remote = [issue for page in pages for issue in page if 'pull_request' not in issue]
    found = {}
    for entry in entries:
        marker = f'<!-- {manifest["collection_id"]}:{entry["id"]} -->'
        matches = [issue for issue in remote if marker in (issue.get('body') or '')]
        if len(matches) > 1:
            raise RuntimeError(f'Duplicate remote markers for {entry["id"]}; resolve before import')
        if matches:
            found[entry['id']] = matches[0]

    def save():
        STATE.write_text(json.dumps({
            'repository': repository, 'collection_id': manifest['collection_id'],
            'issues': {key: {'number': value['number'], 'url': value['html_url']}
                       for key, value in found.items()},
        }, ensure_ascii=False, indent=2) + '\n')

    # Sequential mutations allow safe resumption after a partial import.
    for entry in entries:
        if entry['id'] in found:
            print(f'Reuse {entry["id"]}: {found[entry["id"]]["html_url"]}', flush=True)
            continue
        issue = gh_api(f'repos/{repository}/issues', method='POST', payload={
            'title': entry['title'], 'body': entry['body'],
        })
        found[entry['id']] = issue
        save()
        print(f'Created {entry["id"]}: {issue["html_url"]}', flush=True)

    epic_id = manifest['epic']['id']
    for entry in entries:
        current = found[entry['id']]
        complete_marker = f'<!-- {manifest["collection_id"]}:{entry["id"]}:links-complete -->'
        if complete_marker in (current.get('body') or ''):
            # A completed import is not a body synchronizer: preserve team edits,
            # checked tasks, reassignment notes and subsequent spec decisions.
            continue
        body = entry['body']
        if entry['id'] == epic_id:
            for child in manifest['issues']:
                body = body.replace(
                    f'**{child["id"]}**',
                    f'[{child["id"]} #{found[child["id"]]["number"]}]({found[child["id"]]["html_url"]})',
                )
        else:
            if entry['depends_on']:
                old = '- Abhängigkeiten: ' + ', '.join(entry['depends_on'])
                new = '- Abhängigkeiten: ' + ', '.join(
                    f'[{key} #{found[key]["number"]}]({found[key]["html_url"]})'
                    for key in entry['depends_on']
                )
                body = body.replace(old, new)
            body += f'\n## Sammlung\n\n[Projektwoche: Spezifikation und Aufgabenübersicht]({found[epic_id]["html_url"]})\n'
        body += '\n' + complete_marker + '\n'
        if body != (current.get('body') or '') or entry['title'] != current['title']:
            found[entry['id']] = gh_api(
                f'repos/{repository}/issues/{current["number"]}', method='PATCH',
                payload={'title': entry['title'], 'body': body},
            )
            save()
    save()
    print(f'Published {len(entries)} linked issues: {found[epic_id]["html_url"]}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Publish issues to the manifest repository')
    options = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    entries = validate(manifest)
    if not options.apply:
        print(f'Preview: {manifest["repository"]}; {len(entries)} issues; 120 team hours')
        for entry in entries:
            print(f'{entry["title"]} ({entry["estimate_hours"]} h)')
        print('No GitHub reads or writes. Use --apply after restoring repository access.')
        return
    publish(manifest, entries)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        print(f'Import stopped: {error}', file=sys.stderr)
        sys.exit(1)
