"use strict";

const THEME_KEYWORDS = {
  "稳定性与故障": [
    "闪退", "崩溃", "卡死", "卡顿", "打不开", "无法登录", "登录不了",
    "加载失败", "同步失败", "丢数据", "丢失", "报错", "无响应", "白屏",
    "黑屏", "加载慢", "很慢", "慢很多", "延迟", "断线", "转圈", "进度丢",
    "重新加载", "打开速度", "传不上去", "页面没有更新", "没有更新",
    "支付成功", "订单页面", "内容也没了", "同步一直失败", "失败", "空文档",
    "没有同步上去", "丢了很多", "bug", "故障", "不稳定",
  ],
  "使用体验": [
    "难用", "不会用", "找不到", "看不懂", "步骤", "操作", "界面", "入口",
    "广告", "通知", "搜索", "排版", "复杂", "交互", "新手", "体验",
    "按钮", "页面", "更新后", "不方便", "字太小", "看不清", "没有引导",
    "新手引导", "不知道应该先做什么", "像迷宫", "手势操作", "挡住内容",
  ],
  "功能需求": [
    "希望增加", "能不能加", "建议增加", "缺少", "导出", "批量", "自动",
    "模板", "统计", "分类", "筛选", "自定义", "功能", "电脑版", "深色模式",
    "插件", "平板", "横屏", "手机布局", "适配", "扫描", "提醒时间", "共享",
    "search", "could",
  ],
  "价格与订阅": [
    "价格", "收费", "太贵", "会员", "订阅", "续费", "退款", "扣费",
    "自动续费", "免费", "优惠", "套餐", "付费", "性价比", "涨价", "年费",
    "原价扣", "试用期", "优惠券", "买错", "贵一倍", "免费额度", "取消会员",
  ],
  "内容与效果": [
    "推荐不准", "内容质量", "质量差", "内容", "模板", "结果", "不准",
    "没有效果", "效果", "答案", "生成", "错别字", "文案", "数据不对",
    "帮助不大", "很实用", "有用", "偏题", "关键决定", "没提到", "没有理解",
    "理解我的需求", "翻译", "专业术语", "结果差异", "太空洞", "全部重写",
    "实用", "清晰", "质量不错",
  ],
  "客户服务": [
    "客服", "人工", "售后", "回复慢", "没人回", "态度", "服务", "电话打不通",
    "反馈没人管", "工单", "沟通", "回复很慢", "没人处理", "在线咨询", "排队",
    "被直接断开", "回访", "处理问题", "反馈渠道", "联系你们", "答非所问",
  ],
  "隐私与安全": [
    "隐私", "权限", "泄露", "安全", "数据", "授权", "个人信息", "验证码",
    "账号被盗", "异地登录", "注销", "隐私政策", "共享给", "合作方",
    "删除账号", "历史数据", "清除",
  ],
};

const POSITIVE_WORDS = [
  "好用", "喜欢", "满意", "方便", "流畅", "清晰", "高效", "省心", "实用",
  "不错", "推荐", "惊喜", "稳定", "快",
];
const NEGATIVE_WORDS = [
  "难用", "失望", "生气", "恶心", "太差", "很差", "崩溃", "闪退", "卡顿",
  "失败", "不准", "太贵", "慢", "复杂", "找不到", "没人回", "扣费", "骗",
  "不稳定", "不好", "麻烦", "鸡肋", "退款",
];
const URGENT_WORDS = [
  "崩溃", "闪退", "丢数据", "泄露", "被盗", "扣费", "无法登录", "打不开",
  "支付失败", "报警", "投诉", "退款", "严重", "紧急",
];

const THEME_ACTIONS = {
  "稳定性与故障": "按设备、版本和操作路径抽样复现；先建立故障清单与临时兜底方案。",
  "使用体验": "找到用户卡住的具体页面，做一次可用性走查并验证文案或入口调整。",
  "功能需求": "先访谈提出需求的用户，确认使用场景和频率，再评估投入产出。",
  "价格与订阅": "复核订阅告知、续费规则与退款路径，优先减少误解型投诉。",
  "内容与效果": "补充正反例与预期说明，抽样评估结果质量并建立人工验收标准。",
  "客户服务": "检查响应时效和转人工路径，抽取未解决对话复盘。",
  "隐私与安全": "升级为高优先级核查，确认授权范围、数据流向和账号安全记录。",
  "其他": "继续积累同类反馈，并人工标注具体问题后再决定是否立项。",
};

