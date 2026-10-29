#!/usr/bin/env python3
"""Download public files linked by a user-supplied OpenAIRE CSV export.

The export supplies candidates, not verified History PhDs. This collection stays
separate from the citation corpus. Reuse the existing repository transport for
robots, redirects, per-host pacing, access stops, streaming and PDF validation.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import csv
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
import threading
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.parse import urlsplit, urlunsplit, parse_qs

import fetch_base_pdfs as transport

ROOT = Path(__file__).resolve().parents[1]
FINAL = transport.PERMANENT | {'already_held', 'missing_link', 'partial_download', 'host_stopped', 'error', 'out_of_scope'}
if 'out_of_scope' not in transport.RANK:
    transport.RANK.append('out_of_scope')
LOCAL = threading.local()
OriginalParser = transport.PageParser
OriginalDSpaceCandidates = transport.dspace7_candidates
META_FIELDS = {'citation_title', 'citation_author', 'citation_dissertation_institution', 'dc.title', 'eprints.title',
               'citation_dissertation_name', 'dc.type', 'dc.language', 'dc.subject',
               'eprints.type', 'eprints.thesis_type', 'eprints.thesis_name', 'eprints.institution'}
LABELS = {'type of award', 'level of award', 'awarding institution', 'department',
          'institution', 'qualification name', 'qualification level', 'degree', 'thesis type',
          'type', 'qualification', 'degree name', 'degree level', 'degree granting institution'}
UK_INSTITUTIONS = ('oxford', 'cambridge', 'st andrews', 'nottingham', 'edinburgh',
                   'manchester', 'london', 'bristol', 'sheffield', 'durham', 'warwick',
                   'york', 'birmingham', 'leicester', 'leeds', 'liverpool', 'glasgow',
                   'aberdeen', 'dundee', 'stirling', 'newcastle', 'southampton',
                   'sussex', 'exeter', 'cardiff', 'swansea', 'bangor', 'aberystwyth',
                   'loughborough', 'lancaster', 'reading', 'portsmouth', 'plymouth',
                   'brighton', 'hull', 'kent', 'east anglia', 'essex', 'surrey',
                   'bath', 'winchester', 'royal holloway', 'birkbeck', 'queen mary',
                   'goldsmiths', 'ulster', "queen's university belfast", 'strathclyde',
                   'westminster', 'salford', 'wolverhampton', 'wales', 'sunderland',
                   'chester', 'chichester', 'lincoln', 'keele', 'northumbria',
                   'huddersfield', 'greenwich', 'bradford', 'derby', 'roehampton')


class RepositoryParser(OriginalParser):
    """Retain degree fields already read on each public landing page."""
    def __init__(self):
        super().__init__()
        self.fields = defaultdict(list)
        self.block, self.parts, self.term = None, [], ''
        self.visible, self.hidden_depth = [], 0

    def handle_starttag(self, tag, attrs):
        super().handle_starttag(tag, attrs)
        if tag in {'script', 'style'}:
            self.hidden_depth += 1
        if tag in {'dt', 'dd'}:
            self.block, self.parts = tag, []

    def handle_data(self, text):
        super().handle_data(text)
        if not self.hidden_depth and text.strip():
            self.visible.append(' '.join(text.split()))
        if self.block:
            self.parts.append(text)

    def handle_endtag(self, tag):
        super().handle_endtag(tag)
        if tag in {'script', 'style'}:
            self.hidden_depth = max(0, self.hidden_depth - 1)
        if tag == self.block:
            value = ' '.join(' '.join(self.parts).split())
            if tag == 'dt':
                self.term = value.rstrip(':').lower()
            elif self.term in LABELS:
                self.fields[self.term].append(value[:500])
            self.block = None

    def feed(self, text):
        super().feed(text)
        # Apollo renders qualification/awarder under headings, not dt/dd pairs.
        for index, value in enumerate(self.visible[:-1]):
            label = value.rstrip(':').casefold()
            if label in LABELS and self.visible[index + 1].rstrip(':').casefold() not in LABELS:
                self.fields[label].append(self.visible[index + 1][:500])
        for key, value in self.meta:
            if key in META_FIELDS:
                self.fields[key].append(value[:500])
        for key in self.fields:
            self.fields[key] = list(dict.fromkeys(self.fields[key]))
        if hasattr(LOCAL, 'pages'):
            LOCAL.pages.append(dict(fields=dict(self.fields), page_title=self.title.strip(),
                                    declared_pdf_count=len({v for k, v in self.meta if k == 'citation_pdf_url' and v})))


transport.PageParser = RepositoryParser


def verification(row, pages):
    """Require explicit repository degree/institution fields and title agreement."""
    fields = defaultdict(list)
    for page in pages:
        for key, values in page['fields'].items():
            fields[key].extend(values)
    institutions = fields['awarding institution'] + fields['citation_dissertation_institution'] + fields['degree granting institution'] + fields['eprints.institution']
    if 'University of Birmingham' in institutions:
        # UBIRA's native EPrints codes are paired with explicit Ph.D./M.Phil.
        # labels in its public subject citations; retain raw codes in metadata.
        codes = {'d_ph': 'PhD', 'm_ph': 'MPhil'}
        fields['eprints.thesis_type'] = [codes.get(v, v) for v in fields['eprints.thesis_type']]
    def british_awarder(value):
        value = re.sub(r'\s+', ' ', value.casefold().replace('’', "'")).strip(' .')
        names = {'university of ' + name for name in UK_INSTITUTIONS}
        names.update(name + ' university' for name in UK_INSTITUTIONS
                     if name not in {'york', 'newcastle', 'kent'})
        names.update({'university college london', 'imperial college london',
                      'london school of economics and political science',
                      'soas, university of london', 'soas university of london',
                      "king's college london", 'kings college london',
                      'queen mary university of london', 'royal holloway, university of london',
                      'birkbeck, university of london', "queen's university belfast"})
        return value in names
    aliases = {'ucl (university college london)': 'University College London'}
    uk = list(dict.fromkeys(aliases.get(v.casefold().strip(), v) for v in institutions
                           if british_awarder(v) or v.casefold().strip() in aliases))
    degree = sum((fields[k] for k in ('type of award', 'level of award', 'qualification name',
                                      'qualification level', 'degree', 'thesis type',
                                      'citation_dissertation_name', 'eprints.thesis_type', 'eprints.thesis_name',
                                      'type', 'qualification', 'degree name', 'degree level', 'dc.type')), [])
    doctoral = [v for v in degree if re.search(r'\bD\.?\s?Phil\b|\bPh\.?\s?D\b|\bdoctoral\b|doctor of philosophy', v, re.I)]
    explicit_awards = sum((fields[k] for k in ('type of award', 'qualification name', 'degree',
                          'thesis type', 'eprints.thesis_type', 'eprints.thesis_name')), [])
    if any(re.search(r'\bM\.?\s?Phil\b|\bMSc\b|master of', v, re.I) for v in explicit_awards):
        doctoral = []  # conflicting master's metadata requires review
    normalize_title = lambda x: re.sub(r'[^\w]+', ' ', x.casefold()).strip()
    titles = fields['citation_title'] + fields['dc.title'] + fields['eprints.title']
    # UCL's public EPrints page uses its HTML title instead of citation_title.
    # Accept only the repository's exact, known suffix with native thesis fields.
    if not titles:
        for page in pages:
            native = page['fields']
            title = page.get('page_title', '')
            if (native.get('eprints.type') == ['thesis'] and native.get('eprints.institution')
                    and re.search(r'\s+-\s+UCL Discovery\s*$', title)):
                titles.append(re.sub(r'\s+-\s+UCL Discovery\s*$', '', title).strip())
    title_match = bool(titles) and all(
        SequenceMatcher(None, normalize_title(row['Title']), normalize_title(t)).ratio() >= .90
        for t in titles)
    return dict(status='verified_uk_doctoral' if uk and doctoral and title_match else 'needs_metadata_review',
                awarding_institution=uk, doctoral_degree=doctoral, title_match=title_match,
                department=fields['department'], evidence='Public repository metadata (HTML/API); no PDF text extraction')


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(path)


def normalize(url):
    p = urlsplit(url.strip())
    host = p.netloc.lower()
    if host in {'dx.doi.org', 'www.doi.org'}:
        host = 'doi.org'
    path = p.path.rstrip('/')
    if (host == 'figshare.com' or host.endswith('.figshare.com')):
        file = re.fullmatch(r'/(?:ndownloader/)?files/(\d+)', path)
        if file:
            host, path = 'ndownloader.figshare.com', '/files/' + file[1]
    if host == 'doi.org':
        path = path.lower()
    return urlunsplit(('https', host, path, p.query, ''))


def urls(row):
    out = []
    for raw in row.get('Download From', '').split(';'):
        if raw.strip().startswith(('http://', 'https://')):
            out.append(normalize(raw))
    doi = row.get('DOI', '').strip()
    if doi:
        out.append(normalize(doi if doi.startswith('http') else 'https://doi.org/' + doi))
    return list(dict.fromkeys(out))


def group(row):
    links = urls(row)
    if not links:
        return 'missing_link'
    host = urlsplit(links[0]).netloc
    if host == 'doi.org':
        return 'doi:' + urlsplit(links[0]).path.split('/')[1]
    if host == 'hdl.handle.net':
        return 'handle:' + urlsplit(links[0]).path.split('/')[1]
    return transport.gate_key(host)


def collect_urls(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from collect_urls(v)
    elif isinstance(value, list):
        for v in value:
            yield from collect_urls(v)
    elif isinstance(value, str) and value.startswith(('http://', 'https://')):
        yield normalize(value)


def file_present(file, base):
    path = Path(file.get('path') or '')
    path = path if path.is_absolute() else base / path
    return path.is_file() and path.stat().st_size == file.get('bytes')


def dspace_degree_fields(item, host):
    md = item.get('metadata', {})
    mappings = {'dc.title': 'citation_title', 'dc.contributor.author': 'citation_author',
                'dc.type.qualificationname': 'qualification name',
                'dc.type.qualificationlevel': 'qualification level',
                'dc.publisher.institution': 'awarding institution',
                'dc.publisher.department': 'department'}
    fields = {label: [str(v['value'])[:500] for v in md.get(key, []) if v.get('value')]
              for key, label in mappings.items()}
    if host == 'era.ed.ac.uk':
        publishers = [v['value'].strip() for v in md.get('dc.publisher', []) if v.get('value')]
        fields['native publisher'] = publishers
        approved = {'The University of Edinburgh', 'University of Edinburgh',
                    'The University of Edinburgh. College of Humanities and Social Science'}
        if any(p in approved for p in publishers):
            fields['awarding institution'] = ['University of Edinburgh']
    return fields


def university_dspace_candidates(page_url, link, chain):
    """Apollo's public REST service is on a separate host from its Angular UI."""
    parts = urlsplit(page_url)
    if parts.netloc not in {'www.repository.cam.ac.uk', 'repository.cam.ac.uk', 'era.ed.ac.uk'}:
        return OriginalDSpaceCandidates(page_url, link, chain)
    api = 'https://era.ed.ac.uk/server/api' if parts.netloc == 'era.ed.ac.uk' else 'https://api.repository.cam.ac.uk/server/api'
    match = re.search(r'/(?:items|entities/[a-z]+)/([0-9a-f-]{36})', parts.path)
    if match:
        item_url = api + '/core/items/' + match[1]
    else:
        handle = re.search(r'/handle/(\d[^/?#]*/[^/?#]+)', parts.path)
        if not handle:
            return []
        item_url = api + '/pid/find?id=' + handle[1]
    cached = ROOT / 'data/field-research/openaire-uk-downloads-2026-10-26/edinburgh/native-items' / (match[1] + '.json') if parts.netloc == 'era.ed.ac.uk' and match else None
    if cached and cached.exists():
        item = json.loads(cached.read_text())
        chain.append(item_url)
    else:
        item = json.loads(transport.follow(item_url, 'application/json', transport.read_body, chain))
    fields = dspace_degree_fields(item, parts.netloc)
    bundle_url = item['_links']['bundles']['href'] + '?embed=bitstreams'
    bundles = json.loads(transport.follow(bundle_url, 'application/json', transport.read_body, chain))
    candidates = []
    for bundle in bundles.get('_embedded', {}).get('bundles', []):
        if bundle.get('name') != 'ORIGINAL':
            continue
        embedded = bundle.get('_embedded', {}).get('bitstreams')
        if embedded is None:
            embedded = json.loads(transport.follow(bundle['_links']['bitstreams']['href'],
                                   'application/json', transport.read_body, chain))
        streams = embedded if isinstance(embedded, list) else embedded.get('_embedded', {}).get('bitstreams', [])
        for stream in streams:
            content = stream.get('_links', {}).get('content', {}).get('href')
            if content and (stream.get('name') or '').lower().endswith('.pdf'):
                candidates.append(content)
    if hasattr(LOCAL, 'pages'):
        LOCAL.pages.append(dict(fields=fields, page_title=item.get('name', ''),
                                metadata_url=item_url, declared_pdf_count=len(candidates)))
    return list(dict.fromkeys(candidates))


