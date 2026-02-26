#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

const CONFIG = {
  outputDir: path.resolve(__dirname, "..", "output"),
  siteDir: path.resolve(__dirname, "..", "output", "site"),
  templatesDir: path.resolve(__dirname, "templates"),
};

function parseMode(argv) {
  const idx = argv.indexOf("--mode");
  if (idx === -1) {
    return "paper";
  }

  const mode = argv[idx + 1];
  return mode === "news" ? "news" : "paper";
}

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function escapeHtml(input) {
  return String(input)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderSummary(markdownText) {
  if (!markdownText) {
    return "";
  }

  // We only support a tiny subset of Markdown for safety:
  // - **bold**
  // - newline -> <br/>
  const escaped = escapeHtml(markdownText);
  const bolded = escaped.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  return bolded.replace(/\n/g, "<br/>");
}

function brandForMode(mode) {
  if (mode === "news") {
    return {
      brand: "Daily News",
      brandZh: "每日资讯",
      archiveLabel: "资讯归档",
      itemLabel: "条资讯",
    };
  }

  return {
    brand: "Daily Paper",
    brandZh: "每日论文",
    archiveLabel: "论文归档",
    itemLabel: "篇论文",
  };
}

function readTemplate(name) {
  const templatePath = path.join(CONFIG.templatesDir, name);
  return fs.readFileSync(templatePath, "utf-8");
}

function renderTemplate(name, data) {
  let html = readTemplate(name);
  for (const [key, value] of Object.entries(data)) {
    html = html.split(`{{${key}}}`).join(String(value));
  }
  return html;
}

function listReportFiles() {
  if (!fs.existsSync(CONFIG.outputDir)) {
    return [];
  }

  return fs
    .readdirSync(CONFIG.outputDir)
    .filter((file) => /^\d{4}-\d{2}-\d{2}\.json$/.test(file))
    .sort((a, b) => b.localeCompare(a));
}

function pickItems(payload) {
  if (Array.isArray(payload)) {
    return payload;
  }
  if (payload && Array.isArray(payload.items)) {
    return payload.items;
  }
  if (payload && payload.data && Array.isArray(payload.data.items)) {
    return payload.data.items;
  }
  return [];
}

function extractArxivId(value) {
  if (!value || typeof value !== "string") {
    return "";
  }

  const cleaned = value.trim();
  if (!cleaned) {
    return "";
  }

  const direct = cleaned.match(/^(?:arxiv:)?(\d{4}\.\d{4,5}(?:v\d+)?)$/i);
  if (direct) {
    return direct[1];
  }

  const urlHit = cleaned.match(/arxiv\.org\/(?:abs|pdf)\/(\d{4}\.\d{4,5}(?:v\d+)?)/i);
  if (urlHit) {
    return urlHit[1];
  }

  return "";
}

function normalizeItem(item) {
  const fallbackId =
    extractArxivId(item.arxiv_id) ||
    extractArxivId(item.id) ||
    extractArxivId(item.url) ||
    extractArxivId(item.abs_url) ||
    extractArxivId(item.pdf_url);

  const absUrl =
    item.abs_url ||
    item.absUrl ||
    (fallbackId ? `https://arxiv.org/abs/${fallbackId}` : "");

  const pdfUrl =
    item.pdf_url ||
    item.pdfUrl ||
    (fallbackId ? `https://arxiv.org/pdf/${fallbackId}.pdf` : "");

  return {
    title: item.title || "Untitled",
    topic: item.topic || "未分类",
    score:
      item.final_score ??
      item.second_score ??
      item.first_score ??
      item.score ??
      "-",
    summary:
      item.translated_zh ||
      item.summary_zh ||
      item.abstract_zh ||
      item.reasoning ||
      "",
    absUrl,
    pdfUrl,
  };
}

function loadReports() {
  return listReportFiles().map((file) => {
    const filePath = path.join(CONFIG.outputDir, file);
    const raw = JSON.parse(fs.readFileSync(filePath, "utf-8"));
    const dateFromFile = file.replace(".json", "");
    const date = raw.date || dateFromFile;
    const items = pickItems(raw).map(normalizeItem);
    return { date, items, filename: `${date}.html` };
  });
}

function renderRecentReports(reports, currentDate) {
  return reports
    .map((report) => {
      const active = report.date === currentDate;
      if (active) {
        return `<li><span class="block px-3 py-2 rounded-lg bg-indigo-50 text-indigo-700 font-medium">${report.date}</span></li>`;
      }
      return `<li><a class="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-100" href="${report.filename}">${report.date}</a></li>`;
    })
    .join("\n");
}

function renderItems(items) {
  if (items.length === 0) {
    return '<div class="rounded-lg border border-dashed border-gray-300 p-6 text-sm text-gray-500">No items for this date.</div>';
  }

  return items
    .map((item, index) => {
      const abs = item.absUrl
        ? `<a href="${item.absUrl}" target="_blank" rel="noopener noreferrer" class="text-indigo-600 hover:text-indigo-800">abs</a>`
        : "";
      const pdf = item.pdfUrl
        ? `<a href="${item.pdfUrl}" target="_blank" rel="noopener noreferrer" class="text-indigo-600 hover:text-indigo-800">pdf</a>`
        : "";
      const links = [abs, pdf].filter(Boolean).join(" | ");

      return `
        <article class="border border-gray-200 rounded-xl p-4 bg-white">
          <h2 class="text-lg font-semibold text-gray-900">${index + 1}. ${item.title}</h2>
          <p class="text-sm text-gray-500 mt-1">主题: ${item.topic} | 评分: ${item.score}</p>
          <div class="text-sm text-gray-700 mt-3 leading-6">${renderSummary(item.summary)}</div>
          <p class="text-sm mt-3">${links}</p>
        </article>
      `;
    })
    .join("\n");
}

function buildPage({ report, reports, brandInfo, isIndex = false }) {
  const sidebar = renderTemplate("sidebar.html", {
    brand: brandInfo.brand,
    brand_zh: brandInfo.brandZh,
    recent_reports: renderRecentReports(reports, report.date),
  });

  const content = renderTemplate("homepage.html", {
    date: report.date,
    item_count: report.items.length,
    item_label: brandInfo.itemLabel,
    latest_badge: isIndex ? '<span class="text-xs px-2 py-1 rounded-full bg-green-100 text-green-700">latest</span>' : "",
    report_content: renderItems(report.items),
  });

  const html = renderTemplate("base.html", {
    title: `${brandInfo.brand} - ${report.date}`,
    sidebar,
    content,
    toc_content: '<p class="text-xs text-gray-400">N/A</p>',
  });

  const outputName = isIndex ? "index.html" : `${report.date}.html`;
  fs.writeFileSync(path.join(CONFIG.siteDir, outputName), html);
}

function buildArchive(reports, brandInfo) {
  const sidebar = renderTemplate("sidebar.html", {
    brand: brandInfo.brand,
    brand_zh: brandInfo.brandZh,
    recent_reports: renderRecentReports(reports, null),
  });

  const monthMap = new Map();
  reports.forEach((report) => {
    const month = report.date.slice(0, 7);
    if (!monthMap.has(month)) {
      monthMap.set(month, []);
    }
    monthMap.get(month).push(report);
  });

  const archiveList = Array.from(monthMap.entries())
    .map(([month, monthReports]) => {
      const [year, m] = month.split("-");
      const rows = monthReports
        .map(
          (report) =>
            `<li><a class="flex items-center justify-between px-4 py-3 hover:bg-gray-50" href="${report.filename}"><span>${report.date}</span><span class="text-xs text-gray-400">${report.items.length}${brandInfo.itemLabel}</span></a></li>`,
        )
        .join("\n");

      return `
        <section class="mb-6">
          <h2 class="px-4 py-2 text-sm font-semibold text-gray-500 bg-gray-50">${year}年${m}月</h2>
          <ul class="divide-y divide-gray-100">${rows}</ul>
        </section>
      `;
    })
    .join("\n");

  const content = renderTemplate("archive.html", {
    archive_label: brandInfo.archiveLabel,
    archive_desc: `共 ${monthMap.size} 个月，${reports.length} 期`,
    archive_list: archiveList,
  });

  const html = renderTemplate("base.html", {
    title: `${brandInfo.brand} - Archive`,
    sidebar,
    content,
    toc_content: '<p class="text-xs text-gray-400">Archive</p>',
  });

  fs.writeFileSync(path.join(CONFIG.siteDir, "archive.html"), html);
}

function buildEmptyIndex(brandInfo) {
  const sidebar = renderTemplate("sidebar.html", {
    brand: brandInfo.brand,
    brand_zh: brandInfo.brandZh,
    recent_reports: "",
  });

  const content = renderTemplate("homepage.html", {
    date: "No data",
    item_count: 0,
    item_label: brandInfo.itemLabel,
    latest_badge: "",
    report_content:
      '<div class="rounded-lg border border-dashed border-gray-300 p-6 text-sm text-gray-500">No JSON report found in output/.</div>',
  });

  const html = renderTemplate("base.html", {
    title: brandInfo.brand,
    sidebar,
    content,
    toc_content: '<p class="text-xs text-gray-400">N/A</p>',
  });

  fs.writeFileSync(path.join(CONFIG.siteDir, "index.html"), html);
}

function main() {
  const mode = parseMode(process.argv.slice(2));
  const brandInfo = brandForMode(mode);

  ensureDir(CONFIG.siteDir);
  const reports = loadReports();

  if (reports.length === 0) {
    buildEmptyIndex(brandInfo);
    console.log(`Generated site at ${CONFIG.siteDir}`);
    return;
  }

  buildPage({ report: reports[0], reports, brandInfo, isIndex: true });
  reports.forEach((report) => buildPage({ report, reports, brandInfo, isIndex: false }));
  buildArchive(reports, brandInfo);
  console.log(`Generated site at ${CONFIG.siteDir}`);
}

main();
