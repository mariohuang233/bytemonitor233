/**
 * 主页面 - 列表展示
 */
import React, { useState, useEffect } from 'react';
import {
  Layout,
  Tabs,
  Input,
  Row,
  Col,
  Pagination,
  Empty,
  Spin,
  Button,
  Space,
  message,
  Progress,
} from 'antd';
import { SearchOutlined, SyncOutlined, BarChartOutlined } from '@ant-design/icons';
import ItemCard from '../components/ItemCard';
import ItemDetail from '../components/ItemDetail';
import Dashboard from '../components/Dashboard';
import { getItems, triggerSync, getSyncStatus, type SpongeItem } from '../services/api';

const { Header, Content } = Layout;
const { TabPane } = Tabs;
const { Search } = Input;

const Home: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('all');
  const [searchKeyword, setSearchKeyword] = useState<string>('');
  const [items, setItems] = useState<SpongeItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(20);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedItem, setSelectedItem] = useState<SpongeItem | null>(null);
  const [detailVisible, setDetailVisible] = useState<boolean>(false);
  const [syncing, setSyncing] = useState<boolean>(false);
  const [syncProgress, setSyncProgress] = useState<number>(0);
  const [showDashboard, setShowDashboard] = useState<boolean>(false);

  // 加载数据
  useEffect(() => {
    loadData();
  }, [activeTab, page, searchKeyword]);

  const loadData = async () => {
    try {
      setLoading(true);
      const typeMap: Record<string, string | undefined> = {
        all: undefined,
        intern: 'intern',
        campus: 'campus',
        experienced: 'experienced',
      };

      const result = await getItems({
        type: typeMap[activeTab],
        page,
        limit: pageSize,
        search: searchKeyword || undefined,
      });

      if (result.success) {
        setItems(result.data.items);
        setTotal(result.data.total);
      }
    } catch (error) {
      console.error('加载数据失败:', error);
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 触发同步
  const handleSync = async () => {
    try {
      setSyncing(true);
      setSyncProgress(10);
      const result = await triggerSync();

      if (result.success) {
        message.success('同步已启动');

        // 轮询同步状态
        const checkStatus = setInterval(async () => {
          try {
            const statusResult = await getSyncStatus();
            if (statusResult.success) {
              setSyncProgress(statusResult.data.progress);

              if (!statusResult.data.running) {
                clearInterval(checkStatus);
                setSyncing(false);
                setSyncProgress(0);

                if (statusResult.data.progress === 100) {
                  message.success('同步完成！');
                  loadData(); // 重新加载数据
                } else {
                  message.error(statusResult.data.message || '同步失败');
                }
              }
            }
          } catch (err) {
            console.error('获取同步状态失败:', err);
          }
        }, 2000);

        // 最多等待5分钟
        setTimeout(() => {
          clearInterval(checkStatus);
          if (syncing) {
            setSyncing(false);
            setSyncProgress(0);
            message.warning('同步超时，请检查日志');
          }
        }, 300000);
      }
    } catch (error) {
      console.error('触发同步失败:', error);
      message.error('触发同步失败');
      setSyncing(false);
      setSyncProgress(0);
    }
  };

  // 搜索
  const handleSearch = (value: string) => {
    setSearchKeyword(value);
    setPage(1);
  };

  // 切换标签
  const handleTabChange = (key: string) => {
    setActiveTab(key);
    setPage(1);
  };

  // 打开详情
  const handleItemClick = (item: SpongeItem) => {
    setSelectedItem(item);
    setDetailVisible(true);
  };

  // 渲染内容
  const renderContent = () => {
    if (showDashboard) {
      return <Dashboard />;
    }

    if (loading) {
      return (
        <div style={{ textAlign: 'center', padding: '100px 0' }}>
          <Spin size="large" />
        </div>
      );
    }

    if (items.length === 0) {
      return (
        <div style={{ padding: '100px 0' }}>
          <Empty description="暂无数据" />
        </div>
      );
    }

    return (
      <>
        <Row gutter={[16, 16]}>
          {items.map((item) => (
            <Col key={item._id} xs={24} sm={12} lg={8} xl={6}>
              <ItemCard item={item} onClick={() => handleItemClick(item)} />
            </Col>
          ))}
        </Row>

        <div style={{ textAlign: 'center', marginTop: '32px' }}>
          <Pagination
            current={page}
            total={total}
            pageSize={pageSize}
            onChange={(newPage) => setPage(newPage)}
            showSizeChanger={false}
            showTotal={(total) => `共 ${total} 条`}
          />
        </div>
      </>
    );
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f7fa' }}>
      {/* 头部 */}
      <Header
        style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        }}
      >
        <h1 style={{ color: 'white', margin: 0, fontSize: '24px' }}>
          🥒 丝瓜清单管理系统
        </h1>

        <Space>
          <Button
            icon={<BarChartOutlined />}
            onClick={() => setShowDashboard(!showDashboard)}
            style={{ color: 'white', borderColor: 'white' }}
          >
            {showDashboard ? '列表视图' : '统计视图'}
          </Button>

          <Button
            type="primary"
            icon={<SyncOutlined spin={syncing} />}
            onClick={handleSync}
            loading={syncing}
            disabled={syncing}
            style={{ background: '#52c41a', borderColor: '#52c41a' }}
          >
            {syncing ? `同步中 ${syncProgress}%` : '同步数据'}
          </Button>
        </Space>
      </Header>

      {/* 同步进度条 */}
      {syncing && (
        <Progress
          percent={syncProgress}
          status="active"
          showInfo={false}
          strokeColor={{ from: '#108ee9', to: '#87d068' }}
        />
      )}

      {/* 内容区 */}
      <Content style={{ padding: '24px' }}>
        {!showDashboard && (
          <>
            {/* 搜索和标签 */}
            <div style={{ marginBottom: '24px' }}>
              <Search
                placeholder="搜索标题、描述、要求..."
                allowClear
                enterButton={<SearchOutlined />}
                size="large"
                onSearch={handleSearch}
                style={{ marginBottom: '16px' }}
              />

              <Tabs activeKey={activeTab} onChange={handleTabChange} size="large">
                <TabPane tab="全部" key="all" />
                <TabPane tab="🌱 新丝瓜" key="intern" />
                <TabPane tab="🌿 生丝瓜" key="campus" />
                <TabPane tab="🥒 熟丝瓜" key="experienced" />
              </Tabs>
            </div>
          </>
        )}

        {/* 列表/仪表盘 */}
        {renderContent()}
      </Content>

      {/* 详情模态框 */}
      <ItemDetail
        item={selectedItem}
        visible={detailVisible}
        onClose={() => {
          setDetailVisible(false);
          setSelectedItem(null);
        }}
      />
    </Layout>
  );
};

export default Home;