transport.dspace7_candidates = university_dspace_candidates


def retryable_robots_timeout(row):
    outcome = row.get('metadata_status', {}) if row.get('status') == 'already_held' else row
    reason = outcome.get('reason') or ''
    return (outcome.get('status') == 'robots_disallowed'
            and 'robots.txt unreachable' in reason and 'timed out' in reason.lower())


def retryable_network_hold(row):
    """Retry interrupted transport/server failures, preserving all access holds."""
    reason = str(row.get('reason') or '')
    if row.get('status') == 'host_stopped':
        return reason.endswith('five consecutive network/5xx errors')
    return (row.get('status') == 'error' and bool(re.search(
        r'HTTP 50\d\b|TimeoutError|timed out|ConnectionResetError|Connection reset|'
        r'URLError|incomplete body', reason, re.I)))


def cambridge_rest_attempt(row, link):
    """Read Apollo's public record/file metadata directly, preserving file access checks."""
    host_slug = 'era.ed.ac.uk' if urlsplit(link).netloc == 'era.ed.ac.uk' else 'www.repository.cam.ac.uk'
    attempt = dict(link=link, chain=[], landing_url=link, pdf_urls=[],
                   found_by='edinburgh_public_rest' if host_slug == 'era.ed.ac.uk' else 'cambridge_public_rest', files=[])
    try:
        candidates = university_dspace_candidates(link, link, attempt['chain'])[:transport.MAX_PARTS]
        attempt['pdf_urls'] = candidates
        if not candidates:
            raise transport.Outcome('no_pdf_found', 'No PDF listed in the public ORIGINAL bundle')
        problems = []
        for index, url in enumerate(candidates):
            path = transport.ARGS.out / ('pdf/base/' + host_slug) / (
                transport.safe_id(row['id']) + ('' if index == 0 else f'.{index}') + '.pdf')
            try:
                saved = transport.existing_file(path, url) if path.exists() else None
                if saved is None:
                    saved = transport.follow(url, 'application/pdf,*/*;q=0.8',
                        lambda response, final_url, host, destination=path:
                            transport.save_pdf(response, final_url, host, destination), attempt['chain'])
                attempt['files'].append(saved)
            except transport.Outcome as exc:
                problems.append(exc)
                break
        if attempt['files']:
            attempt.update(status='downloaded', reason=None)
            if problems:
                attempt['part_problems'] = [f'{p.status}: {p.reason}' for p in problems]
        else:
            raise min(problems, key=lambda p: transport.RANK.index(p.status))
    except transport.Outcome as exc:
        transport.raise_into(attempt, exc)
    except Exception as exc:
        attempt.update(status='error', reason=f'{type(exc).__name__}: {exc}')
    return attempt


