import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityEntry,
  Autonomy,
  Decision,
  DoneItem,
  Draft,
  Email,
  INITIAL_ACTIVITY,
  INITIAL_DECISIONS,
  INITIAL_DONE,
  INITIAL_DRAFTS,
  EMAILS,
  TaskPlan,
  ViewKey,
  buildPlan,
} from './data';
import Sidebar from './components/Sidebar';
import Briefing from './components/Briefing';
import Delegate from './components/Delegate';
import TaskProgress, { TaskState } from './components/TaskProgress';
import Review from './components/Review';
import Inbox from './components/Inbox';

let uid = 100;
const nextId = (p: string) => `${p}${++uid}`;

function nowTime(): string {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

export interface SeededTask {
  id: string;
  title: string;
  stepLabel: string;
  progress: number;
  cap: number;
}

export default function App() {
  const [view, setView] = useState<ViewKey>('briefing');
  const [decisions, setDecisions] = useState<Decision[]>(INITIAL_DECISIONS);
  const [drafts, setDrafts] = useState<Draft[]>(INITIAL_DRAFTS);
  const [doneFeed, setDoneFeed] = useState<DoneItem[]>(INITIAL_DONE);
  const [activity, setActivity] = useState<ActivityEntry[]>(INITIAL_ACTIVITY);
  const [emails, setEmails] = useState<Email[]>(EMAILS);
  const [task, setTask] = useState<TaskState | null>(null);
  const [delegatePrefill, setDelegatePrefill] = useState('');
  const [seeded, setSeeded] = useState<SeededTask[]>([
    { id: 's1', title: '整理本周会议邮件为待办', stepLabel: '正在提取时间与参会人', progress: 46, cap: 92 },
    { id: 's2', title: '汇总 10 月发票并核对金额', stepLabel: '正在核对第 3 张发票', progress: 68, cap: 95 },
  ]);
  const timerRef = useRef<number | null>(null);

  const log = useCallback((text: string) => {
    setActivity((prev) => [{ id: nextId('a'), time: nowTime(), text }, ...prev]);
  }, []);

  /* 简报里两个进行中任务的进度缓慢推进（展示用） */
  useEffect(() => {
    const t = window.setInterval(() => {
      setSeeded((prev) =>
        prev.map((s) => (s.progress < s.cap ? { ...s, progress: Math.min(s.cap, s.progress + 1) } : s)),
      );
    }, 2600);
    return () => window.clearInterval(t);
  }, []);

  /* ---------- 决策卡 ---------- */
  const resolveDecision = useCallback(
    (id: string, action: 'approve' | 'self' | 'ignore', editedDraft?: string) => {
      const d = decisions.find((x) => x.id === id);
      if (!d) return;
      setDecisions((prev) => prev.filter((x) => x.id !== id));
      if (action === 'approve') {
        log(`你批准了「${d.title}」${editedDraft ? '（含你的编辑）' : ''}，Agent 已执行发送`);
        setDoneFeed((prev) => [
          { id: nextId('c'), text: `${d.title}，已按建议处理`, output: '查看产出', time: nowTime() },
          ...prev,
        ]);
      } else if (action === 'self') {
        log(`「${d.title}」已转由你手动处理，Agent 停止跟进`);
      } else {
        log(`你忽略了「${d.title}」，Agent 不再提醒`);
      }
    },
    [decisions, log],
  );

  /* ---------- 任务引擎 ---------- */
  const launchTask = useCallback(
    (intent: string, autonomy: Autonomy) => {
      const plan: TaskPlan = buildPlan(intent);
      const steps = plan.steps.map((s) => {
        if (autonomy === 'fullauto' && s.gate === 'tone') return { ...s, gate: 'send' as const };
        return s;
      });
      setTask({
        id: nextId('t'),
        title: intent,
        intent,
        autonomy,
        plan: { ...plan, steps },
        current: 0,
        status: 'running',
        gate: null,
        tone: null,
        finalAction: null,
      });
      log(`你发起了任务「${intent}」，授权级别：${
        autonomy === 'stepwise' ? '每一步问我' : autonomy === 'keypoints' ? '关键节点问我' : '全自动，发前确认'
      }`);
      setView('task');
    },
    [log],
  );

  const completeStepAndContinue = useCallback((t: TaskState): TaskState => {
    const next = t.current + 1;
    if (next >= t.plan.steps.length) {
      return { ...t, current: next, status: 'done', gate: null };
    }
    return { ...t, current: next, status: 'running', gate: null };
  }, []);

  // 定时推进：每 1.8 秒走一步
  useEffect(() => {
    if (!task || task.status !== 'running') return;
    timerRef.current = window.setTimeout(() => {
      setTask((prev) => {
        if (!prev || prev.status !== 'running') return prev;
        const step = prev.plan.steps[prev.current];
        if (!step) return { ...prev, status: 'done' };
        if (step.gate) {
          return { ...prev, status: 'waiting', gate: step.gate };
        }
        if (prev.autonomy === 'stepwise') {
          return { ...prev, status: 'waiting', gate: 'step' };
        }
        return completeStepAndContinue(prev);
      });
    }, 1800);
    return () => {
      if (timerRef.current) window.clearTimeout(timerRef.current);
    };
  }, [task, completeStepAndContinue]);

  const resolveGate = useCallback(
    (payload: { tone?: 'formal' | 'concise'; sendAction?: 'send' | 'save' }) => {
      if (!task) return;
      let t: TaskState = { ...task, gate: null };
      if (payload.tone) {
        t = { ...t, tone: payload.tone };
        log(`任务「${t.title}」：你选择了${payload.tone === 'formal' ? '正式版' : '简洁版'}草稿，Agent 继续执行`);
      }
      if (payload.sendAction === 'send') {
        t = { ...t, finalAction: 'sent' };
        log(`任务「${t.title}」：你确认发送，Agent 已发送给 ${t.plan.draftTo}`);
      } else if (payload.sendAction === 'save') {
        t = { ...t, finalAction: 'saved' };
        log(`任务「${t.title}」：产出已存入待审阅，未发送`);
        setDrafts((ds) => [
          {
            id: nextId('dr'),
            to: t.plan.draftTo,
            subject: t.plan.draftSubject,
            body: t.tone === 'formal' ? t.plan.toneFormal : t.plan.toneConcise,
            source: `由任务「${t.title}」生成`,
            status: 'pending',
          },
          ...ds,
        ]);
      }
      const done = completeStepAndContinue(t);
      setTask(done);
    },
    [task, completeStepAndContinue, log],
  );

  /* 任务完成时统一记账（无论经由决策点还是自动跑完） */
  const doneLoggedRef = useRef<string | null>(null);
  useEffect(() => {
    if (task && task.status === 'done' && doneLoggedRef.current !== task.id) {
      doneLoggedRef.current = task.id;
      log(`任务「${task.title}」已完成：${task.plan.resultSummary}`);
      setDoneFeed((prevFeed) => [
        { id: nextId('c'), text: `任务完成：${task.title}`, output: '查看产出', time: nowTime() },
        ...prevFeed,
      ]);
    }
  }, [task, log]);

  const taskControl = useCallback(
    (action: 'pause' | 'resume' | 'takeover' | 'cancel') => {
      if (!task) return;
      if (action === 'pause') {
        log(`任务「${task.title}」已暂停`);
        setTask({ ...task, status: 'paused' });
      } else if (action === 'resume') {
        log(`任务「${task.title}」继续执行`);
        setTask({ ...task, status: 'running', gate: null });
      } else if (action === 'takeover') {
        log(`你接管了任务「${task.title}」，Agent 已停止`);
        setTask({ ...task, status: 'takenover' });
      } else {
        log(`任务「${task.title}」已终止`);
        setTask({ ...task, status: 'cancelled' });
      }
    },
    [task, log],
  );

  const taskFinalAction = useCallback(
    (action: 'send' | 'save', editedBody?: string) => {
      if (!task) return;
      if (action === 'send') {
        log(`任务「${task.title}」：成果已发送给 ${task.plan.draftTo}${editedBody ? '（含你的修改）' : ''}`);
        setTask({ ...task, finalAction: 'sent' });
      } else {
        log(`任务「${task.title}」：成果已存入待审阅`);
        setDrafts((ds) => [
          {
            id: nextId('dr'),
            to: task.plan.draftTo,
            subject: task.plan.draftSubject,
            body: editedBody ?? (task.tone === 'formal' ? task.plan.toneFormal : task.plan.toneConcise),
            source: `由任务「${task.title}」生成`,
            status: 'pending',
          },
          ...ds,
        ]);
        setTask({ ...task, finalAction: 'saved' });
      }
    },
    [task, log],
  );

  /* ---------- 草稿审阅 ---------- */
  const draftAction = useCallback(
    (id: string, action: 'send' | 'discard' | 'edit', body?: string) => {
      const d = drafts.find((x) => x.id === id);
      if (!d) return;
      if (action === 'send') {
        setDrafts((prev) => prev.map((x) => (x.id === id ? { ...x, status: 'sent' } : x)));
        log(`你批准发送了草稿「${d.subject}」给 ${d.to}`);
      } else if (action === 'discard') {
        setDrafts((prev) => prev.filter((x) => x.id !== id));
        log(`你丢弃了草稿「${d.subject}」`);
      } else if (action === 'edit' && body !== undefined) {
        setDrafts((prev) => prev.map((x) => (x.id === id ? { ...x, body } : x)));
        log(`你编辑了草稿「${d.subject}」`);
      }
    },
    [drafts, log],
  );

  /* ---------- 收件箱 ---------- */
  const markRead = useCallback((id: string) => {
    setEmails((prev) => prev.map((e) => (e.id === id ? { ...e, unread: false } : e)));
  }, []);

  const delegateFromEmail = useCallback((e: Email) => {
    setDelegatePrefill(`跟进这封来自${e.from}的邮件：${e.subject}`);
    setView('delegate');
  }, []);

  const counts = useMemo(
    () => ({
      decisions: decisions.length,
      review: drafts.filter((d) => d.status === 'pending').length,
      unread: emails.filter((e) => e.unread).length,
      taskActive: task && (task.status === 'running' || task.status === 'waiting' || task.status === 'paused') ? 1 : 0,
    }),
    [decisions, drafts, emails, task],
  );

  return (
    <div className="app">
      <Sidebar view={view} setView={setView} counts={counts} />
      <main className="main">
        {view === 'briefing' && (
          <Briefing
            decisions={decisions}
            resolveDecision={resolveDecision}
            seeded={seeded}
            activeTask={task}
            doneFeed={doneFeed}
            activity={activity}
            goTask={() => setView('task')}
            goReview={() => setView('review')}
          />
        )}
        {view === 'delegate' && (
          <Delegate prefill={delegatePrefill} onLaunch={launchTask} hasActiveTask={counts.taskActive > 0} />
        )}
        {view === 'task' && (
          <TaskProgress
            task={task}
            resolveGate={resolveGate}
            control={taskControl}
            finalAction={taskFinalAction}
            goDelegate={() => setView('delegate')}
            goInbox={() => setView('inbox')}
          />
        )}
        {view === 'review' && <Review drafts={drafts} draftAction={draftAction} />}
        {view === 'inbox' && (
          <Inbox emails={emails} markRead={markRead} delegateFromEmail={delegateFromEmail} log={log} />
        )}
      </main>
    </div>
  );
}
