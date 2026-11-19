// 回声 Echo — 模拟数据与任务规划
// 全部数据为虚构演示数据，前端本地运行。

export type ViewKey = 'briefing' | 'delegate' | 'task' | 'review' | 'inbox';

export type Autonomy = 'stepwise' | 'keypoints' | 'fullauto';

export const AUTONOMY_LABELS: Record<Autonomy, string> = {
  stepwise: '每一步问我',
  keypoints: '关键节点问我',
  fullauto: '全自动，发前确认',
};

export const AUTONOMY_DESCS: Record<Autonomy, string> = {
  stepwise: 'Agent 每执行一步都先征得你同意',
  keypoints: '只在起草、发送等关键节点停下来问你',
  fullauto: 'Agent 自行推进，只在真正发送前让你确认',
};

/* ---------------- 邮件 ---------------- */

export interface Email {
  id: string;
  from: string;
  role: string;
  subject: string;
  preview: string;
  body: string[];
  time: string;
  unread: boolean;
  tag: string;
}

export const EMAILS: Email[] = [
  {
    id: 'e1',
    from: '林晓彤',
    role: '设计总监',
    subject: '评审邀请：Echo 首页改版方案评审（周四 14:00）',
    preview: '各位好，Echo 首页改版的交互稿已经定版，邀请大家周四下午参加评审……',
    body: [
      '各位好，',
      'Echo 首页改版的交互稿已经定版，邀请大家周四 14:00 在 3 号会议室（同步线上）参加评审。本次评审重点看三块：首屏信息层级、任务卡片的密度、以及空状态的引导文案。',
      '评审材料已放在共享盘「设计评审 / 2026-Q4」目录下，请提前扫一眼，有问题先在文档里评论，评审时集中过。',
      '评审结束后需要当场定版，定版稿周五交付开发。请务必准时参加。',
      '林晓彤',
    ],
    time: '09:12',
    unread: true,
    tag: '会议',
  },
  {
    id: 'e2',
    from: 'Daniel Chen',
    role: 'Meridian Capital · 品牌负责人',
    subject: 'Re: Q4 brand site proposal — timeline & quote validity',
    preview: 'Hi Toni, thanks for the proposal. Two questions before we sign off: is the quote still valid…',
    body: [
      'Hi Toni,',
      'Thanks for the proposal. Two questions before we sign off internally:',
      '1) Is the quote from last Tuesday still valid through the end of November? Our procurement cycle closes on the 28th.',
      '2) If we confirm this week, can the first milestone (discovery + IA) still start on Dec 2 as proposed?',
      'If both are yes, I can get the SOW signed this week.',
      'Best, Daniel',
    ],
    time: '08:47',
    unread: true,
    tag: '客户',
  },
  {
    id: 'e3',
    from: '周子昂',
    role: '产品经理',
    subject: '产品周会改期：本周五 10:00，议程已更新',
    preview: '原定周三的产品周会改到周五上午 10:00，议程里新增了 Q1 路线图对齐……',
    body: [
      '大家好，',
      '原定周三的产品周会改到本周五 10:00，地点不变（线上）。',
      '议程更新了两项：新增 Q1 路线图对齐，以及上周用户访谈的结论同步。每人需要提前准备自己负责模块的进展，一页纸以内。',
      '周子昂',
    ],
    time: '昨天 18:20',
    unread: false,
    tag: '会议',
  },
  {
    id: 'e4',
    from: '李维斯',
    role: '青禾家居 · 采购经理',
    subject: '询价跟进：官网改版项目的报价什么时候能确认？',
    preview: 'Toni 你好，上周发的官网改版询价还没收到回复，想确认一下报价和档期……',
    body: [
      'Toni 你好，',
      '上周三我发了官网改版项目的询价邮件，一直没有收到回复，想跟进一下。',
      '我们内部希望在 12 月中旬前定下供应商，年底前签合同。想确认两点：一是你们的报价区间，二是最早能什么时候启动。',
      '如果这周能给个初步答复，我们就可以约下周当面聊细节。',
      '李维斯',
    ],
    time: '周一 11:03',
    unread: true,
    tag: '客户',
  },
  {
    id: 'e5',
    from: '财务部',
    role: '财务共享中心',
    subject: '报销提醒：10 月差旅发票请于本周内补齐',
    preview: '系统检测到你有 2 笔差旅报销缺少发票原件，请在本周五前补齐提交……',
    body: [
      '你好，',
      '系统检测到你有 2 笔 10 月差旅报销缺少发票原件：上海出差高铁票（10 月 21 日）、深圳客户拜访打车费（10 月 24 日）。',
      '请在本周五 18:00 前在报销系统补齐上传，逾期将顺延到下个结算周期。',
      '财务共享中心',
    ],
    time: '昨天 15:40',
    unread: false,
    tag: '财务',
  },
  {
    id: 'e6',
    from: '王静',
    role: 'HR · 招聘',
    subject: '面试安排：高级产品设计师候选人（赵一帆）终面',
    preview: '候选人赵一帆已通过二面，终面安排在下周二，需要你作为设计评委参加……',
    body: [
      'Toni 你好，',
      '高级产品设计师候选人赵一帆已通过二面，终面安排在下周二 15:00，需要你作为设计评委参加，时长约 45 分钟。',
      '候选人的作品集和二面评价已附在日历邀请里。终面重点考察系统化设计能力和跨职能协作，请提前准备 2 到 3 个深挖问题。',
      '王静',
    ],
    time: '昨天 10:05',
    unread: true,
    tag: '招聘',
  },
  {
    id: 'e7',
    from: '赵晴',
    role: '项目助理',
    subject: '会议纪要：供应链对齐会（11 月 17 日）',
    preview: '昨日供应链对齐会纪要：确认了三家供应商的交期，遗留问题是包装规格待定……',
    body: [
      '各位好，附件为昨日供应链对齐会的纪要，要点如下：',
      '1. 三家供应商的交期已确认，最晚一批 12 月 5 日到仓；',
      '2. 包装规格仍待品牌方确认，赵晴跟进，周三前给结论；',
      '3. 下次对齐会定在 12 月 1 日。',
      '赵晴',
    ],
    time: '周一 09:31',
    unread: false,
    tag: '纪要',
  },
  {
    id: 'e8',
    from: 'Figma',
    role: '产品更新',
    subject: "What's new in Figma: Dev Mode annotations and more",
    preview: 'This month: annotation threads in Dev Mode, variable scoping improvements…',
    body: [
      'Hi there,',
      'This month in Figma: annotation threads in Dev Mode, variable scoping improvements, and a faster way to compare versions.',
      'Open Figma to try them out.',
      'The Figma Team',
    ],
    time: '周日 08:00',
    unread: false,
    tag: '订阅',
  },
  {
    id: 'e9',
    from: 'Notion',
    role: '每周摘要',
    subject: '你的每周摘要：3 个页面有更新',
    preview: '本周「产品路线图」「设计系统」等 3 个页面有协作者更新……',
    body: [
      '你好，',
      '本周你关注的 3 个页面有更新：「产品路线图」新增 2 条评论，「设计系统」更新了色彩规范，「用户访谈记录」新增 1 篇。',
      'Notion',
    ],
    time: '周日 07:30',
    unread: false,
    tag: '订阅',
  },
];