def sussex_rest_attempt(row, link, holdings):
    """Use Sussex's documented public Figshare API and declared download URLs."""
    attempt = dict(link=link, chain=[], landing_url=link, pdf_urls=[],
                   found_by='sussex_public_rest', files=[])
    try:
        match = re.search(r'/v2/articles/(\d+)$', urlsplit(link).path)
        if not match or urlsplit(link).netloc != 'api.figshare.com':
            raise transport.Outcome('out_of_scope', 'Not a public Figshare article API URL')
        item = json.loads(transport.follow(link, 'application/json', transport.read_body, attempt['chain']))
        native = item.get('url_public_html') or ''
        custom = {v['name'].casefold(): v.get('value') for v in item.get('custom_fields', [])}
        values = lambda value: value if isinstance(value, list) else [str(value)] if value else []
        fields = dict(citation_title=[item['title']],
                      citation_author=[a['full_name'] for a in item.get('authors', []) if a.get('full_name')],
                      **{'awarding institution': values(custom.get('institution')),
                         'qualification name': values(custom.get('qualification name')),
                         'qualification level': values(custom.get('qualification level')),
                         'department': values(custom.get('department affiliated with'))})
        pdfs = [f for f in item.get('files', []) if not f.get('is_link_only')
                and f.get('name', '').lower().endswith('.pdf') and f.get('download_url')]
        LOCAL.pages.append(dict(fields=fields, page_title=item['title'], metadata_url=link,
                                native_url=native, declared_pdf_count=len(pdfs)))
        attempt['landing_url'] = native
        departments = set(fields['department'])
        if (urlsplit(native).netloc != 'sussex.figshare.com'
                or item.get('defined_type_name') != 'thesis'
                or not departments.intersection({'History Theses', 'Art History Theses', 'American Studies Theses'})):
            raise transport.Outcome('out_of_scope', 'Native Sussex thesis department outside History/Art History/American Studies')
        if verification(row, LOCAL.pages)['status'] != 'verified_uk_doctoral':
            raise transport.Outcome('out_of_scope', 'Native metadata does not establish a matching UK doctoral thesis')
        if item.get('is_embargoed') or item.get('download_disabled') or item.get('is_confidential'):
            raise transport.Outcome('restricted', 'Public API identifies embargo, confidentiality or disabled downloads')
        if not pdfs:
            raise transport.Outcome('no_pdf_found', 'No public PDF declared by Sussex Figshare API')
        attempt['pdf_urls'] = [f['download_url'] for f in pdfs]
        if len(pdfs) > transport.MAX_PARTS:
            raise transport.Outcome('no_pdf_found', 'Too many declared PDF parts; needs complete-volume review')
        problems = []
        for index, file in enumerate(pdfs):
            url = file['download_url']
            held = holdings.get(normalize(url))
            path = transport.ARGS.out / 'pdf/base/sussex.figshare.com' / (
                transport.safe_id(row['id']) + ('' if index == 0 else f'.{index}') + '.pdf')
            try:
                if held and len(pdfs) == 1:
                    attempt['files'] = held['files']; attempt['reused_holding'] = held['source_log']
                    break
                saved = transport.existing_file(path, url) if path.exists() else None
                if saved is None:
                    saved = save_public_sussex_file(file, path, attempt['chain'])
                attempt['files'].append(saved)
            except transport.Outcome as exc:
                problems.append(exc); break
        if attempt['files']:
            attempt.update(status='downloaded', reason=None)
            if problems:
                attempt['part_problems'] = [f'{p.status}: {p.reason}' for p in problems]
        else:
            raise problems[0]
    except transport.Outcome as exc:
        transport.raise_into(attempt, exc)
    except Exception as exc:
        attempt.update(status='error', reason=f'{type(exc).__name__}: {exc}')
    return attempt