const DEMO_RECORDS = [
  ["D001", "今天上午开始云同步一直失败，换了 Wi-Fi 和流量都不行，工作被打断了。", "应用商店评论", 1],
  ["D002", "笔记超过五百条以后打开文档会闪退，iPhone 15 也一样，不敢继续用了。", "客服工单", 1],
  ["D003", "更新后一直卡在登录页面转圈，卸载重装还是登录不了。", "微信群", 1],
  ["D004", "昨晚的会议记录没有同步上去，今天打开只剩一个空文档，太吓人了。", "客服工单", 1],
  ["D005", "全局搜索输入关键词以后要等十几秒，加载慢得离谱。", "应用商店评论", 2],
  ["D006", "离线编辑内容在恢复网络后被旧版本覆盖了，丢了很多内容，希望尽快处理。", "客服工单", 1],
  ["D007", "开关同步的入口藏得太深，我找了三层菜单才找到，操作很不方便。", "问卷", 3],
  ["D008", "更新之后工具栏位置全变了，常用的按钮找不到，学习成本太高。", "应用商店评论", 2],
  ["D009", "新手引导太简单了，我到现在都不知道怎么把笔记导出成模板。", "问卷", 3],
  ["D010", "页面挺好看，但是创建模板的步骤太多，每次都要点很多按钮。", "客服工单", 3],
  ["D011", "搜索筛选的条件看不懂，标签和文件夹混在一起，体验很乱。", "应用商店评论", 2],
  ["D012", "网页版登录以后侧边栏会挡住内容，页面排版有点复杂。", "问卷", 3],
  ["D013", "希望增加批量导出和批量分类功能，整理一百多篇笔记太费时间了。", "微信群", 4],
  ["D014", "能不能加一个自动生成思维导图的功能，复习的时候会很方便。", "问卷", 5],
  ["D015", "建议支持日历同步，把待办直接显示在系统日历里。", "应用商店评论", 4],
  ["D016", "希望可以自定义标签颜色，现在标签多了很难分类。", "微信群", 4],
  ["D017", "功能整体不错，但没有电脑版离线客户端，出差时很不方便。", "问卷调查", 3],
  ["D018", "希望增加深色模式，晚上整理笔记有点刺眼。", "应用商店评论", 4],
  ["D019", "缺少完整备份功能，想每周自动备份一次到本地。", "客服工单", 4],
  ["D020", "会员到期前没有任何提醒，今天突然自动续费扣费了，希望退款。", "客服工单", 1],
  ["D021", "专业版价格太贵了，我只是偶尔用模板，性价比不高。", "应用商店评论", 2],
  ["D022", "学生认证已经通过，但是优惠套餐一直显示原价，收费规则没看懂。", "客服工单", 2],
  ["D023", "申请退款三天了还没到账，自动续费的提示也不明显。", "微信群", 1],
  ["D024", "免费版够用了，付费功能没有让我觉得有明显效果，暂时不续费。", "问卷", 3],
  ["D025", "会议纪要模板非常实用，帮我省了不少整理时间。", "应用商店评论", 5],
  ["D026", "AI 摘要经常把行动项写错，生成结果看起来通顺但内容不准。", "客服工单", 2],
  ["D027", "每周回顾模板生成的文案很空，像套话，帮助不大。", "问卷", 2],
  ["D028", "读书笔记模板质量不错，结构清晰，也很容易修改。", "应用商店评论", 5],
  ["D029", "导出后的编号全乱了，生成的内容有错别字，还需要手动排版。", "客服工单", 2],
  ["D030", "客服两天都没人回复，工单提交后也看不到处理进度。", "客服工单", 1],
  ["D031", "人工客服态度很好，远程帮我解决了模板配置问题，很满意。", "问卷", 5],
  ["D032", "反馈没人管，电话打不通，在线客服只会让我重启。", "微信群", 1],
  ["D033", "首次打开就要求通讯录权限，我觉得没有必要，也不太安全。", "应用商店评论", 2],
  ["D034", "今天收到异地登录提醒，但我没有在其他设备登录，账号是不是被盗了？", "客服工单", 1],
  ["D035", "想注销账号，但找不到删除个人信息的入口，隐私说明也写得很模糊。", "问卷", 2],
  ["D036", "希望适配安卓平板，横屏以后页面还是手机布局，使用起来很难受。", "应用商店评论", 3],
].map(([id, text, source, rating]) => ({ id, text, source, rating, createdAt: null }));

const STATUS_LABELS = {
  pending: "待审核",
  approved: "已通过",
  needs_revision: "需修订",
};

