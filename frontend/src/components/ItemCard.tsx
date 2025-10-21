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

          {/* 标题 */}
          <Typography.Title level={5} style={{ margin: 0, fontSize: '16px' }}>
            {item.title}
          </Typography.Title>

          {/* 副标题 */}
          {item.sub_title && (
            <Text type="secondary" style={{ fontSize: '13px' }}>
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

          {/* 底部信息 */}
          <Space split={<span style={{ color: '#d9d9d9' }}>|</span>} size="small" wrap>
            {item.采摘时间 && (
              <Text type="secondary" style={{ fontSize: '12px' }}>
                <ClockCircleOutlined /> {formatTime(item.采摘时间)}
              </Text>
            )}
            {item.city_list && (
              <Text type="secondary" style={{ fontSize: '12px' }}>
                <EnvironmentOutlined /> {item.city_list}
              </Text>
            )}
            {item.job_category && (
              <Tag color="default" style={{ fontSize: '11px', margin: 0 }}>
                {item.job_category}
              </Tag>
            )}
          </Space>

          {/* 申请按钮 */}
          <div style={{ textAlign: 'center', paddingTop: '12px', borderTop: '1px solid #f0f0f0' }}>
            <Button
              type="primary"
              size="small"
              icon={<LinkOutlined />}
              onClick={handleApply}
              style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                border: 'none',
                borderRadius: '6px',
                fontWeight: 500,
              }}
              disabled={!item.job_id}
            >
              立即申请
            </Button>
          </div>
        </Space>
      </Card>
    </Badge.Ribbon>
  );
};

export default ItemCard;