def authorized_sussex_delivery(url, file_id):
    """A fresh Figshare redirect grants one named object, never a bucket listing."""
    parts = urlsplit(url)
    query = parse_qs(parts.query)
    return (parts.scheme == 'https' and parts.netloc == 's3-eu-west-1.amazonaws.com'
            and parts.path.startswith(f'/pstorage-sussex-87467812357921/{file_id}/')
            and query.get('X-Amz-Algorithm') == ['AWS4-HMAC-SHA256']
            and bool(query.get('X-Amz-Signature')) and bool(query.get('X-Amz-Expires')))


def save_public_sussex_file(file, destination, chain):
    """Follow a public file grant to S3 object storage, retaining download checks.

    The shared S3 service root has no bucket and returns403 for /robots.txt.
    That is not the publisher's robots policy. Check the actual Figshare origin,
    then use only its fresh signed redirect for the exact public Sussex file ID.
    Any content401/403/429 still stops access; all other routes use normal follow.
    """
    url = normalize(file['download_url'])
    parts = urlsplit(url)
    if parts.netloc != 'ndownloader.figshare.com' or parts.path != '/files/' + str(file['id']):
        return transport.follow(url, 'application/pdf,*/*;q=0.8',
            lambda response, final_url, host: transport.save_pdf(response, final_url, host, destination), chain)
    host = transport.get_host(parts.netloc)
    transport.ensure_robots(host, 'https')
    if host.robots_block or not transport.allowed(host.rules, parts.path):
        raise transport.Outcome('robots_disallowed', host.robots_block or 'Publisher robots disallows file URL')
    if host.stopped:
        raise transport.Outcome('host_stopped', host.stopped)
    chain.append(url)
    target = None
    try:
        with transport.request(host, url, 'application/pdf,*/*;q=0.8') as response:
            return transport.save_pdf(response, url, host, destination)
    except HTTPError as exc:
        location = exc.headers.get('Location')
        code = exc.code; exc.close()
        if code in (301, 302, 303, 307, 308) and location:
            target = location
        elif code == 401:
            raise transport.Outcome('restricted', 'HTTP401 on declared public file URL')
        else:
            if code in (403, 429):
                transport.stop_host(host, f'HTTP{code} on declared public file URL')
                raise transport.Outcome('host_stopped', host.stopped)
            raise transport.Outcome('error', f'HTTP{code} on declared public file URL')
    if not authorized_sussex_delivery(target, file['id']):
        return transport.follow(target, 'application/pdf,*/*;q=0.8',
            lambda response, final_url, host: transport.save_pdf(response, final_url, host, destination), chain)
    delivery = transport.get_host(urlsplit(target).netloc)
    if delivery.stopped:
        raise transport.Outcome('host_stopped', delivery.stopped)
    # Do not persist expiring signatures; stable publisher file URL is provenance.
    chain.append(urlsplit(target)._replace(query='').geturl())
    try:
        with transport.request(delivery, target, 'application/pdf,*/*;q=0.8') as response:
            saved = transport.save_pdf(response, url, delivery, destination)
            saved['delivery_method'] = 'Fresh native Figshare signed grant for exact Sussex object'
            return saved
    except HTTPError as exc:
        code = exc.code; exc.close()
        if code == 401:
            raise transport.Outcome('restricted', 'HTTP401 on public object delivery')
        if code in (403, 429):
            transport.stop_host(delivery, f'HTTP{code} on public object delivery')
            raise transport.Outcome('host_stopped', delivery.stopped)
        raise transport.Outcome('error', f'HTTP{code} on public object delivery')


