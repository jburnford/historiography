#!/usr/bin/env python3
"""Check curated graph references and report editorial coverage gaps."""
import json
from datetime import date
from pathlib import Path
import sys
try:
    from .validate_journal_catalogue import validate_catalogue
except ImportError:
    from validate_journal_catalogue import validate_catalogue

ROOT = Path(__file__).resolve().parents[1]


def validate(graph, pathways):
    errors, warnings = [], []
    if 'journal_catalogue' in graph:
        errors.extend(validate_catalogue(graph['journal_catalogue'], graph['nodes']))
    identifiers = {}
    for name in ("nodes", "edges", "sources", "layers", "periods"):
        rows = graph[name]
        ids = [r["id"] for r in rows]
        identifiers[name] = set(ids)
        if len(ids) != len(set(ids)):
            errors.append(f"Duplicate IDs in {name}")
    used_sources, connected = set(), set()
    for node in graph["nodes"]:
        if node["layer"] not in identifiers["layers"]:
            errors.append(f"Unknown layer in {node['id']}")
        if node["period"] is not None and node["period"] not in identifiers["periods"]:
            errors.append(f"Unknown period in {node['id']}")
        if not node.get("source_ids"):
            warnings.append(f"No supporting sources for {node['id']}")
    pairs = set()
    for edge in graph["edges"]:
        for key in ("source", "target"):
            if edge[key] not in identifiers["nodes"]:
                errors.append(f"Unknown endpoint in {edge['id']}: {edge[key]}")
            connected.add(edge[key])
        triple = (edge["source"], edge["target"], edge["type"])
        if triple in pairs:
            warnings.append(f"Repeated endpoint/type combination in {edge['id']}")
        pairs.add(triple)
        if edge["type"] not in ("connection", "critique"):
            errors.append(f"Unknown edge type in {edge['id']}")
        # Older imports may lack classification. Comparisons never gain arrows.
        if "directed" in edge or "relationship_kind" in edge:
            kind = edge.get("relationship_kind")
            if kind not in ("comparison", "influence", "contribution", "critique"):
                errors.append(f"Unknown relationship kind in {edge['id']}")
            if type(edge.get("directed")) is not bool:
                errors.append(f"Direction must be a boolean in {edge['id']}")
            elif edge["directed"] != (kind != "comparison"):
                errors.append(f"Direction disagrees with relationship kind in {edge['id']}")
            if (kind == "critique") != (edge["type"] == "critique"):
                errors.append(f"Critique metadata disagrees in {edge['id']}")
    for source in graph["sources"]:
        if "citation" in source and (not isinstance(source["citation"], str) or not source["citation"].strip()):
            errors.append(f"Empty or invalid citation in {source['id']}")
        url = source.get("url")
        if url is not None and (not isinstance(url, str) or not url.startswith(("https://", "http://"))):
            errors.append(f"Invalid source URL in {source['id']}")
        verification = source.get("verification")
        if verification is not None:
            if not isinstance(verification, dict):
                errors.append(f"Invalid verification record in {source['id']}")
                continue
            status = verification.get("status")
            if status not in ("not_checked", "bibliographic_metadata_checked", "supporting_page_checked"):
                errors.append(f"Unknown verification status in {source['id']}")
            if not isinstance(verification.get("note"), str) or not verification["note"].strip():
                errors.append(f"Verification needs a scope note in {source['id']}")
            if status in ("bibliographic_metadata_checked", "supporting_page_checked"):
                try:
                    date.fromisoformat(verification.get("checked_on", ""))
                except (TypeError, ValueError):
                    errors.append(f"Verification needs a valid check date in {source['id']}")
    for row in graph["nodes"] + graph["edges"]:
        refs = row.get("source_ids", [])
        used_sources.update(refs)
        for ref in refs:
            if ref not in identifiers["sources"]:
                errors.append(f"Unknown source {ref} in {row['id']}")
    people = graph.get("people", [])
    people_ids = [p.get("id") for p in people]
    if len(people_ids) != len(set(people_ids)):
        errors.append("Duplicate people IDs")
    for person in people:
        if not person.get("id") or not person.get("label"):
            errors.append("Person needs an ID and label")
        if person.get("node_id") and person["node_id"] not in identifiers["nodes"]:
            errors.append(f"Unknown full entry for person {person['id']}")
    for node in graph["nodes"]:
        if graph.get("schema_version") in ("1.3", "1.4") and node.get("entry_kind") not in ("group", "person"):
            errors.append(f"Missing entry kind in {node['id']}")
        if graph.get("schema_version") == "1.4" and not node.get("entry_type"):
            errors.append(f"Missing entry type in {node['id']}")
        strand_ids = set()
        for strand in node.get("strands", []):
            if not all(strand.get(key) for key in ("id", "title", "focus", "works", "person_ids", "source_ids")):
                errors.append(f"Incomplete strand in {node['id']}")
            if strand.get("id") in strand_ids:
                errors.append(f"Duplicate strand in {node['id']}")
            strand_ids.add(strand.get("id"))
            for pid in strand.get("person_ids", []):
                if pid not in people_ids:
                    errors.append(f"Unknown strand person {pid} in {node['id']}")
            for ref in strand.get("source_ids", []):
                used_sources.add(ref)
                if ref not in identifiers["sources"]:
                    errors.append(f"Unknown strand source {ref} in {node['id']}")
        representatives = node.get("representative_people", [])
        if node.get("entry_kind") == "group" and not representatives:
            errors.append(f"Group needs representative people: {node['id']}")
        if node.get("entry_kind") == "person" and representatives:
            errors.append(f"Person entry cannot be a representative group: {node['id']}")
        seen = set()
        for rep in representatives:
            pid = rep.get("person_id")
            if pid not in people_ids:
                errors.append(f"Unknown representative person {pid} in {node['id']}")
            if pid in seen:
                errors.append(f"Duplicate representative person {pid} in {node['id']}")
            seen.add(pid)
            if rep.get("role") not in ("historian", "contributor", "precursor", "critic", "comparison"):
                errors.append(f"Invalid representative role in {node['id']}")
            if not rep.get("context") or rep.get("basis") not in ("curated_entry", "existing_relationship", "source_review", "editorial_comparison"):
                errors.append(f"Representative needs context and basis in {node['id']}")
            if not rep.get("source_ids"):
                errors.append(f"Representative needs references in {node['id']}")
            for ref in rep.get("source_ids", []):
                used_sources.add(ref)
                if ref not in identifiers["sources"]:
                    errors.append(f"Unknown representative source {ref} in {node['id']}")
            if rep.get("edge_id"):
                edge = next((e for e in graph["edges"] if e["id"] == rep["edge_id"]), None)
                person = next((p for p in people if p["id"] == pid), {})
                if not edge or set((edge["source"], edge["target"])) != set((node["id"], person.get("node_id"))):
                    errors.append(f"Representative edge does not connect person and group in {node['id']}")
    for ref in sorted(identifiers["sources"] - used_sources):
        warnings.append(f"Unused source: {ref}")
    for node_id in sorted(identifiers["nodes"] - connected):
        warnings.append(f"Unconnected node: {node_id}")
    pathway_ids = [p["id"] for p in pathways["pathways"]]
    if len(pathway_ids) != len(set(pathway_ids)):
        errors.append("Duplicate pathway IDs")
    for pathway in pathways["pathways"]:
        for node_id in pathway["node_ids"]:
            if node_id not in identifiers["nodes"]:
                errors.append(f"Unknown node {node_id} in pathway {pathway['id']}")
    return errors, warnings


