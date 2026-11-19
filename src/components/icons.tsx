// 轻量线性图标（stroke 风格，跟随 currentColor）
interface IconProps {
  size?: number;
}

function base(size: number) {
  return {
    width: size,
    height: size,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.8,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    'aria-hidden': true,
  };
}

export function IconGrid({ size = 18 }: IconProps) {
  return (
    <svg {...base(size)}>
      <rect x="3.5" y="3.5" width="7" height="7" rx="1.8" />
      <rect x="13.5" y="3.5" width="7" height="7" rx="1.8" />
      <rect x="3.5" y="13.5" width="7" height="7" rx="1.8" />
      <rect x="13.5" y="13.5" width="7" height="7" rx="1.8" />
    </svg>
  );
}

export function IconSparkle({ size = 18 }: IconProps) {
  return (
    <svg {...base(size)}>
      <path d="M12 3.5c.7 4.8 2.4 6.9 7 8.5-4.6 1.6-6.3 3.7-7 8.5-.7-4.8-2.4-6.9-7-8.5 4.6-1.6 6.3-3.7 7-8.5Z" />
    </svg>
  );
}

export function IconList({ size = 18 }: IconProps) {
  return (
    <svg {...base(size)}>
      <path d="M9 6h11M9 12h11M9 18h11" />
      <path d="M4 6h.01M4 12h.01M4 18h.01" strokeWidth={2.6} />
    </svg>
  );
}

export function IconMail({ size = 18 }: IconProps) {
  return (
    <svg {...base(size)}>
      <rect x="3" y="5" width="18" height="14" rx="2.5" />
      <path d="m4 7.5 8 6 8-6" />
    </svg>
  );
}

export function IconShieldCheck({ size = 18 }: IconProps) {
  return (
    <svg {...base(size)}>
      <path d="M12 3.5 5 6v5.2c0 4.4 2.9 7.4 7 9.3 4.1-1.9 7-4.9 7-9.3V6l-7-2.5Z" />
      <path d="m9 11.6 2.2 2.2L15.4 9.6" />
    </svg>
  );
}

export function IconBolt({ size = 18 }: IconProps) {
  return (
    <svg {...base(size)}>
      <path d="M13 2.8 4.8 13.4h5.7L9.6 21.2l8.2-10.6h-5.7l.9-7.8Z" />
    </svg>
  );
}

export function IconArchive({ size = 18 }: IconProps) {
  return (
    <svg {...base(size)}>
      <rect x="3" y="4.5" width="18" height="4.5" rx="1.2" />
      <path d="M5 9v10a1.5 1.5 0 0 0 1.5 1.5h11A1.5 1.5 0 0 0 19 19V9" />
      <path d="M10 13.5h4" />
    </svg>
  );
}

export function IconGear({ size = 18 }: IconProps) {
  return (
    <svg {...base(size)}>
      <circle cx="12" cy="12" r="3.2" />
      <path d="M12 2.8v3M12 18.2v3M2.8 12h3M18.2 12h3M5.2 5.2l2.1 2.1M16.7 16.7l2.1 2.1M18.8 5.2l-2.1 2.1M7.3 16.7l-2.1 2.1" />
    </svg>
  );
}

export function IconSearch({ size = 18 }: IconProps) {
  return (
    <svg {...base(size)}>
      <circle cx="11" cy="11" r="6.5" />
      <path d="m20 20-3.8-3.8" />
    </svg>
  );
}

export function IconBell({ size = 18 }: IconProps) {
  return (
    <svg {...base(size)}>
      <path d="M6 16.5v-5.2a6 6 0 1 1 12 0v5.2l1.2 2.7H4.8L6 16.5Z" />
      <path d="M10 21a2.2 2.2 0 0 0 4 0" />
    </svg>
  );
}

export function IconCheck({ size = 18 }: IconProps) {
  return (
    <svg {...base(size)}>
      <path d="m4.5 12.5 5 5 10-11" />
    </svg>
  );
}

export function IconClock({ size = 18 }: IconProps) {
  return (
    <svg {...base(size)}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.5V12l3 2" />
    </svg>
  );
}

export function IconArrowRight({ size = 18 }: IconProps) {
  return (
    <svg {...base(size)}>
      <path d="M4 12h15M14 6l6 6-6 6" />
    </svg>
  );
}

export function IconPaperclip({ size = 18 }: IconProps) {
  return (
    <svg {...base(size)}>
      <path d="m20 11.2-8.7 8.7a5.2 5.2 0 0 1-7.4-7.4l9.1-9.1a3.5 3.5 0 0 1 4.9 4.9l-8.6 8.6a1.7 1.7 0 0 1-2.4-2.4l7.4-7.4" />
    </svg>
  );
}

export function IconCalendar({ size = 18 }: IconProps) {
  return (
    <svg {...base(size)}>
      <rect x="3.5" y="5" width="17" height="16" rx="2.5" />
      <path d="M3.5 10h17M8 3v4M16 3v4" />
    </svg>
  );
}

export function IconFile({ size = 18 }: IconProps) {
  return (
    <svg {...base(size)}>
      <path d="M6 3.5h8L19 8.5v12H6v-17Z" />
      <path d="M13.5 3.5v5.5H19" />
    </svg>
  );
}

export function IconPlus({ size = 18 }: IconProps) {
  return (
    <svg {...base(size)}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

export function IconSun({ size = 18 }: IconProps) {
  return (
    <svg {...base(size)}>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2.5v2.4M12 19.1v2.4M2.5 12h2.4M19.1 12h2.4M5 5l1.7 1.7M17.3 17.3 19 19M19 5l-1.7 1.7M6.7 17.3 5 19" />
    </svg>
  );
}

export function IconMoon({ size = 18 }: IconProps) {
  return (
    <svg {...base(size)}>
      <path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z" />
    </svg>
  );
}

/** 简报决策卡与 hero 用的轨道标记（描边小图） */
export function OrbitMark({ size = 34 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <ellipse cx="24" cy="24" rx="19" ry="8.5" transform="rotate(-24 24 24)" stroke="currentColor" strokeWidth="1.6" opacity="0.75" />
      <circle cx="24" cy="24" r="5.5" fill="currentColor" />
      <circle cx="39.5" cy="13.5" r="2.4" fill="currentColor" opacity="0.85" />
    </svg>
  );
}
