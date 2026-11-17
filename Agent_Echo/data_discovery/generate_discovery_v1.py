"""Build the discovery_v1 pack (plan v10 §5). Run from Agent_Echo: python -m data_discovery.generate_discovery_v1

Order matters: background operations, then HR (which links to team goals), then the hand-built
stories, then the automatic plants, which read the final pulse scores to place their slots.
"""
from . import common, hr, ops, plants, stories


def main():
    ctx = common.load_context()
    ops.generate(ctx)
    hr.generate(ctx)
    stories.apply(ctx)
    plants.apply(ctx)
    common.write_pack(ctx)
    common.write_answer_key(ctx)
    print({table: len(rows) for table, rows in sorted(ctx.tables.items())})


if __name__ == "__main__":
    main()
