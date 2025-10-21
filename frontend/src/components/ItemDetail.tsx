/**
 * 丝瓜条目详情模态框
 */
import React from 'react';
import { Modal, Descriptions, Tag, Button, Space, message } from 'antd';
import { CopyOutlined, LinkOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { SpongeItem } from '../services/api';

interface ItemDetailProps {
  item: SpongeItem | null;
  visible: boolean;
  onClose: () => void;
}

const ItemDetail: React.FC<ItemDetailProps> = ({ item, visible, onClose }) => {
  if (!item) return null;

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    message.success('已复制到剪贴板');
  };

  const handleApply = () => {
    if (item.job_id) {
      const applyUrl = `https://jobs.bytedance.com/campus/position/${item.job_id}/detail`;
      window.open(applyUrl, '_blank');
    }
  };

  const formatTime = (time?: string) => {
    if (!time) return '-';
    return dayjs(time).format('YYYY-MM-DD HH:mm:ss');
  };

  return (
    <Modal
      title={
        <Space>
          <span>{item.title}</span>
          {item.is_new && <Tag color="gold">新采摘</Tag>}
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width={800}
      footer={[
        <Button key="copy" icon={<CopyOutlined />} onClick={() => handleCopy(item.title)}>
          复制标题
        </Button>,
        <Button
          key="apply"
          type="primary"
          icon={<LinkOutlined />}
          onClick={handleApply}
          disabled={!item.job_id}
          style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            border: 'none',
          }}
        >
          立即申请
        </Button>,
        item.pc_job_url && (
          <Button
            key="link"
            icon={<LinkOutlined />}
            onClick={() => window.open(item.pc_job_url, '_blank')}
          >
            查看原文
          </Button>
        ),
        <Button key="close" onClick={onClose}>
          关闭
        </Button>,
      ]}
    >
      <Descriptions column={2} bordered size="small">
        <Descriptions.Item label="类型" span={1}>
          <Tag color="blue">{item.type_name}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="检测到变化时间" span={1}>
          {formatTime(item.采摘时间)}
        </Descriptions.Item>

        {item.sub_title && (
          <Descriptions.Item label="副标题" span={2}>
            {item.sub_title}
          </Descriptions.Item>
        )}

        {item.description && (
          <Descriptions.Item label="职位描述" span={2}>
            <div style={{ whiteSpace: 'pre-wrap', maxHeight: '200px', overflow: 'auto' }}>
              {item.description}
            </div>
          </Descriptions.Item>
        )}

        {item.requirement && (
          <Descriptions.Item label="任职要求" span={2}>
            <div style={{ whiteSpace: 'pre-wrap', maxHeight: '200px', overflow: 'auto' }}>
              {item.requirement}
            </div>
          </Descriptions.Item>
        )}

        {item.city_list && (
          <Descriptions.Item label="工作地点">{item.city_list}</Descriptions.Item>
        )}

        {item.job_category && (
          <Descriptions.Item label="职位类别">{item.job_category}</Descriptions.Item>
        )}

        {item.job_function && (
          <Descriptions.Item label="职位职能">{item.job_function}</Descriptions.Item>
        )}

        {item.degree && <Descriptions.Item label="学历要求">{item.degree}</Descriptions.Item>}

        {item.experience && (
          <Descriptions.Item label="经验要求">{item.experience}</Descriptions.Item>
        )}

        {(item.min_salary || item.max_salary) && (
          <Descriptions.Item label="薪资范围">
            {item.min_salary && item.max_salary
              ? `${item.min_salary / 1000}K - ${item.max_salary / 1000}K`
              : item.min_salary
              ? `${item.min_salary / 1000}K+`
              : item.max_salary ? `最高${item.max_salary / 1000}K` : '面议'}
          </Descriptions.Item>
        )}

        {item.publish_time && (
          <Descriptions.Item label="发布时间" span={2}>
            {formatTime(item.publish_time)}
          </Descriptions.Item>
        )}

        {item.code && <Descriptions.Item label="职位编码">{item.code}</Descriptions.Item>}
      </Descriptions>
    </Modal>
  );
};

export default ItemDetail;