def retryable_cambridge_recovery(row):
    reason = row.get('reason') or ''
    wrong_api = 'https://www.repository.cam.ac.uk/server/api/' in reason
    transient = bool(re.search(r'HTTP 50[234]', reason)) and 'repository.cam.ac.uk' in reason
    return row.get('status') in {'not_found', 'error'} and (wrong_api or transient)


def unique_doctorates(results):
    """Count complete50+page works once, using native identity and file hashes."""
    identities, hashes, unique = set(), set(), []
    for row in results:
        if row.get('status') not in {'downloaded', 'already_held'}:
            continue
        if row.get('degree_verification', {}).get('status') != 'verified_uk_doctoral':
            continue
        files = row.get('files') or []
        if sum(f.get('pages') or 0 for f in files) < 50:
            continue
        fingerprint = {f['sha256'] for f in files if f.get('sha256')}
        fields = defaultdict(list)
        for page in row.get('repository_metadata', []):
            for key, values in page.get('fields', {}).items():
                fields[key].extend(values)
        title = next(iter(fields['citation_title']), row.get('title', ''))
        authors = fields['citation_author'] or [row.get('authors', '')]
        institution = row['degree_verification']['awarding_institution']
        clean = lambda v: re.sub(r'[^\w]+', ' ', v.casefold()).strip()
        identity = (clean(title), tuple(sorted({clean(a) for a in authors})),
                    tuple(sorted({clean(i) for i in institution})))
        if identity in identities or fingerprint.intersection(hashes):
            continue
        identities.add(identity)
        hashes.update(fingerprint)
        unique.append(row)
    return unique


def existing_holdings(storage, wanted):
    """Use exact logged URLs and readable existing files, without extracting text."""
    index = {}
    logs = list((ROOT / 'data/field-research').rglob('downloads*.jsonl'))
    pilot = storage / 'pilot-results.jsonl'
    if pilot.exists():
        logs.append(pilot)
    for log in sorted(logs):
        try:
            lines = log.read_text().splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get('status') != 'downloaded' or row.get('part_problems'):
                continue
            matching_urls = set(collect_urls(row)).intersection(wanted)
            if not matching_urls:
                continue
            files = []
            provenance = log.parent / 'input-provenance.json'
            base = log.parent
            if provenance.exists():
                base = Path(json.loads(provenance.read_text()).get('pdf_storage', str(base)))
            for f in row.get('files') or []:
                if not f.get('path'):
                    continue
                path = Path(f['path'])
                path = path if path.is_absolute() else base / path
                if path.is_file() and path.stat().st_size == f.get('bytes'):
                    files.append(dict(f, path=str(path.resolve())))
            if not files or len(files) != len(row.get('files') or []):
                continue
            for url in matching_urls:
                index[url] = dict(files=files, source_log=str(log), matched_url=url)
    return index


