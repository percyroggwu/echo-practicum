"""Mechanical excerpt selection and version-bound reuse of agent-authored content."""

from copy import deepcopy
import hashlib
import json
import re

from .validation import ValidationError
from .grounding import NARRATIVE_LIMIT


def identity(prefix, value):
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return prefix + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def fragments(text, source_id, limit=400):
    """Expose literal source slices; segmentation never labels or interprets them."""
    if not isinstance(text, str) or not text.strip():
        return {}
    spans = [(0, len(text))] if len(text) <= limit else []
    start = 0
    boundaries = [match.end() for match in re.finditer(r"[.!?](?=\s|$)|\n", text)] + [len(text)]
    for end in boundaries:
        while end - start > limit:
            cut = text.rfind(" ", start + 1, start + limit + 1)
            cut = cut if cut > start else start + limit
            spans.append((start, cut))
            start = cut
        if end > start:
            spans.append((start, end))
        start = end
    found = {}
    for start, end in spans:
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        if end > start:
            key = identity("EX_", [source_id, text, start, end])
            found[key] = {"source_id": source_id, "start": start, "end": end,
                          "text": text[start:end]}
    return found


def excerpt_catalog(evidence):
    result = {}
    for source in evidence:
        text = source.get("response_text", source.get("text"))
        if source.get("citation_id") and isinstance(text, str):
            result.update(fragments(text, source["citation_id"]))
    return result


def extract(reference, catalog, allowed=None, field="quote_ref"):
    if reference is None:
        return None
    if not isinstance(reference, str) or reference not in catalog:
        raise ValidationError("excerpt_reference", field, "Select an existing excerpt reference; never reproduce quote text.")
    item = catalog[reference]
    if allowed is not None and item["source_id"] not in allowed:
        raise ValidationError("excerpt_source", field, "Select an excerpt from this item's cited sources only.")
    return item["text"]


def correction_tool(tool, question, existing_ids=()):
    """Keep the canonical stored review contract; change only live reference delivery."""
    tool = deepcopy(tool)
    schema = tool["parameters"]["properties"].get("corrections", {}).get("items", {})
    properties = schema.get("properties", {})
    if "request_excerpt" in properties:
        old = properties.pop("request_excerpt")
        nullable = isinstance(old.get("type"), list) and "null" in old["type"]
        choices = list(fragments(question, "original_question"))
        properties["request_ref"] = {"type": ["string", "null"] if nullable else "string",
                                      "enum": choices + ([None] if nullable else [])}
        schema["required"] = ["request_ref" if key == "request_excerpt" else key
                              for key in schema.get("required", [])]
        if 'kind' in properties:
            properties['related_correction_id'] = {'type': ['string', 'null'], 'enum': [*existing_ids, None],
                'description': 'An existing correction ID when refining the same issue, otherwise null. Never create an ID.'}
            schema['required'].append('related_correction_id')
    return tool


def resolve_corrections(report, question, links=None, existing_ids=()):
    report = deepcopy(report)
    if not isinstance(report, dict):
        return report
    catalog = fragments(question, "original_question")
    for index, correction in enumerate(report.get("corrections", [])):
        if not isinstance(correction, dict):
            continue
        if "request_ref" not in correction or "request_excerpt" in correction:
            raise ValidationError("correction_reference", "corrections.request_ref",
                                  "Select request_ref from the supplied original-question excerpts, or null when allowed.",
                                  item_index=index)
        correction["request_excerpt"] = extract(correction.pop("request_ref"), catalog,
                                                field="corrections.request_ref")
        related = correction.pop('related_correction_id', None)
        if related is not None:
            if related not in existing_ids or links is None:
                raise ValidationError('correction_identity', 'corrections.related_correction_id', 'Select an active correction ID or null.')
            if related in links.values():
                raise ValidationError('correction_duplicate', 'corrections.related_correction_id', 'Refine an existing correction only once.')
            links[index] = related
    return report


def block_catalog(payload, evidence, scope, facts=None):
    sources = {item["citation_id"]: item for item in evidence}
    result = {}
    for kind in ("fact_ids", "interpretations", "proposals"):
        for value in payload.get(kind, []):
            refs = ((facts or {}).get(value, {}).get("citation_ids", list(sources))
                    if kind == "fact_ids" else value["citation_ids"])
            binding = {"scope": scope, "sources": {key: sources[key] for key in refs}}
            key = identity("BLOCK_", [kind, value, binding])
            result[key] = {"kind": kind, "value": deepcopy(value), "source_ids": list(refs),
                           "binding": identity("SRC_", binding)}
    return result


def public_blocks(blocks):
    return [{"block_id": key, "kind": block["kind"], "content": block["value"]}
            for key, block in blocks.items()]


def draft_text_catalog(text):
    result = {}
    for paragraph in re.split(r'\n\s*\n', text):
        if paragraph.strip():
            for item in fragments(paragraph, 'unverified_agent_draft', 600).values():
                result[identity('DRAFT_', item['text'])] = item['text']
    return result


def draft_capacity(blocks):
    """Informational capacity; same-call removals/reuse are resolved before enforcing it."""
    return {kind: {'retained_count': sum(block['kind'] == kind for block in blocks.values()),
                   'limit': NARRATIVE_LIMIT,
                   'remaining_slots': max(0, NARRATIVE_LIMIT - sum(block['kind'] == kind for block in blocks.values()))}
            for kind in ('interpretations', 'proposals')}