const state = {
  source: "demo",
  records: DEMO_RECORDS,
  uploadedRecords: [],
  pastedRecords: [],
  currentRun: null,
  history: [],
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normalizeText(value) {
  return String(value ?? "").trim().toLocaleLowerCase("zh-CN");
}

function hits(text, words) {
  const lowered = normalizeText(text);
  return words.filter((word) => lowered.includes(normalizeText(word)));
}

function cleanText(value) {
  let text = String(value ?? "")
    .replaceAll("&nbsp;", " ")
    .replaceAll("&amp;", "&")
    .replaceAll("&lt;", "<")
    .replaceAll("&gt;", ">")
    .replaceAll('&quot;', '"')
    .replaceAll("&#039;", "'")
    .replace(/<[^>]+>/g, " ");
  text = text.replace(/(?<!\d)1[3-9]\d{9}(?!\d)/g, "[手机号已隐藏]");
  text = text.replace(/\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b/g, "[邮箱已隐藏]");
  text = text.replace(/(?<!\d)\d{17}[\dXx](?!\d)/g, "[证件号已隐藏]");
  return text.replace(/\s+/g, " ").trim().slice(0, 2000);
}

function parseRating(value) {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) && number >= 1 && number <= 5 ? number : null;
}

function cleanRecords(records) {
  const cleaned = [];
  const seen = new Set();
  let dropped = 0;
  records.forEach((record, index) => {
    const text = cleanText(record.text);
    const dedupeKey = normalizeText(text);
    if (!text || seen.has(dedupeKey)) {
      dropped += 1;
      return;
    }
    seen.add(dedupeKey);
    cleaned.push({
      ...record,
      id: String(record.id || `F${String(index + 1).padStart(3, "0")}`).trim(),
      text,
      source: cleanText(record.source) || "未知渠道",
      rating: parseRating(record.rating),
    });
  });
  return { cleaned, dropped };
}

function classifyTheme(text) {
  const scores = {};
  Object.entries(THEME_KEYWORDS).forEach(([theme, words]) => {
    scores[theme] = hits(text, words).reduce(
      (total, word) => total + (word.length >= 3 ? 2 : 1),
      0,
    );
  });
  if (/希望|能否|能不能|可不可以|如果.*(?:就|会).*|期待|建议|想要|wish i could/i.test(text)) {
    scores["功能需求"] += 1;
  }
  const orderedThemes = Object.keys(scores).sort((a, b) => scores[b] - scores[a]);
  const bestTheme = orderedThemes[0];
  const bestScore = scores[bestTheme];
  if (!bestScore) return { theme: "其他", confidence: 0.35 };
  const orderedScores = Object.values(scores).sort((a, b) => b - a);
  const margin = bestScore - (orderedScores[1] || 0);
  return {
    theme: bestTheme,
    confidence: Math.round(Math.min(0.95, 0.55 + bestScore * 0.04 + margin * 0.05) * 100) / 100,
  };
}

function classifySentiment(record) {
  let positive = hits(record.text, POSITIVE_WORDS).length;
  let negative = hits(record.text, NEGATIVE_WORDS).length;
  if (record.rating !== null) {
    if (record.rating <= 2) negative += 2;
    if (record.rating >= 4) positive += 2;
  }
  if (negative > positive) return "负面";
  if (positive > negative) return "正面";
  return /[?？]|建议|希望|能不能/.test(record.text) ? "中性/建议" : "中性";
}

function classifySeverity(record, theme) {
  if (hits(record.text, URGENT_WORDS).length || (record.rating !== null && record.rating <= 1)) {
    return "high";
  }
  if (["稳定性与故障", "隐私与安全", "价格与订阅"].includes(theme)) return "medium";
  if (record.rating !== null && record.rating <= 2) return "medium";
  return "low";
}

function priorityScore(themeRecords, total, sentiments, severities) {
  const frequency = (themeRecords.length / Math.max(total, 1)) * 40;
  const negativeRatio = sentiments.filter((value) => value === "负面").length / Math.max(sentiments.length, 1);
  const severityRatio = severities.filter((value) => value === "high").length / Math.max(severities.length, 1);
  const ratings = themeRecords.map((record) => record.rating).filter((value) => value !== null);
  const lowRatingRatio = ratings.length
    ? ratings.filter((rating) => rating <= 2).length / ratings.length
    : 0;
  return Math.round(
    Math.min(100, frequency + negativeRatio * 30 + severityRatio * 20 + lowRatingRatio * 10) * 10,
  ) / 10;
}

