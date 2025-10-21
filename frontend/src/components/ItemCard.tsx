/**
 * 丝瓜条目卡片组件
 */
import React from 'react';
import { Card, Tag, Badge, Space, Typography, Button } from 'antd';
import {
  ClockCircleOutlined,
  EnvironmentOutlined,
  StarOutlined,
  LinkOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { SpongeItem } from '../services/api';

const { Text, Paragraph } = Typography;

interface ItemCardProps {
  item: SpongeItem;
  onClick?: () => void;
}

const ItemCard: React.FC<ItemCardProps> = ({ item, onClick }) => {
  const getTypeColor = (typeName: string) => {
    const colors: Record<string, string> = {
      '新丝瓜': '#52c41a',
      '生丝瓜': '#1890ff',
      '熟丝瓜': '#722ed1',
    };
    return colors[typeName] || '#1890ff';
  };

  const formatTime = (time?: string) => {
    if (!time) return '';
    return dayjs(time).format('YYYY-MM-DD HH:mm');
  };

  const handleApply = (e: React.MouseEvent) => {
    e.stopPropagation(); // 防止触发卡片点击
    if (item.job_id) {
      const applyUrl = `https://jobs.bytedance.com/campus/position/${item.job_id}/detail`;
      window.open(applyUrl, '_blank');
    }
  };

  return (
    <Badge.Ribbon
      text={item.is_new ? '新采摘' : null}
      color="#faad14"
      style={{ display: item.is_new ? 'block' : 'none' }}
    >
      <Card
        hoverable
        onClick={onClick}
        style={{
          height: '100%',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
          transition: 'all 0.3s ease',
        }}
        styles={{
          body: { padding: '20px' },
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateY(-4px)';
          e.currentTarget.style.boxShadow = '0 4px 20px rgba(0,0,0,0.12)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)';
        }}
      >
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {/* 类型标签 */}
          <div>
            <Tag color={getTypeColor(item.type_name)} style={{ marginBottom: 8 }}>
              {item.type_name}
            </Tag>
            {item.is_new && (
              <Tag icon={<StarOutlined />} color="gold">
                新鲜
              </Tag>
            )}
          </div>

          {/* 标题 - 加粗黑体，大字号 */}
          <Typography.Title
            level={5}
            style={{
              margin: 0,
              fontSize: '20px',
              fontWeight: 800,
              color: '#1a1a1a',
              lineHeight: 1.3,
            }}
          >
            {item.title}
          </Typography.Title>

          {/* 副标题 */}
          {item.sub_title && (
            <Text type="secondary" style={{ fontSize: '14px', lineHeight: 1.5 }}>
              {item.sub_title}
            </Text>
          )}

          {/* 描述（截断） */}
          {item.description && (
            <Paragraph
              ellipsis={{ rows: 2 }}
              style={{ margin: 0, color: '#666', fontSize: '13px' }}
            >
              {item.description}
            </Paragraph>
          )}

          {/* 标签区 - pill样式 */}
          <Space size={[8, 8]} wrap>
            {item.job_category && (
              <span
                style={{
                  background: '#f0f0f0',
                  color: '#666',
                  padding: '6px 14px',
                  borderRadius: '16px',
                  fontSize: '12px',
                  fontWeight: 500,
                }}
              >
                {item.job_category}
              </span>
            )}
            {item.city_list && (
              <span
                style={{
                  background: '#f0f0f0',
                  color: '#666',
                  padding: '6px 14px',
                  borderRadius: '16px',
                  fontSize: '12px',
                  fontWeight: 500,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                <EnvironmentOutlined style={{ fontSize: '12px' }} />
                {item.city_list}
              </span>
            )}
          </Space>

          {/* 采摘时间 - 最后一次检测到变化的时间 */}
          {item.采摘时间 && (
            <Text type="secondary" style={{ fontSize: '11px', opacity: 0.6 }}>
              <ClockCircleOutlined style={{ marginRight: '4px' }} />
              检测到变化 {formatTime(item.采摘时间)}
            </Text>
          )}

          {/* Apply now按钮 - 黑底白字 */}
          <div style={{ paddingTop: '16px' }}>
            <Button
              type="primary"
              block
              size="large"
              icon={<LinkOutlined />}
              onClick={handleApply}
              disabled={!item.job_id}
              style={{
                background: '#1a1a1a',
                border: 'none',
                borderRadius: '12px',
                height: '48px',
                fontWeight: 600,
                fontSize: '15px',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              }}
              onMouseEnter={(e) => {
                if (item.job_id) {
                  e.currentTarget.style.background = '#333';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.2)';
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = '#1a1a1a';
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              Apply Now
            </Button>
          </div>
        </Space>
      </Card>
    </Badge.Ribbon>
  );
};

export default ItemCard;