def resolve_answer(submitted, evidence, scope, available, previous, draft_texts=None):
    """Resolve IDs and edits to the existing replayable source-facts-v4 payload."""
    if not isinstance(submitted, dict):
        raise ValidationError("answer_fields", "answer", "Return the declared structured answer.")
    expected = {"fact_ids", "interpretations", "proposals", "reuse_ids", "remove_ids"}
    if set(submitted) != expected:
        raise ValidationError("answer_fields", "answer", "Use fact_ids, interpretations, proposals, reuse_ids and remove_ids only.")
    sources = {item["citation_id"]: item for item in evidence}
    reuse, remove = submitted["reuse_ids"], submitted["remove_ids"]
    if not isinstance(reuse, list) or not isinstance(remove, list) or len(reuse) > 32 or len(remove) > 32:
        raise ValidationError("answer_edits", "reuse_ids", "Use bounded lists of existing block IDs.")
    if any(not isinstance(key, str) or key not in available for key in reuse):
        raise ValidationError("answer_block_reference", "reuse_ids", "Reuse only the supplied existing block IDs.")
    if any(not isinstance(key, str) or key not in previous for key in remove):
        raise ValidationError("answer_block_removal", "remove_ids", "Remove only blocks belonging to the current saved draft.")
    # A changed source packet invalidates reuse, rather than granting old judgments to new evidence.
    selected = {key: value for key, value in previous.items() if key not in remove}
    selected.update({key: available[key] for key in reuse})
    if any(any(key not in sources for key in block["source_ids"]) or block["binding"] != identity("SRC_",
           {"scope": scope, "sources": {key: sources[key] for key in block["source_ids"]}})
           for block in selected.values()):
        raise ValidationError("answer_block_binding", "reuse_ids", "Retained content belongs to different sources or scope; submit an explicit revised block.")
    result = {kind: [] for kind in ("fact_ids", "interpretations", "proposals")}
    for block in selected.values():
        result[block["kind"]].append(deepcopy(block["value"]))
    catalog = excerpt_catalog(evidence)
    for kind in result:
        values = submitted[kind]
        if not isinstance(values, list):
            raise ValidationError("answer_items", kind, "Return a list of explicit additions.")
        for item in values:
            if kind != "fact_ids":
                if not isinstance(item, dict) or set(item) != {"text", "citation_ids", "quote_ref"}:
                    raise ValidationError("narrative_fields", kind, "Use text, citation_ids and quote_ref; Python extracts the quote.")
                if isinstance(item['text'], dict):
                    reference = item['text'].get('draft_text_ref')
                    if set(item['text']) != {'draft_text_ref'} or not isinstance(reference, str) or reference not in (draft_texts or {}):
                        raise ValidationError('draft_text_reference', kind + '.text', 'Select an existing unverified draft text ID, or write your explicit revised text.')
                    item = {**item, 'text': draft_texts[reference]}
                item = {**item, "quote": extract(item["quote_ref"], catalog, item["citation_ids"])}
                del item["quote_ref"]
            if item not in result[kind]:
                result[kind].append(deepcopy(item))
    for kind in ('interpretations', 'proposals'):
        if len(result[kind]) > NARRATIVE_LIMIT:
            base = [key for key, block in selected.items() if block['kind'] == kind]
            retained = [key for key in base if key in previous and key not in remove]
            raise ValidationError('narrative_count', kind, 'The resolved narrative list exceeds its item limit.',
                expected_count=NARRATIVE_LIMIT, actual_count=len(result[kind]),
                retained_count=len(retained), reused_count=len(base) - len(retained),
                submitted_count=len(submitted[kind]), new_count=len(result[kind]) - len(base),
                merged_count=len(result[kind]), excess=len(result[kind]) - NARRATIVE_LIMIT,
                remaining_slots=max(0, NARRATIVE_LIMIT - len(base)),
                removable_block_ids=[key for key in base if key in previous],
                reused_block_ids=[key for key in base if key in reuse])
    return result


def live_answer_schema(schema, excerpts=(), available=(), previous=(), draft_texts=()):
    schema = deepcopy(schema)
    for name in ("interpretations", "proposals"):
        # The canonical schema shares a template; detach each branch before editing it.
        schema[name] = deepcopy(schema[name])
        schema[name]['description'] = ('Explicit additions, not a replacement list. Retained and reused blocks plus '
            'unique additions must fit the final item limit. Remove a saved block with remove_ids when replacing it; '
            'omit it from reuse_ids too. Same-call removals free capacity.')
        item = schema[name]["items"]
        item["properties"].pop("quote")
        item["properties"]["quote_ref"] = {"type": ["string", "null"],
            "enum": [*excerpts, None],
            "description": "An EX_ reference from the excerpt catalog, or null. Never write quote text."}
        item["required"] = ["text", "citation_ids", "quote_ref"]
        if draft_texts:
            item['properties']['text'] = {'anyOf': [item['properties']['text'], {
                'type': 'object', 'properties': {'draft_text_ref': {'type': 'string', 'enum': list(draft_texts)}},
                'required': ['draft_text_ref'], 'additionalProperties': False}]}
    for name in ("reuse_ids", "remove_ids"):
        schema[name] = {"type": "array", "maxItems": 32, "items": {"type": "string"}}
        choices = list(available if name == 'reuse_ids' else previous)
        if choices:
            schema[name]['items']['enum'] = choices
        else:
            schema[name]['maxItems'] = 0
    return schema