/* ---------------- 需要你决定 ---------------- */

export interface Decision {
  id: string;
  title: string;
  context: string;
  recommendation: string;
  draft?: string;
  source: string;
}

export const INITIAL_DECISIONS: Decision[] = [
  {
    id: 'd1',
    title: '回复 Meridian Capital 的报价确认',
    context:
      'Daniel Chen 今早来信确认两件事：上周二的报价是否在 11 月底前有效，以及本周确认后 12 月 2 日能否按原计划启动第一阶段。两点与报价单原文一致，Agent 已按确认口径起草回复。',
    recommendation: '建议批准发送。内容只确认既有承诺，不涉及新报价。',
    draft:
      'Hi Daniel,\n\nThanks for getting back to us.\n\n1) Yes — the quote from last Tuesday remains valid through Nov 30.\n2) Yes — if we confirm this week, the first milestone (discovery + IA) can start on Dec 2 as proposed.\n\nHappy to jump on a short call if anything else would help the sign-off.\n\nBest,\nToni',
    source: '关联邮件：Re: Q4 brand site proposal',
  },
  {
    id: 'd2',
    title: '周四日程冲突：设计评审与客户电话撞期',
    context:
      '周四 14:00 林晓彤召集 Echo 首页改版评审，同一时间青禾家居李维斯希望约电话确认询价。评审有 6 人参加且需当场定版，客户电话可弹性安排。',
    recommendation: '建议参加评审，把客户电话改到周四 16:30，并先回一封简短邮件说明。',
    source: '关联邮件：评审邀请 + 青禾家居询价',
  },
  {
    id: 'd3',
    title: '一笔报销金额与发票不符',
    context:
      '10 月 24 日深圳打车费报销申请为 86 元，发票金额为 68 元，差额 18 元。财务要求本周五前补齐或修正。',
    recommendation: '建议按发票金额 68 元修正申请，差额不再申报。Agent 可以直接改，你只需确认。',
    source: '关联邮件：财务部报销提醒',
  },
];

/* ---------------- 待审阅草稿 ---------------- */

export interface Draft {
  id: string;
  to: string;
  subject: string;
  body: string;
  source: string;
  status: 'pending' | 'sent';
}