function buildInsights(records) {
  const labels = new Map();
  records.forEach((record) => {
    const { theme, confidence } = classifyTheme(record.text);
    labels.set(record.id, {
      theme,
      confidence,
      sentiment: classifySentiment(record),
      severity: classifySeverity(record, theme),
    });
  });

  const buckets = new Map();
  records.forEach((record) => {
    const label = labels.get(record.id);
    if (!buckets.has(label.theme)) buckets.set(label.theme, []);
    buckets.get(label.theme).push(record);
  });

  return Array.from(buckets.entries()).map(([theme, themeRecords]) => {
    const themeLabels = themeRecords.map((record) => labels.get(record.id));
    const sentiments = themeLabels.map((label) => label.sentiment);
    const severities = themeLabels.map((label) => label.severity);
    const sentimentCounts = countValues(sentiments);
    const sentiment = Object.entries(sentimentCounts).sort((a, b) => b[1] - a[1])[0][0];
    const severity = severities.includes("high")
      ? "high"
      : severities.includes("medium")
        ? "medium"
        : "low";
    const allHits = themeRecords.flatMap((record) => hits(record.text, THEME_KEYWORDS[theme] || []));
    const wordCounts = countValues(allHits);
    const topWords = Object.entries(wordCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([word]) => word);
    const negativeRatio = sentiments.filter((value) => value === "负面").length / sentiments.length;
    const summary = themeRecords.length === 1
      ? `有 1 条反馈涉及${theme}，需要结合原话判断是否为个别问题。`
      : `${themeRecords.length} 条反馈涉及${theme}，${
        negativeRatio >= 0.6 ? "集中出现负面声音" : "存在不同态度"
      }，建议结合证据原话确认主要触发场景。`;
    const actionSuffix = topWords.length ? ` 当前高频线索：${topWords.slice(0, 3).join("、")}。` : "";
    const confidence = themeLabels.reduce((sum, label) => sum + label.confidence, 0) / themeLabels.length;
    const evidence = [...themeRecords]
      .sort((a, b) => {
        const severityDelta = Number(classifySeverity(a, theme) !== "high") - Number(classifySeverity(b, theme) !== "high");
        if (severityDelta) return severityDelta;
        return (a.rating ?? 6) - (b.rating ?? 6);
      })
      .slice(0, 3);

    return {
      theme,
      count: themeRecords.length,
      share: themeRecords.length / records.length,
      sentiment,
      severity,
      priorityScore: priorityScore(themeRecords, records.length, sentiments, severities),
      summary,
      action: THEME_ACTIONS[theme] + actionSuffix,
      confidence: Math.round(confidence * 100) / 100,
      evidence,
    };
  }).sort((a, b) => b.priorityScore - a.priorityScore || b.count - a.count);
}

function countValues(values) {
  return values.reduce((counts, value) => {
    counts[value] = (counts[value] || 0) + 1;
    return counts;
  }, {});
}

function makeRun(records, datasetName) {
  const { cleaned, dropped } = cleanRecords(records);
  if (!cleaned.length) throw new Error("没有可分析的有效反馈。");
  const insights = buildInsights(cleaned);
  const ratings = cleaned.map((record) => record.rating).filter((value) => value !== null);
  const evidenceIds = new Set(insights.flatMap((insight) => insight.evidence.map((record) => record.id)));
  const highSeverityCount = cleaned.filter((record) => {
    const { theme } = classifyTheme(record.text);
    return classifySeverity(record, theme) === "high";
  }).length;
  const warnings = [];
  if (cleaned.length < 10) warnings.push("样本少于 10 条，结论只适合作为探索性线索。");
  if (ratings.length / cleaned.length < 0.5) warnings.push("评分字段覆盖不足，情绪判断主要依赖文本。");
  if (insights.some((insight) => insight.confidence < 0.5)) {
    warnings.push("存在低置信度分类，建议人工复核证据原话。");
  }
  const reviewReasons = [];
  if (insights.some((insight) => insight.severity === "high")) {
    reviewReasons.push("检测到高严重度反馈，发布结论前需要人工确认。");
  }
  if (insights.some((insight) => insight.confidence < 0.5)) reviewReasons.push("部分主题置信度较低。");
  if (cleaned.length < 10) reviewReasons.push("样本量较小。");
  const top = insights[0];
  const risk = highSeverityCount ? `，其中 ${highSeverityCount} 条为高严重度线索` : "";
  const summary = `共分析 ${cleaned.length} 条有效反馈。当前最优先主题是“${top.theme}”，占 ${formatPercent(
    top.share,
  )}，优先级 ${top.priorityScore.toFixed(1)}/100${risk}。建议先核对代表性原话，再决定是否进入产品迭代。`;
  const now = new Date();
  return {
    runId: crypto.randomUUID().replaceAll("-", "").slice(0, 12),
    createdAt: localIsoString(now),
    datasetName: datasetName.trim() || "未命名数据集",
    analysisMode: "rules",
    engine: "本地规则（离线）",
    engineNote: "公开离线演示模式，不读取或发送任何反馈数据到外部服务。",
    totalFeedback: cleaned.length,
    insights,
    dataQuality: {
      inputCount: records.length,
      validCount: cleaned.length,
      droppedCount: dropped,
      ratingCoverage: ratings.length / Math.max(cleaned.length, 1),
      evidenceCoverage: evidenceIds.size / Math.max(cleaned.length, 1),
      highSeverityCount,
      warnings,
    },
    executiveSummary: summary,
    reviewRequired: reviewReasons.length > 0,
    reviewReasons,
    reviewStatus: "pending",
    reviewNote: "",
  };
}

