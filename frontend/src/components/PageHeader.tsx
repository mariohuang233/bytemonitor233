/**
 * 统一页面头部组件
 */
import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button, Space, Typography } from 'antd';
import { ArrowLeftOutlined, HomeOutlined } from '@ant-design/icons';
import { motion } from 'framer-motion';
import theme from '../styles/theme';

const { Title } = Typography;

interface PageHeaderProps {
  title?: string;
  subtitle?: string;
  showBack?: boolean;
  showHome?: boolean;
  extra?: React.ReactNode;
  style?: React.CSSProperties;
}

const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  showBack = false,
  showHome = false,
  extra,
  style,
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const isHome = location.pathname === '/';

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      style={{
        background: 'white',
        borderBottom: `1px solid ${theme.colors.neutral.border}`,
        padding: `${theme.spacing.lg} 0`,
        ...style,
      }}
    >
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: `0 ${theme.spacing.lg}` }}>
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          {/* 导航按钮 */}
          {(showBack || showHome) && (
            <Space size="small">
              {showBack && (
                <Button
                  icon={<ArrowLeftOutlined />}
                  onClick={() => navigate(-1)}
                  type="text"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    fontSize: theme.typography.fontSize.base,
                    color: theme.colors.neutral.text.secondary,
                    transition: theme.transitions.base,
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.color = theme.colors.primary.main;
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.color = theme.colors.neutral.text.secondary;
                  }}
                >
                  返回
                </Button>
              )}
              
              {showHome && !isHome && (
                <Button
                  icon={<HomeOutlined />}
                  onClick={() => navigate('/')}
                  type="text"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    fontSize: theme.typography.fontSize.base,
                    color: theme.colors.neutral.text.secondary,
                    transition: theme.transitions.base,
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.color = theme.colors.primary.main;
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.color = theme.colors.neutral.text.secondary;
                  }}
                >
                  首页
                </Button>
              )}
            </Space>
          )}

          {/* 标题区域 */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              {title && (
                <Title
                  level={2}
                  style={{
                    margin: 0,
                    fontSize: theme.typography.fontSize['3xl'],
                    fontWeight: theme.typography.fontWeight.bold,
                    color: theme.colors.neutral.text.primary,
                    background: theme.colors.primary.gradient,
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                  }}
                >
                  {title}
                </Title>
              )}
              {subtitle && (
                <Typography.Text
                  style={{
                    display: 'block',
                    marginTop: theme.spacing.sm,
                    fontSize: theme.typography.fontSize.base,
                    color: theme.colors.neutral.text.secondary,
                  }}
                >
                  {subtitle}
                </Typography.Text>
              )}
            </div>
            
            {extra && <div>{extra}</div>}
          </div>
        </Space>
      </div>
    </motion.div>
  );
};

export default PageHeader;