export const INITIAL_DRAFTS: Draft[] = [
  {
    id: 'dr1',
    to: '设计评审参会人（6 人）',
    subject: '纪要与下一步：Echo 首页改版评审',
    body: '各位好，\n\n感谢参加今天的评审。结论与下一步如下：\n\n1. 首屏信息层级通过，任务卡片密度按 B 版执行；\n2. 空状态引导文案由我补一版，周五中午前发到群里确认；\n3. 定版稿周五交付开发，视觉走查安排在下周一。\n\n如有遗漏请直接回复补充。\n\nToni',
    source: '由任务「给设计评审参会人发纪要和下一步」生成',
    status: 'pending',
  },
  {
    id: 'dr2',
    to: '李维斯（青禾家居）',
    subject: 'Re: 官网改版项目询价跟进',
    body: '李维斯你好，\n\n抱歉回复晚了。官网改版项目的初步报价区间和档期如下：整体预算区间在 18 万到 24 万之间（视页面规模与动效复杂度浮动），最早可于 12 月 1 日启动，第一阶段（信息架构与首页设计）约 3 周。\n\n方便的话，我们约下周二或周三当面过一版方案细节？\n\nToni',
    source: '由任务「跟进上周没回复的客户询价」生成',
    status: 'pending',
  },
  {
    id: 'dr3',
    to: '赵晴',
    subject: 'Re: 供应链对齐会纪要确认',
    body: '赵晴你好，\n\n纪要已确认，内容无误。补充一点：包装规格的品牌方确认如果周三前没有结论，建议按现有规格先行打样，避免影响 12 月 5 日的到仓时间。\n\n谢谢整理。\n\nToni',
    source: '由 Agent 阅读纪要后生成',
    status: 'pending',
  },
];

/* ---------------- 已完成动态 ---------------- */

export interface DoneItem {
  id: string;
  text: string;
  output: string;
  time: string;
}

export const INITIAL_DONE: DoneItem[] = [
  { id: 'c1', text: '归档了 14 封订阅与通知类邮件', output: '归档清单', time: '08:15' },
  { id: 'c2', text: '为周五产品周会生成议程草稿（已同步子昂的改期）', output: '议程草稿', time: '08:40' },
  { id: 'c3', text: '把 3 张发票信息录入报销表，标出 1 处金额不一致', output: '报销表', time: '09:02' },
];

/* ---------------- 审计日志 ---------------- */

export interface ActivityEntry {
  id: string;
  time: string;
  text: string;
}

export const INITIAL_ACTIVITY: ActivityEntry[] = [
  { id: 'a1', time: '09:02', text: 'Agent 将 3 张发票录入报销表（授权范围：整理类，可自动执行）' },
  { id: 'a2', time: '08:40', text: 'Agent 生成产品周会议程草稿，未发送（授权范围：起草类，发送前需确认）' },
  { id: 'a3', time: '08:15', text: 'Agent 归档 14 封订阅与通知邮件（授权范围：整理类，可自动执行）' },
  { id: 'a4', time: '07:50', text: 'Agent 完成夜间扫描：读取 23 封新邮件，分类并生成今日简报' },
];

/* ---------------- 委托：预设计划 ---------------- */

export interface TaskStep {
  label: string;
  note: string;
  gate?: 'tone' | 'send';
}

export interface TaskPlan {
  steps: TaskStep[];
  draftTo: string;
  draftSubject: string;
  toneFormal: string;
  toneConcise: string;
  resultSummary: string;
}

export const PRESET_INTENTS: string[] = [
  '跟进上周没回复的客户询价',
  '把本周会议邮件整理成待办',
  '给设计评审参会人发纪要和下一步',
  '帮我婉拒下周的非必要会议',
];