function localIsoString(date) {
  const offset = date.getTimezoneOffset() * 60000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 19);
}

function formatPercent(value) {
  return `${Math.round(value * 100)}%`;
}

function severityLabel(value) {
  return { high: "高", medium: "中", low: "低" }[value] || value;
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let value = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (quoted) {
      if (char === '"' && text[index + 1] === '"') {
        value += '"';
        index += 1;
      } else if (char === '"') {
        quoted = false;
      } else {
        value += char;
      }
    } else if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      row.push(value);
      value = "";
    } else if (char === "\n") {
      row.push(value.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      value = "";
    } else {
      value += char;
    }
  }
  if (value || row.length) {
    row.push(value.replace(/\r$/, ""));
    rows.push(row);
  }
  return rows.filter((cells) => cells.some((cell) => cell.trim()));
}

function recordsFromCsv(text) {
  const rows = parseCsv(text.replace(/^\uFEFF/, ""));
  if (rows.length < 2) throw new Error("CSV 缺少表头或数据行。");
  const aliases = {
    id: ["id", "反馈id", "编号", "feedback_id"],
    text: ["text", "content", "反馈内容", "评论", "用户反馈", "内容"],
    source: ["source", "来源", "渠道"],
    rating: ["rating", "评分", "星级", "score"],
    createdAt: ["created_at", "date", "时间", "日期"],
  };
  const headers = rows[0].map((header) => normalizeText(header));
  const mapping = {};
  Object.entries(aliases).forEach(([key, options]) => {
    mapping[key] = headers.findIndex((header) => options.some((option) => normalizeText(option) === header));
  });
  if (mapping.text < 0) throw new Error("CSV 至少需要一个“反馈内容”或 text 列。");
  return rows.slice(1).map((cells, index) => ({
    id: cells[mapping.id]?.trim() || `F${String(index + 1).padStart(3, "0")}`,
    text: cells[mapping.text]?.trim() || "",
    source: cells[mapping.source]?.trim() || "未知渠道",
    rating: parseRating(cells[mapping.rating]),
    createdAt: cells[mapping.createdAt]?.trim() || null,
  })).filter((record) => record.text);
}

function recordsFromLines(text) {
  return String(text)
    .split(/\r?\n/)
    .map((line) => line.replace(/^[\s\-*]+/, "").trim())
    .filter(Boolean)
    .map((line, index) => ({
      id: `M${String(index + 1).padStart(3, "0")}`,
      text: line,
      source: "手动粘贴",
      rating: null,
      createdAt: null,
    }));
}

function currentRecords() {
  if (state.source === "csv") return state.uploadedRecords;
  if (state.source === "text") return state.pastedRecords;
  return DEMO_RECORDS;
}

function renderPreview() {
  const records = currentRecords();
  state.records = records;
  $("#record-count").textContent = `${records.length} 条可分析反馈`;
  $("#preview-body").innerHTML = records.slice(0, 8).map((record) => `
    <tr>
      <td>${escapeHtml(record.id)}</td>
      <td>${escapeHtml(record.text)}</td>
      <td>${escapeHtml(record.source)}</td>
      <td>${record.rating ?? "—"}</td>
    </tr>
  `).join("");
  $("#preview-note").textContent = records.length > 8
    ? `预览仅展示前 8 条，分析将使用全部 ${records.length} 条。`
    : records.length
      ? "以上为全部待分析数据。"
      : "当前没有可分析数据。";
  $("#analyze-button").disabled = records.length === 0;
}

function setTab(tabName) {
  $$(".tab").forEach((button) => {
    const active = button.dataset.tab === tabName;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-selected", String(active));
  });
  $$(".panel").forEach((panel) => panel.classList.toggle("is-active", panel.dataset.panel === tabName));
  $$(".panel").forEach((panel) => {
    panel.setAttribute("aria-hidden", String(panel.dataset.panel !== tabName));
  });
  window.scrollTo({ top: 285, behavior: "smooth" });
}