def fetch(row, index, storage):
    LOCAL.pages = []
    result = dict(id=row['id'], csv_row=row['csv_row'], title=row['Title'],
                  authors=row['Authors'], organizations=row['Related Organizations'],
                  publication_year=row['Publication Year'], doi=row['DOI'],
                  checked_at=now(), candidate_links=row['candidate_links'],
                  qualification='OpenAIRE candidate; awarding institution, degree and History programme unverified',
                  files=[], attempts=[])
    def finish(value):
        value['repository_metadata'] = LOCAL.pages
        if value['status'] == 'downloaded' and any(p.get('declared_pdf_count', 0) > transport.MAX_PARTS for p in LOCAL.pages):
            value.update(status='partial_download', reason='Repository declares more PDF parts than the retrieval limit; complete work not certified')
        value['degree_verification'] = verification(row, LOCAL.pages)
        if value['degree_verification']['status'] == 'verified_uk_doctoral':
            value['qualification'] = 'UK doctoral award verified from repository or British Library metadata; subject scope recorded separately'
        return value

    def metadata_only(response, url, host):
        first = response.read(4096)
        if b'%PDF' in first[:1024]:
            return
        body = first + response.read(transport.MAX_LANDING_BYTES)
        if transport.is_challenge(body):
            transport.stop_host(host, 'bot challenge on metadata page ' + url)
            raise transport.Outcome('host_stopped', host.stopped)
        parser = RepositoryParser()
        parser.feed(body.decode('utf-8', 'replace'))

    discovered = []
    portal = row.get('Ethos URL') or next((u for u in row['candidate_links'] if urlsplit(u).netloc == 'ethos.bl.uk'), None)
    if portal:
        def read_ethos(response, url, host):
            body = response.read(transport.MAX_LANDING_BYTES)
            if transport.is_challenge(body):
                transport.stop_host(host, 'bot challenge on EThOS record ' + url)
                raise transport.Outcome('host_stopped', host.stopped)
            parser = RepositoryParser()
            parser.feed(body.decode('utf-8', 'replace'))
            for anchor in parser.anchors:
                if 'external' in anchor.get('rel', '').split() and anchor['href'].startswith(('http://', 'https://')):
                    target = normalize(anchor['href'])
                    host = urlsplit(target).netloc
                    if host.endswith('.ac.uk') or host in {'doi.org', 'hdl.handle.net', 'figshare.com'} or host.endswith(('.figshare.com', '.worktribe.com')):
                        discovered.append(target)
        chain = []
        try:
            transport.follow(portal, 'text/html', read_ethos, chain)
            result['ethos_resolution'] = dict(record_url=portal, chain=chain, repository_links=list(dict.fromkeys(discovered)))
        except transport.Outcome as exc:
            result['ethos_resolution'] = dict(record_url=portal, status=exc.status, reason=exc.reason)

    for url in row['candidate_links']:
        has_figshare_api = any(urlsplit(u).netloc == 'api.figshare.com'
                              and re.fullmatch(r'/v2/articles/\d+', urlsplit(u).path)
                              for u in row['candidate_links'])
        if url in index and not has_figshare_api:
            held = index[url]
            chain = []
            metadata_url = next((u for u in row['candidate_links']
                if urlsplit(u).netloc == urlsplit(url).netloc
                and re.search(r'/(?:id/eprint/)?\d+/?$|/handle/[^/]+/[^/]+/?$|/items/[0-9a-f-]{36}/?$', urlsplit(u).path)), url)
            metadata_url = next((u for u in row['candidate_links'] if urlsplit(u).netloc == 'era.ed.ac.uk'
                                 and '/items/' in urlsplit(u).path), metadata_url)
            try:
                if urlsplit(metadata_url).netloc in {'www.repository.cam.ac.uk', 'repository.cam.ac.uk', 'era.ed.ac.uk'}:
                    university_dspace_candidates(metadata_url, metadata_url, chain)
                else:
                    transport.follow(metadata_url, 'text/html,*/*;q=0.5', metadata_only, chain)
            except transport.Outcome as exc:
                result['metadata_status'] = dict(status=exc.status, reason=exc.reason)
            return finish(dict(result, status='already_held', files=held['files'],
                               metadata_chain=chain, matched_url=url, holding_source_log=held['source_log']))
    links = list(dict.fromkeys(discovered + [u for u in row['candidate_links'] if urlsplit(u).netloc != 'ethos.bl.uk']))
    if not links:
        return finish(dict(result, status='no_pdf_found' if portal else 'missing_link',
                           reason='EThOS record has no usable repository link' if portal else 'Export has neither download link nor DOI'))
    for link in links:
        if urlsplit(link).netloc == 'api.figshare.com' and re.fullmatch(r'/v2/articles/\d+', urlsplit(link).path):
            attempt = sussex_rest_attempt(row, link, index)
        elif urlsplit(link).netloc in {'www.repository.cam.ac.uk', 'repository.cam.ac.uk', 'era.ed.ac.uk'}:
            attempt = cambridge_rest_attempt(row, link)
        else:
            attempt = transport.try_link({'cluster_id': row['id']}, link)
        result['attempts'].append(attempt)
        if attempt['status'] == 'downloaded':
            result.update(status='partial_download' if attempt.get('part_problems') else 'downloaded',
                          files=attempt['files'], landing_url=attempt.get('landing_url'),
                          pdf_urls=attempt.get('pdf_urls'), reason=attempt.get('part_problems'))
            return finish(result)
        # A retired EPrints file may have a replacement on its public item page.
        # Follow that page only after a genuine404, never after an access denial.
        if attempt['status'] == 'not_found':
            p = urlsplit(link)
            m = re.fullmatch(r'/(\d+)/.+\.pdf', p.path, re.I)
            if m and 'nottingham.ac.uk' in p.netloc:
                item = urlunsplit((p.scheme, p.netloc, '/' + m[1] + '/', '', ''))
                if item not in links:
                    links.append(item)
        if attempt['status'] in {'host_stopped', 'robots_disallowed', 'restricted', 'out_of_scope'}:
            break
    best = min(result['attempts'], key=lambda a: transport.RANK.index(a['status']))
    return finish(dict(result, status=best['status'], reason=best.get('reason')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=ROOT / 'data/field-research/openaire-uk-downloads-2026-10-26')
    parser.add_argument('--storage', type=Path, default=Path('/mnt/e/historiography-dissertation-pdfs/openaire-uk-2026-10-26'))
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--min-delay', type=float, default=5)
    parser.add_argument('--pilot-per-group', type=int)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--baseline-log', type=Path, action='append', default=[])
    parser.add_argument('--stop-after-verified', type=int)
    parser.add_argument('--skip-hosts', nargs='*', default=[])
    parser.add_argument('--retry-transient-robots', action='store_true',
                        help='Retry only records held by an earlier robots network timeout; access denials stay held')
    parser.add_argument('--retry-cambridge-recovery', action='store_true',
                        help='Retry the corrected Apollo REST routing and transient502/503/504 errors only')
    parser.add_argument('--retry-sussex-delivery', action='store_true',
                        help='Retry only earlier shared-S3-root robots holds on native public Sussex file grants')
    parser.add_argument('--retry-network-holds', action='store_true',
                        help='Retry only transient network/5xx host stops and interrupted transfers; restrictions remain held')
    args = parser.parse_args()
    if any((folder / 'pause.json').exists() for folder in (args.out, args.out.parent)):
        parser.error('Collection paused by user. Remove pause.json only after explicit user resumption.')
    if not str(args.storage.resolve()).startswith('/mnt/e/'):
        parser.error('PDF storage must be on E:')
    args.out.mkdir(parents=True, exist_ok=True)
    args.storage.mkdir(parents=True, exist_ok=True)
    transport.ARGS = SimpleNamespace(out=args.storage, min_delay=args.min_delay,
                                    resolver_delay=2, min_pages=1, max_mb=1000)
    transport.SKIP_HOSTS.update({
        'jscholarship.library.jhu.edu': 'User instruction: Johns Hopkins is browser-download-only',
        'dash.harvard.edu': 'Separate existing Harvard collector; not resumed here',
        'ecommons.cornell.edu': 'Separate Cornell access hold; not resumed here',
        'escholarship.org': 'Existing UC browser-download-only access hold'})
    transport.SKIP_HOSTS.update({host: 'Separate active university batch; no overlapping requests' for host in args.skip_hosts})
    with args.csv.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    for number, row in enumerate(rows, 2):
        identity = json.dumps(row, sort_keys=True, ensure_ascii=False).encode()
        row.update(id='openaire-' + hashlib.sha256(identity).hexdigest()[:20],
                   csv_row=number, candidate_links=urls(row), repository_group=group(row))
    assert len({row['id'] for row in rows}) == len(rows), 'Repeated identical CSV rows need explicit clustering'
    provenance = dict(input_csv=str(args.csv), input_sha256=hashlib.sha256(args.csv.read_bytes()).hexdigest(),
                      records=len(rows), created_at=now(), pdf_storage=str(args.storage),
                      qualification='Candidate collection only; no citation extraction or corpus/website update',
                      min_delay_seconds=args.min_delay, pdf_min_pages=1)
    pin = args.out / 'input-provenance.json'
    if pin.exists():
        assert json.loads(pin.read_text())['input_sha256'] == provenance['input_sha256'], 'Input changed'
    else:
        write(pin, provenance)
    (args.out / 'records.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
    if args.prepare_only:
        print(json.dumps(provenance, indent=2))
        return
    lock = threading.Lock()
    # Prevent overlapping runs from issuing requests to the same repositories.
    import fcntl
    run_lock = (args.out / 'run.lock').open('w')
    fcntl.flock(run_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    log = args.out / 'downloads.jsonl'
    done = {}
    if log.exists():
        for line in log.read_text().splitlines():
            row = json.loads(line)
            done[row['id']] = row
    if args.retry_transient_robots:
        retry_ids = [identifier for identifier, row in done.items() if retryable_robots_timeout(row)]
        for identifier in retry_ids:
            del done[identifier]
        print('Retrying', len(retry_ids), 'earlier robots network timeouts; access denials remain held', flush=True)
    if args.retry_cambridge_recovery:
        retry_ids = [identifier for identifier, row in done.items() if retryable_cambridge_recovery(row)]
        for identifier in retry_ids:
            del done[identifier]
        print('Retrying', len(retry_ids), 'Cambridge routing/transient-server failures; access denials remain held', flush=True)
    if args.retry_sussex_delivery:
        retry_ids = [identifier for identifier, row in done.items()
                     if row.get('status') == 'robots_disallowed'
                     and 's3-eu-west-1.amazonaws.com: robots.txt answered HTTP 403' in str(row.get('reason'))
                     and any(a.get('found_by') == 'sussex_public_rest' for a in row.get('attempts', []))]
        for identifier in retry_ids:
            del done[identifier]
        print('Retrying', len(retry_ids), 'public Sussex object-delivery holds; restrictions remain held', flush=True)
    if args.retry_network_holds:
        retry_ids = [identifier for identifier, row in done.items() if retryable_network_hold(row)]
        for identifier in retry_ids:
            del done[identifier]
        print('Retrying', len(retry_ids), 'transient network/server holds; access denials remain held', flush=True)
    for identifier, result in list(done.items()):
        if result['status'] in {'downloaded', 'already_held'} and (
                not result.get('files') or not all(file_present(f, args.storage) for f in result['files'])):
            del done[identifier]
    print('Indexing existing holdings for', len(rows), 'export candidates', flush=True)
    held = existing_holdings(args.storage, {url for row in rows for url in row['candidate_links']})
    print('Found', len(held), 'existing exact-URL matches; starting repository requests', flush=True)
    groups = defaultdict(list)
    baseline = []
    for path in args.baseline_log:
        latest = {}
        for line in path.read_text().splitlines():
            record = json.loads(line)
            latest[record['id']] = record
        baseline.extend(latest.values())
    for row in rows:
        if done.get(row['id'], {}).get('status') in FINAL:
            continue
        groups[row['repository_group']].append(row)

    def summary(state):
        with transport.HOSTS_LOCK:
            hosts = list(transport.HOSTS.values())
        verified = len(unique_doctorates([*baseline, *done.values()]))
        target_met = bool(args.stop_after_verified and verified >= args.stop_after_verified)
        if target_met:
            transport.STOP.set()
        value = dict(status='target_met' if target_met else state, updated_at=now(), records=len(rows),
                     processed=len(done), remaining=len(rows) - len(done),
                     statuses=dict(Counter(r['status'] for r in done.values())),
                     verified_uk_doctoral_downloads=verified,
                     uk_doctoral_target=args.stop_after_verified or 2000,
                     newly_downloaded_bytes=sum(f['bytes'] for r in done.values()
                                                if r['status'] in {'downloaded', 'partial_download'} for f in r['files']),
                     storage=str(args.storage),
                     stopped_hosts={h.netloc: h.stopped for h in hosts if h.stopped},
                     robots_blocked={h.netloc: h.robots_block for h in hosts if h.robots_block})
        write(args.out / 'summary.json', value)
        return value

    def run_group(batch):
        selected = batch[:args.pilot_per_group] if args.pilot_per_group else batch
        for row in selected:
            if any((folder / 'pause.json').exists() for folder in (args.out, args.out.parent)):
                transport.STOP.set()
            if not transport.space_ok([(args.storage, 30), (Path('/mnt/c'), 5)]):
                transport.STOP.set()
            if transport.STOP.is_set():
                break
            try:
                result = fetch(row, held, args.storage)
            except Exception as exc:
                result = dict(id=row['id'], csv_row=row['csv_row'], title=row['Title'],
                              status='error', reason=f'{type(exc).__name__}: {exc}', files=[])
            with lock:
                done[row['id']] = result
                with log.open('a') as f:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
                if result['status'] == 'downloaded':
                    for url in collect_urls(result):
                        held[url] = dict(files=[dict(f, path=str(args.storage / f['path'])) for f in result['files']],
                                         source_log=str(log), matched_url=url)
                summary('running')
                print(f"{len(done)}/{len(rows)} {result['status']} {row['Title'][:95]}", flush=True)
            if (result['status'] == 'host_stopped'
                    and str(result.get('reason', '')).endswith('five consecutive network/5xx errors')):
                # Leave the rest of this batch pending after a server outage.
                # Do not manufacture hundreds of per-record failures without requests.
                break
    summary('running')
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed([pool.submit(run_group, batch) for batch in sorted(groups.values(), key=len, reverse=True)]):
            future.result()
    print(json.dumps(summary('complete' if len(done) == len(rows) else 'incomplete'), indent=2), flush=True)


if __name__ == '__main__':
    main()
