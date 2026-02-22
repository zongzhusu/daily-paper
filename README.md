# Daily Paper

`daily-paper` is the orchestration layer that integrates `news-collector` and `news-scorer` for arXiv daily publishing.

## Daily Schedule

- Timezone: Asia/Shanghai
- Publish SLA: 08:30 daily

## Pipeline

- collect -> score -> curate -> render -> build

## Output

- Daily markdown: `projects/daily-paper/output/YYYY-MM-DD.md`
- Static site: `projects/daily-paper/output/site/`