function switchSource(source) {
  state.source = source;
  $$(".source-option").forEach((button) => button.classList.toggle("is-active", button.dataset.source === source));
  $$(".source-panel").forEach((panel) => panel.classList.toggle("is-active", panel.dataset.sourcePanel === source));
  renderPreview();
}

function renderRun(run) {
  state.currentRun = run;
  $("#insights-empty").classList.add("is-hidden");
  $("#insights-content").classList.remove("is-hidden");
  $("#report-title").textContent = run.datasetName;
  $("#report-meta").textContent =
    `${run.createdAt.replace("T", " ")} · 运行 ${run.runId} · ${run.totalFeedback} 条有效反馈`;
  $("#metrics").innerHTML = [
    ["有效反馈", run.totalFeedback, `${run.dataQuality.droppedCount} 条去重或丢弃`],
    ["识别主题", run.insights.length, "可回到原话验证"],
    ["最高优先级", `${run.insights[0].priorityScore.toFixed(1)}/100`, run.insights[0].theme],
    ["审核状态", STATUS_LABELS[run.reviewStatus], run.reviewRequired ? "已触发质量门禁" : "建议抽样检查"],
  ].map(([label, value, note]) => `
    <div class="metric">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
      <small>${escapeHtml(note)}</small>
    </div>
  `).join("");
  $("#executive-summary").textContent = run.executiveSummary;
  $("#engine-note").textContent = `引擎：${run.engine} · ${run.engineNote}`;
  $("#review-required-chip").textContent = run.reviewRequired ? "需要人工审核" : "可进入抽样检查";
  $("#review-required-chip").className = `status-chip ${run.reviewRequired ? "is-danger" : "is-ready"}`;
  $("#quality-stats").innerHTML = `
    <div class="quality-stat"><span>评分覆盖</span><strong>${formatPercent(run.dataQuality.ratingCoverage)}</strong></div>
    <div class="quality-stat"><span>证据覆盖</span><strong>${formatPercent(run.dataQuality.evidenceCoverage)}</strong></div>
    <div class="quality-stat"><span>高严重度</span><strong>${run.dataQuality.highSeverityCount} 条</strong></div>
    <div class="quality-stat"><span>清洗后有效率</span><strong>${formatPercent(run.dataQuality.validCount / Math.max(run.dataQuality.inputCount, 1))}</strong></div>
  `;
  $("#quality-warnings").innerHTML = run.dataQuality.warnings.length
    ? run.dataQuality.warnings.map((warning) => `<div class="warning-item">⚠ ${escapeHtml(warning)}</div>`).join("")
    : '<div class="success-item">✓ 未发现明显的数据质量风险</div>';
  $("#bar-chart").innerHTML = run.insights.map((insight) => `
    <div class="bar-row">
      <span class="bar-label">${escapeHtml(insight.theme)}</span>
      <div
        class="bar-track"
        role="progressbar"
        aria-label="${escapeHtml(insight.theme)}优先级"
        aria-valuemin="0"
        aria-valuemax="100"
        aria-valuenow="${insight.priorityScore}"
        aria-valuetext="${insight.priorityScore.toFixed(1)} 分（满分 100 分）"
      >
        <div class="bar-fill" style="width:${insight.priorityScore}%"></div>
      </div>
      <span class="bar-score">${insight.priorityScore.toFixed(1)}</span>
    </div>
  `).join("");
  $("#insight-list").innerHTML = run.insights.map((insight, index) => `
    <details class="insight-card" ${index < 2 ? "open" : ""}>
      <summary>
        <span class="insight-rank">${String(index + 1).padStart(2, "0")}</span>
        <span class="insight-title">
          <strong>${escapeHtml(insight.theme)}</strong>
          <span>${insight.count} 条反馈 · 占 ${formatPercent(insight.share)}</span>
        </span>
        <span class="priority-pill">${insight.priorityScore.toFixed(1)} / 100</span>
      </summary>
      <div class="insight-body">
        <div class="insight-facts">
          <div class="insight-fact"><span>主要情绪</span><strong>${escapeHtml(insight.sentiment)}</strong></div>
          <div class="insight-fact"><span>严重度</span><strong>${severityLabel(insight.severity)}</strong></div>
          <div class="insight-fact"><span>分类置信度</span><strong>${formatPercent(insight.confidence)}</strong></div>
          <div class="insight-fact"><span>证据数量</span><strong>${insight.evidence.length} 条</strong></div>
        </div>
        <p class="insight-summary">${escapeHtml(insight.summary)}</p>
        <div class="action-callout"><strong>建议行动：</strong>${escapeHtml(insight.action)}</div>
        <div class="evidence-title">代表原话</div>
        ${insight.evidence.map((record) => `
          <blockquote class="quote">
            ${escapeHtml(record.text)}
            <cite>— ${escapeHtml(record.source)} / ${escapeHtml(record.id)}</cite>
          </blockquote>
        `).join("")}
      </div>
    </details>
  `).join("");
  renderReview(run);
  renderHistory();
}

