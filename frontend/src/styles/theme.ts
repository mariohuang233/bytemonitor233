/**
 * 统一设计系统配置
 */

// 颜色系统
export const colors = {
  // 主色调 - 紫色渐变
  primary: {
    main: '#667eea',
    light: '#9f7aea',
    dark: '#764ba2',
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  },
  
  // 辅助色
  secondary: {
    blue: '#1890ff',
    green: '#52c41a',
    purple: '#722ed1',
    gold: '#faad14',
    red: '#ff4d4f',
  },
  
  // 中性色
  neutral: {
    white: '#ffffff',
    background: '#FAFBFC',
    cardBg: '#ffffff',
    border: '#e8e8e8',
    text: {
      primary: '#1a1a1a',
      secondary: '#666666',
      tertiary: '#999999',
    },
  },
  
  // 状态色
  status: {
    success: '#52c41a',
    warning: '#faad14',
    error: '#ff4d4f',
    info: '#1890ff',
  },
};

// 字体系统
export const typography = {
  fontFamily: {
    base: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
    mono: "'SF Mono', Monaco, 'Courier New', monospace",
  },
  
  fontSize: {
    xs: '12px',
    sm: '14px',
    base: '16px',
    lg: '18px',
    xl: '20px',
    '2xl': '24px',
    '3xl': '30px',
    '4xl': '36px',
    '5xl': '48px',
    '6xl': '56px',
  },
  
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    extrabold: 800,
  },
  
  lineHeight: {
    tight: 1.2,
    normal: 1.5,
    relaxed: 1.8,
  },
};

// 间距系统
export const spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  '2xl': '48px',
  '3xl': '64px',
  '4xl': '80px',
};

// 圆角系统
export const borderRadius = {
  sm: '4px',
  md: '8px',
  lg: '12px',
  xl: '16px',
  '2xl': '24px',
  full: '9999px',
};

// 阴影系统
export const shadows = {
  sm: '0 1px 3px rgba(0,0,0,0.08)',
  md: '0 2px 8px rgba(0,0,0,0.08)',
  lg: '0 4px 16px rgba(0,0,0,0.12)',
  xl: '0 8px 24px rgba(0,0,0,0.15)',
  '2xl': '0 16px 48px rgba(0,0,0,0.18)',
  inner: 'inset 0 2px 4px rgba(0,0,0,0.06)',
  card: '0 2px 8px rgba(0,0,0,0.08)',
  cardHover: '0 8px 24px rgba(0,0,0,0.12)',
};

// 过渡动画
export const transitions = {
  fast: '0.15s cubic-bezier(0.4, 0, 0.2, 1)',
  base: '0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  slow: '0.5s cubic-bezier(0.4, 0, 0.2, 1)',
  elastic: '0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55)',
};

// 断点系统
export const breakpoints = {
  xs: '480px',
  sm: '576px',
  md: '768px',
  lg: '992px',
  xl: '1200px',
  '2xl': '1600px',
};

// Z-index系统
export const zIndex = {
  dropdown: 1000,
  sticky: 1020,
  fixed: 1030,
  modalBackdrop: 1040,
  modal: 1050,
  popover: 1060,
  tooltip: 1070,
};

// 动画变体（用于framer-motion）
export const animations = {
  // 淡入
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
  },
  
  // 从下方滑入
  slideUp: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: 20 },
  },
  
  // 从右侧滑入
  slideRight: {
    initial: { opacity: 0, x: -20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -20 },
  },
  
  // 缩放
  scale: {
    initial: { opacity: 0, scale: 0.9 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.9 },
  },
  
  // 弹跳
  bounce: {
    initial: { opacity: 0, scale: 0.3 },
    animate: { 
      opacity: 1, 
      scale: 1,
      transition: {
        type: "spring",
        stiffness: 260,
        damping: 20,
      },
    },
    exit: { opacity: 0, scale: 0.3 },
  },
  
  // 列表项交错动画
  staggerContainer: {
    animate: {
      transition: {
        staggerChildren: 0.1,
      },
    },
  },
  
  // 列表项
  staggerItem: {
    initial: { opacity: 0, y: 20 },
    animate: { 
      opacity: 1, 
      y: 0,
      transition: {
        duration: 0.4,
      },
    },
  },
};

// 毛玻璃效果
export const glassmorphism = {
  light: {
    background: 'rgba(255, 255, 255, 0.7)',
    backdropFilter: 'blur(10px)',
    border: '1px solid rgba(255, 255, 255, 0.3)',
  },
  dark: {
    background: 'rgba(0, 0, 0, 0.3)',
    backdropFilter: 'blur(10px)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
  },
};

// 导出默认主题
export const theme = {
  colors,
  typography,
  spacing,
  borderRadius,
  shadows,
  transitions,
  breakpoints,
  zIndex,
  animations,
  glassmorphism,
};

export default theme;

