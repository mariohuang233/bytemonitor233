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
import { SearchOutlined, SyncOutlined, BarChartOutlined, HomeOutlined } from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import ItemCard from '../components/ItemCard';
import ItemDetail from '../components/ItemDetail';
import Dashboard from '../components/Dashboard';
import PageHeader from '../components/PageHeader';
import { getItems, triggerSync, getSyncStatus, type SpongeItem } from '../services/api';
import theme from '../styles/theme';
import { useNavigate, useLocation } from 'react-router-dom';

const { Header, Content } = Layout;
const { TabPane } = Tabs;
const { Search } = Input;

const Home: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
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
  
  // 从URL参数获取搜索关键词
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const searchParam = params.get('search');
    if (searchParam) {
      setSearchKeyword(searchParam);
    }
  }, [location.search]);

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
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Layout style={{ minHeight: '100vh', background: theme.colors.neutral.background }}>
        {/* 统一头部 */}
        <PageHeader
          title="职位清单"
          subtitle="探索精选职位机会"
          showHome={true}
          extra={
            <Space>
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button
                  icon={<BarChartOutlined />}
                  type={showDashboard ? 'primary' : 'default'}
                  onClick={() => setShowDashboard(!showDashboard)}
                  style={{
                    borderRadius: theme.borderRadius.lg,
                    transition: theme.transitions.base,
                  }}
                >
                  {showDashboard ? '返回列表' : '数据统计'}
                </Button>
              </motion.div>
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button
                  icon={<SyncOutlined spin={syncing} />}
                  onClick={handleSync}
                  loading={syncing}
                  disabled={syncing}
                  style={{
                    borderRadius: theme.borderRadius.lg,
                    transition: theme.transitions.base,
                  }}
                >
                  同步数据
                </Button>
              </motion.div>
            </Space>
          }
        />
        
        {/* 同步进度条 */}
        <AnimatePresence>
          {syncing && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              style={{ background: 'white', borderBottom: `1px solid ${theme.colors.neutral.border}` }}
            >
              <div style={{ maxWidth: '1200px', margin: '0 auto', padding: `${theme.spacing.sm} ${theme.spacing.lg}` }}>
                <Progress
                  percent={syncProgress}
                  status={syncProgress === 100 ? 'success' : 'active'}
                  strokeColor={theme.colors.primary.gradient}
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 主内容区 */}
        <Content style={{ padding: theme.spacing.lg, maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
          <AnimatePresence mode="wait">
            {showDashboard ? (
              <motion.div
                key="dashboard"
                {...theme.animations.fadeIn}
                transition={{ duration: 0.4 }}
              >
                <Dashboard />
              </motion.div>
            ) : (
              <motion.div
                key="list"
                {...theme.animations.fadeIn}
                transition={{ duration: 0.4 }}
              >
                {/* 搜索栏 */}
                <motion.div
                  initial={{ y: -20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.1 }}
                  style={{ marginBottom: theme.spacing.lg }}
                >
                  <Search
                    placeholder="搜索职位、技能、公司..."
                    allowClear
                    enterButton={<SearchOutlined />}
                    size="large"
                    onSearch={handleSearch}
                    value={searchKeyword}
                    onChange={(e) => setSearchKeyword(e.target.value)}
                    style={{ 
                      maxWidth: '600px',
                    }}
                  />
                </motion.div>

                {/* 标签页 */}
                <motion.div
                  initial={{ y: -20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.2 }}
                >
                  <Tabs 
                    activeKey={activeTab} 
                    onChange={handleTabChange} 
                    size="large"
                    style={{
                      marginBottom: theme.spacing.lg,
                    }}
                  >
                    <TabPane tab="全部" key="all" />
                    <TabPane tab="新丝瓜（实习）" key="intern" />
                    <TabPane tab="生丝瓜（校招）" key="campus" />
                    <TabPane tab="熟丝瓜（社招）" key="experienced" />
                  </Tabs>
                </motion.div>

                {/* 内容展示 */}
                <AnimatePresence mode="wait">
                  {loading ? (
                    <motion.div
                      key="loading"
                      {...theme.animations.fadeIn}
                      style={{ textAlign: 'center', padding: '100px 0' }}
                    >
                      <Spin size="large" />
                    </motion.div>
                  ) : items.length === 0 ? (
                    <motion.div
                      key="empty"
                      {...theme.animations.scale}
                      style={{ padding: '100px 0' }}
                    >
                      <Empty description="暂无数据" />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="content"
                      variants={theme.animations.staggerContainer}
                      initial="initial"
                      animate="animate"
                    >
                      <Row gutter={[16, 16]}>
                        {items.map((item, index) => (
                          <Col key={item._id} xs={24} sm={12} lg={8} xl={6}>
                            <motion.div
                              variants={theme.animations.staggerItem}
                              custom={index}
                            >
                              <ItemCard item={item} onClick={() => handleItemClick(item)} />
                            </motion.div>
                          </Col>
                        ))}
                      </Row>

                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        style={{ textAlign: 'center', marginTop: theme.spacing.xl }}
                      >
                        <Pagination
                          current={page}
                          total={total}
                          pageSize={pageSize}
                          onChange={(newPage) => setPage(newPage)}
                          showSizeChanger={false}
                          showTotal={(total) => `共 ${total} 条`}
                        />
                      </motion.div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )}
          </AnimatePresence>
        </Content>

        {/* 详情弹窗 */}
        <ItemDetail
          item={selectedItem}
          visible={detailVisible}
          onClose={() => {
            setDetailVisible(false);
            setSelectedItem(null);
          }}
        />
      </Layout>
    </motion.div>
  );
};

export default Home;