function renderReview(run) {
  $("#review-empty").classList.add("is-hidden");
  $("#review-content").classList.remove("is-hidden");
  $("#review-run-id").textContent = run.runId;
  $("#review-reasons").innerHTML = run.reviewReasons.length
    ? run.reviewReasons.map((reason) => `<div class="warning-item">${escapeHtml(reason)}</div>`).join("")
    : '<div class="success-item">本次结果未触发强制审核原因，仍建议进行抽样检查。</div>';
  const selected = $(`input[name="review-status"][value="${run.reviewStatus}"]`);
  if (selected) selected.checked = true;
  $("#review-note").value = run.reviewNote || "";
  $("#review-save-status").textContent = "";
}

function renderHistory() {
  const history = state.history;
  $("#history-empty").classList.toggle("is-hidden", history.length > 0);
  $("#history-table-wrap").classList.toggle("is-hidden", history.length === 0);
  $("#history-body").innerHTML = history.map((run) => `
    <tr>
      <td><code>${escapeHtml(run.runId)}</code></td>
      <td>${escapeHtml(run.datasetName)}</td>
      <td>${escapeHtml(run.createdAt.replace("T", " "))}</td>
      <td>${run.totalFeedback}</td>
      <td>${escapeHtml(STATUS_LABELS[run.reviewStatus])}</td>
      <td><button class="history-open" type="button" data-open-run="${escapeHtml(run.runId)}">打开报告</button></td>
    </tr>
  `).join("");
}

function saveCurrentRun() {
  const existingIndex = state.history.findIndex((run) => run.runId === state.currentRun.runId);
  if (existingIndex >= 0) {
    state.history[existingIndex] = structuredClone(state.currentRun);
  } else {
    state.history.unshift(structuredClone(state.currentRun));
  }
  state.history = state.history.slice(0, 30);
  try {
    localStorage.setItem("feedback-insight-runs-v1", JSON.stringify(state.history));
  } catch {
    showToast("报告已打开，但浏览器未允许本地保存。");
  }
  renderHistory();
}

function loadHistory() {
  try {
    const saved = JSON.parse(localStorage.getItem("feedback-insight-runs-v1") || "[]");
    state.history = Array.isArray(saved) ? saved.slice(0, 30) : [];
  } catch {
    state.history = [];
  }
}

function openRun(runId) {
  const run = state.history.find((item) => item.runId === runId);
  if (!run) return;
  renderRun(structuredClone(run));
  setTab("insights");
  window.scrollTo({ top: 285, behavior: "smooth" });
}

function markdownReport(run) {
  const lines = [
    `# 用户反馈洞察报告：${run.datasetName}`,
    "",
    `- 运行编号：\`${run.runId}\``,
    `- 生成时间：${run.createdAt}`,
    `- 分析引擎：${run.engine}`,
    `- 有效反馈：${run.dataQuality.validCount} 条`,
    `- 审核状态：${STATUS_LABELS[run.reviewStatus]}`,
    "",
    "## 核心结论",
    "",
    run.executiveSummary,
    "",
    "## 数据质量",
    "",
    `- 原始输入：${run.dataQuality.inputCount} 条`,
    `- 清洗后：${run.dataQuality.validCount} 条`,
    `- 去重或丢弃：${run.dataQuality.droppedCount} 条`,
    `- 评分覆盖率：${formatPercent(run.dataQuality.ratingCoverage)}`,
    `- 证据覆盖率：${formatPercent(run.dataQuality.evidenceCoverage)}`,
    `- 高严重度反馈：${run.dataQuality.highSeverityCount} 条`,
    ...run.dataQuality.warnings.map((warning) => `- 注意事项：${warning}`),
    "",
    "## 优先级主题",
    "",
  ];
  run.insights.forEach((insight, index) => {
    lines.push(
      `### ${index + 1}. ${insight.theme}`,
      "",
      `- 反馈数量：${insight.count}`,
      `- 占比：${formatPercent(insight.share)}`,
      `- 主要情绪：${insight.sentiment}`,
      `- 严重度：${severityLabel(insight.severity)}`,
      `- 优先级：${insight.priorityScore.toFixed(1)}/100`,
      `- 分类置信度：${formatPercent(insight.confidence)}`,
      "",
      `**摘要：** ${insight.summary}`,
      "",
      `**建议行动：** ${insight.action}`,
      "",
      "**代表原话：**",
      "",
    );
    insight.evidence.forEach((record) => {
      lines.push(`> ${record.text}  `, `> — ${record.source} / ${record.id}`, "");
    });
  });
  lines.push(
    "## 人工审核",
    "",
    `- 是否要求审核：${run.reviewRequired ? "是" : "否"}`,
    `- 审核状态：${STATUS_LABELS[run.reviewStatus]}`,
    `- 审核备注：${run.reviewNote || "无"}`,
    ...run.reviewReasons.map((reason) => `- 审核原因：${reason}`),
    "",
    "## 边界说明",
    "",
    "本报告用于辅助发现问题和排序，不替代用户访谈或业务决策。低样本量、低置信度或高严重度结论必须经过人工复核。",
    "",
  );
  return lines.join("\n");
}