export function buildPlan(intent: string): TaskPlan {
  if (intent.includes('纪要') || intent.includes('评审')) {
    return {
      steps: [
        { label: '读取相关邮件', note: '已找到评审邀请与会前材料共 4 封，评审结论记录在林晓彤的邮件线程里。' },
        { label: '归纳上下文', note: '提取出 3 条结论与 3 项下一步，负责人和时间点都已对齐原文。' },
        { label: '起草纪要邮件', note: '已按结论、下一步、时间点三段式起草，请你选一个语气版本。', gate: 'tone' },
        { label: '发送并记录跟进', note: '发送后会把下一步同步进待办，并设置周五的跟进提醒。' },
      ],
      draftTo: '设计评审参会人（6 人）',
      draftSubject: '纪要与下一步：Echo 首页改版评审',
      toneFormal:
        '各位好：\n\n感谢各位参加今日评审，现将结论与下一步同步如下。\n\n一、首屏信息层级方案通过，任务卡片密度按 B 版执行；\n二、空状态引导文案由我补充一版，周五中午前发出确认；\n三、定版稿周五交付开发，视觉走查安排在下周一。\n\n如有遗漏，请回复补充。谢谢各位。\n\nToni',
      toneConcise:
        '各位好，评审结论同步：\n\n1. 首屏层级通过，卡片密度用 B 版；\n2. 空状态文案我周五中午前补一版；\n3. 定版稿周五交开发，下周一走查。\n\n有遗漏直接回复我。\n\nToni',
      resultSummary: '纪要已生成，覆盖 3 条结论与 3 项下一步，收件人为评审参会人共 6 人。',
    };
  }
  if (intent.includes('会议') && (intent.includes('待办') || intent.includes('整理'))) {
    return {
      steps: [
        { label: '扫描本周邮件', note: '本周共 9 封邮件，其中会议相关 4 封：2 个邀请、1 次改期、1 份纪要。' },
        { label: '提取时间与参会人', note: '已对齐日历：周四 14:00 设计评审、周五 10:00 产品周会、下周二 15:00 终面。' },
        { label: '生成待办清单', note: '已整理成带负责人和截止时间的待办，请你确认清单版本。', gate: 'tone' },
        { label: '写入待办并提醒', note: '清单会写入待办应用，并在每个节点前 1 天提醒你。' },
      ],
      draftTo: '我的待办清单',
      draftSubject: '本周会议待办（由邮件整理）',
      toneFormal:
        '本周会议待办清单\n\n1. 周四 14:00 Echo 首页改版评审：提前通读评审材料，准备定版意见（负责人：我）；\n2. 周五 10:00 产品周会：准备负责模块的一页纸进展（负责人：我）；\n3. 下周二 15:00 候选人终面：准备 2 到 3 个深挖问题（负责人：我，HR 王静已同步材料）。',
      toneConcise:
        '本周待办：\n\n1. 周四 14:00 设计评审，提前看材料；\n2. 周五 10:00 产品周会，备一页纸进展；\n3. 下周二 15:00 终面，备 3 个问题。',
      resultSummary: '已从 4 封会议邮件整理出 3 项待办，均带时间和准备事项。',
    };
  }
  if (intent.includes('婉拒') || intent.includes('拒绝')) {
    return {
      steps: [
        { label: '识别非必要会议', note: '下周共 5 个会议邀请，其中 2 个与你无直接议程关系：行业分享会、供应商产品宣讲。' },
        { label: '归纳上下文', note: '两个会议都已有同事参加，议程与你当前项目无交集，婉拒不影响信息同步。' },
        { label: '起草婉拒邮件', note: '已起草婉拒并请求会后纪要，请你选一个语气版本。', gate: 'tone' },
        { label: '发送并记录', note: '发送后会在日历上释放对应时间段。' },
      ],
      draftTo: '会议邀请人（2 人）',
      draftSubject: 'Re: 下周会议邀请',
      toneFormal:
        '你好，感谢邀请。下周我的项目排期较满，无法参加本次会议。我已请参会的同事会后同步纪要，如有需要我补充意见的部分，随时邮件联系。谢谢理解。\n\nToni',
      toneConcise: '你好，下周排期冲突，这次就不参加了。麻烦会后把纪要发我一份，有需要我补充的随时喊我。谢谢！\n\nToni',
      resultSummary: '已识别 2 个非必要会议并起草婉拒，发送后可释放下周共 2.5 小时。',
    };
  }
  // 默认：客户询价跟进类
  return {
    steps: [
      { label: '读取相关邮件', note: '已找到 3 封相关邮件，最近一封是李维斯周一的跟进，上周的原始询价在更早的线程里。' },
      { label: '归纳上下文', note: '客户在等两件事：报价区间和最早启动时间。内部档期显示 12 月 1 日可启动。' },
      { label: '起草回复', note: '已按客户的两个问题逐条起草，请你选一个语气版本。', gate: 'tone' },
      { label: '发送并记录跟进', note: '发送后会记录这次跟进，若 3 天未回复自动提醒你。' },
    ],
    draftTo: '李维斯（青禾家居）',
    draftSubject: 'Re: 官网改版项目询价跟进',
    toneFormal:
      '李维斯您好，\n\n抱歉回复晚了。关于官网改版项目，初步答复如下：整体预算区间为 18 万至 24 万元，具体视页面规模与动效复杂度而定；档期方面，最早可于 12 月 1 日启动，第一阶段（信息架构与首页设计）约需 3 周。\n\n如方便，建议下周二或周三当面沟通方案细节，我提前准备演示材料。\n\n顺祝商祺\nToni',
    toneConcise:
      '李维斯你好，抱歉晚回。报价区间 18 万到 24 万（看页面规模和动效），最早 12 月 1 日能启动，第一阶段约 3 周。下周二或周三方便当面聊一版方案吗？\n\nToni',
    resultSummary: '已跟进青禾家居的询价，答复了报价区间与启动时间，并提出下周面谈。',
  };
}
