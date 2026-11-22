import argparse

import infrai


def schedule_daily_health_check(task_url: str) -> str:
    result = infrai.cron.create(
        {
            "cron_expr": "0 8 * * *",
            "task": task_url,
        }
    )
    data = result.get("data") or {}
    job_id = data.get("job_id", "")
    return str(job_id)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True, help="Public URL to call for the daily health check")
    args = parser.parse_args()
    job_id = schedule_daily_health_check(args.task)
    print({"job_id": job_id, "task": args.task, "cron_expr": "0 8 * * *"})


if __name__ == "__main__":
    main()