function downloadFile(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

let toastTimer;
function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.add("is-visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("is-visible"), 2600);
}

function bindEvents() {
  $$(".tab").forEach((button) => button.addEventListener("click", () => setTab(button.dataset.tab)));
  $$("[data-go-tab]").forEach((button) => button.addEventListener("click", () => setTab(button.dataset.goTab)));
  $$(".source-option").forEach((button) => button.addEventListener("click", () => switchSource(button.dataset.source)));

  $("#csv-file").addEventListener("change", async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    try {
      const buffer = await file.arrayBuffer();
      let text;
      try {
        text = new TextDecoder("utf-8", { fatal: true }).decode(buffer);
      } catch {
        text = new TextDecoder("gb18030").decode(buffer);
      }
      state.uploadedRecords = recordsFromCsv(text);
      $("#csv-status").textContent = `已读取 ${state.uploadedRecords.length} 条反馈：${file.name}`;
      renderPreview();
    } catch (error) {
      state.uploadedRecords = [];
      $("#csv-status").textContent = error.message;
      renderPreview();
    }
  });

  $("#text-input").addEventListener("input", (event) => {
    state.pastedRecords = recordsFromLines(event.target.value);
    renderPreview();
  });

  $("#analyze-button").addEventListener("click", () => {
    try {
      const datasetName = state.source === "csv"
        ? $("#csv-name").value
        : state.source === "text"
          ? $("#text-name").value
          : "拾光笔记 · 产品反馈演示";
      const run = makeRun(currentRecords(), datasetName);
      renderRun(run);
      saveCurrentRun();
      setTab("insights");
      window.scrollTo({ top: 285, behavior: "smooth" });
      showToast(`分析完成：${run.insights.length} 个主题，${run.totalFeedback} 条有效反馈。`);
    } catch (error) {
      showToast(error.message);
    }
  });

  $("#download-md").addEventListener("click", () => {
    if (!state.currentRun) return;
    downloadFile(
      `feedback-report-${state.currentRun.runId}.md`,
      markdownReport(state.currentRun),
      "text/markdown;charset=utf-8",
    );
  });

  $("#download-json").addEventListener("click", () => {
    if (!state.currentRun) return;
    downloadFile(
      `feedback-report-${state.currentRun.runId}.json`,
      JSON.stringify(state.currentRun, null, 2),
      "application/json;charset=utf-8",
    );
  });

  $("#save-review").addEventListener("click", () => {
    if (!state.currentRun) return;
    const selected = $('input[name="review-status"]:checked');
    state.currentRun.reviewStatus = selected?.value || "pending";
    state.currentRun.reviewNote = $("#review-note").value.trim();
    $("#review-save-status").textContent = "审核结果已保存到当前浏览器。";
    saveCurrentRun();
    renderRun(structuredClone(state.currentRun));
    setTab("review");
    showToast("审核结果已保存。");
  });

  $("#history-body").addEventListener("click", (event) => {
    const button = event.target.closest("[data-open-run]");
    if (button) openRun(button.dataset.openRun);
  });

  $("#clear-history").addEventListener("click", () => {
    if (!state.history.length) return;
    if (!window.confirm("确定清空当前浏览器中的历史报告吗？此操作不可撤销。")) return;
    state.history = [];
    localStorage.removeItem("feedback-insight-runs-v1");
    renderHistory();
    showToast("历史记录已清空。");
  });
}

function init() {
  loadHistory();
  bindEvents();
  renderPreview();
  renderHistory();
}

init();
