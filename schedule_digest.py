"""Register the weekly webhook with Infrai cron."""

import argparse

from infrai_client import InfraiClient


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_url", help="Public URL for /jobs/weekly-digest")
    parser.add_argument("--cron", default="0 9 * * 1", dest="cron_expr")
    args = parser.parse_args()

    job_id = InfraiClient().create_cron(args.cron_expr, args.task_url)
    print(f"scheduled weekly digest: {job_id}")


if __name__ == "__main__":
    main()
