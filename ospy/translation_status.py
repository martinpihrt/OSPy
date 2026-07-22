"""Read-only translation completeness checks for Diagnostics."""

import ast
import copy
import os
import re
import threading


TRANSLATION_WARNING_PERCENT = 80.0
SOURCE_LOCALE = 'en_US'
_FIELD_RE = re.compile(
    r'^(msgctxt|msgid|msgid_plural|msgstr(?:\[(\d+)\])?)\s+(.*)$'
)
_cache_lock = threading.RLock()
_cache = {'signature': None, 'data': None}


class TranslationCatalogError(ValueError):
    pass


def _quoted_value(value, path, line_number):
    try:
        decoded = ast.literal_eval(value.strip())
    except (SyntaxError, ValueError) as err:
        raise TranslationCatalogError(
            '{}:{}: {}'.format(path, line_number, err)
        )
    if not isinstance(decoded, str):
        raise TranslationCatalogError(
            '{}:{}: invalid catalog string'.format(path, line_number)
        )
    return decoded


def _catalog_entries(path):
    """Return current PO/POT entries without executing catalog content."""
    entries = {}
    entry = None
    active_field = None

    def ensure_entry():
        nonlocal entry
        if entry is None:
            entry = {
                'context': '', 'msgid': None, 'plural': None,
                'translations': {}, 'fuzzy': False, 'obsolete': False,
            }
        return entry

    def finish_entry():
        nonlocal entry, active_field
        if (entry is not None and not entry['obsolete'] and
                entry['msgid'] not in (None, '')):
            key = entry['msgid']
            if entry['context']:
                key = entry['context'] + '\x04' + key
            values = list(entry['translations'].values())
            entries[key] = {
                'translated': bool(values) and all(
                    bool(value.strip()) for value in values
                ) and not entry['fuzzy'],
                'fuzzy': entry['fuzzy'],
            }
        entry = None
        active_field = None

    try:
        with open(path, 'r', encoding='utf-8-sig') as catalog:
            for line_number, raw_line in enumerate(catalog, 1):
                line = raw_line.rstrip('\r\n')
                if not line.strip():
                    finish_entry()
                    continue
                if line.startswith('#~'):
                    ensure_entry()['obsolete'] = True
                    active_field = None
                    continue
                if line.startswith('#,'):
                    flags = [item.strip() for item in line[2:].split(',')]
                    if 'fuzzy' in flags:
                        ensure_entry()['fuzzy'] = True
                    active_field = None
                    continue
                if line.startswith('#'):
                    active_field = None
                    continue

                match = _FIELD_RE.match(line)
                if match:
                    field, plural_index, raw_value = match.groups()
                    value = _quoted_value(raw_value, path, line_number)
                    current = ensure_entry()
                    if field == 'msgctxt':
                        current['context'] = value
                        active_field = ('context', None)
                    elif field == 'msgid':
                        current['msgid'] = value
                        active_field = ('msgid', None)
                    elif field == 'msgid_plural':
                        current['plural'] = value
                        active_field = ('plural', None)
                    else:
                        index = int(plural_index or 0)
                        current['translations'][index] = value
                        active_field = ('translation', index)
                    continue

                if line.startswith('"') and active_field is not None:
                    value = _quoted_value(line, path, line_number)
                    current = ensure_entry()
                    field, index = active_field
                    if field == 'translation':
                        current['translations'][index] = (
                            current['translations'].get(index, '') + value
                        )
                    else:
                        current[field] = (current.get(field) or '') + value
                    continue

                raise TranslationCatalogError(
                    '{}:{}: unsupported catalog line'.format(path, line_number)
                )
        finish_entry()
    except (OSError, UnicodeError) as err:
        raise TranslationCatalogError('{}: {}'.format(path, err))
    return entries


def _file_signature(paths):
    signature = []
    for path in paths:
        try:
            stat = os.stat(path)
            signature.append((path, stat.st_mtime_ns, stat.st_size))
        except OSError:
            signature.append((path, None, None))
    return tuple(signature)


def translation_coverage(localedir, languages, use_cache=True):
    """Compare every language PO catalog with the current POT template."""
    locales = list(languages.items())
    pot_path = os.path.join(localedir, 'ospy_messages.pot')
    po_paths = [
        os.path.join(localedir, locale, 'LC_MESSAGES', 'ospy_messages.po')
        for locale, unused_name in locales if locale != SOURCE_LOCALE
    ]
    signature = (tuple(locales), _file_signature([pot_path] + po_paths))

    with _cache_lock:
        if (use_cache and _cache['signature'] == signature and
                _cache['data'] is not None):
            return copy.deepcopy(_cache['data'])

    source_entries = _catalog_entries(pot_path)
    source_keys = set(source_entries)
    total = len(source_keys)
    if not total:
        raise TranslationCatalogError(
            'No source strings were found in {}'.format(pot_path)
        )

    language_results = []
    for locale, name in locales:
        error = ''
        if locale == SOURCE_LOCALE:
            translated = total
        else:
            po_path = os.path.join(
                localedir, locale, 'LC_MESSAGES', 'ospy_messages.po'
            )
            try:
                translated_entries = _catalog_entries(po_path)
                translated = sum(
                    1 for key in source_keys
                    if translated_entries.get(key, {}).get('translated', False)
                )
            except TranslationCatalogError as err:
                translated = 0
                error = str(err)

        missing = total - translated
        percent = round((float(translated) / float(total)) * 100.0, 1)
        status = (
            'ok' if missing == 0 else
            'warning' if percent >= TRANSLATION_WARNING_PERCENT else
            'error'
        )
        language_results.append({
            'locale': locale,
            'name': name,
            'translated': translated,
            'missing': missing,
            'percent': percent,
            'status': status,
            'error': error,
        })

    statuses = [item['status'] for item in language_results]
    overall = (
        'error' if 'error' in statuses else
        'warning' if 'warning' in statuses else 'ok'
    )
    result = {
        'status': overall,
        'total': total,
        'languages': language_results,
        'updated': os.path.getmtime(pot_path),
    }
    with _cache_lock:
        _cache['signature'] = signature
        _cache['data'] = copy.deepcopy(result)
    return result