if __name__ == "__main__":
    graph = json.loads((ROOT / "historiography-1920-2000.json").read_text())
    pathways = json.loads((ROOT / "seminar-pathways.json").read_text())
    errors, warnings = validate(graph, pathways)
    for message in errors:
        print("ERROR:", message)
    for message in warnings:
        print("WARNING:", message)
    print(f"{len(graph['nodes'])} nodes, {len(graph['edges'])} edges, {len(graph['sources'])} sources, {len(pathways['pathways'])} pathways.")
    if graph.get("people"):
        print(f"{len(graph['people'])} people; {sum(n.get('entry_kind') == 'group' for n in graph['nodes'])} groups with representative rosters.")
    print(f"{len(errors)} structural errors; {len(warnings)} structural warnings.")
    if graph.get('journal_catalogue'):
        catalogue = graph['journal_catalogue']
        print(f"Journal extension: {sum(n['entry_kind']=='periodical' for n in catalogue['nodes'])} candidate periodicals; {len(catalogue['edges'])} specific venue edges; {len(catalogue['subject_classifications'])} subject classifications (not visual edges).")
    sourced_edges = sum(bool(e.get("source_ids")) for e in graph["edges"])
    print(f"Relationship bibliography: {sourced_edges}/{len(graph['edges'])} have explicit source references. Structural validation does not verify historical claims.")
    comparisons = sum(e.get("relationship_kind") == "comparison" for e in graph["edges"])
    classified = sum("relationship_kind" in e for e in graph["edges"])
    print(f"Relationship classification: {classified}/{len(graph['edges'])}; {comparisons} explicit undirected comparisons.")
    sys.exit(bool(errors))
