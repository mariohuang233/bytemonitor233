/**
 * Landing页面 - 主页
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Row, Col, Input, Button, Card, Statistic, Avatar, Typography, Space } from 'antd';
import {
  SearchOutlined,
  RiseOutlined,
  TeamOutlined,
  CheckCircleOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons';
import { getStats, getItems, type SpongeItem } from '../services/api';
import ItemCard from '../components/ItemCard';

const { Search } = Input;
const { Title, Paragraph, Text } = Typography;

const Landing: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<any>(null);
  const [featuredJobs, setFeaturedJobs] = useState<SpongeItem[]>([]);
  const [searchValue, setSearchValue] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // 加载统计数据
      const statsResult = await getStats();
      if (statsResult.success) {
        setStats(statsResult.data);
      }

      // 加载推荐职位（最新3条）
      const jobsResult = await getItems({ page: 1, limit: 3 });
      if (jobsResult.success) {
        setFeaturedJobs(jobsResult.data.items);
      }
    } catch (error) {
      console.error('加载数据失败:', error);
    }
  };

  const handleSearch = (value: string) => {
    navigate(`/jobs?search=${encodeURIComponent(value)}`);
  };

  const handleExploreAll = () => {
    navigate('/jobs');
  };

  // 推荐公司
  const companies = [
    { name: 'ByteDance', logo: '🚀', tagline: 'Inspire Creativity, Enrich Life' },
    { name: 'TikTok', logo: '🎵', tagline: 'Make Your Day' },
    { name: 'Lark', logo: '🕊️', tagline: 'Advanced Collaboration' },
  ];

  return (
    <div style={{ background: '#FAFBFC', minHeight: '100vh', overflow: 'hidden' }}>
      {/* Hero Section - 左大右小 */}
      <section
        style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          padding: '80px 0 120px',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* 装饰元素 */}
        <div
          style={{
            position: 'absolute',
            top: '10%',
            right: '5%',
            width: '400px',
            height: '400px',
            background: 'rgba(255,255,255,0.1)',
            borderRadius: '50%',
            filter: 'blur(100px)',
          }}
        />

        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 24px' }}>
          <Row gutter={[48, 48]} align="middle">
            {/* 左侧：主文案 + 搜索 */}
            <Col xs={24} lg={14}>
              <div style={{ position: 'relative', zIndex: 1 }}>
                <Title
                  level={1}
                  style={{
                    color: 'white',
                    fontSize: '56px',
                    fontWeight: 800,
                    lineHeight: 1.2,
                    marginBottom: '24px',
                    textShadow: '0 4px 20px rgba(0,0,0,0.1)',
                  }}
                >
                  Your Dream Career
                  <br />
                  Starts Here 🚀
                </Title>

                <Paragraph
                  style={{
                    color: 'rgba(255,255,255,0.9)',
                    fontSize: '18px',
                    marginBottom: '40px',
                    lineHeight: 1.6,
                  }}
                >
                  探索字节跳动全球职位，发现最适合你的机会。
                  <br />
                  实习、校招、社招，总有一个适合你。
                </Paragraph>

                {/* 搜索框 */}
                <Search
                  placeholder="搜索职位、技能、地点..."
                  size="large"
                  value={searchValue}
                  onChange={(e) => setSearchValue(e.target.value)}
                  onSearch={handleSearch}
                  enterButton={
                    <Button
                      type="primary"
                      size="large"
                      icon={<SearchOutlined />}
                      style={{
                        background: '#1a1a1a',
                        border: 'none',
                        height: '56px',
                        fontSize: '16px',
                        fontWeight: 600,
                      }}
                    >
                      Search
                    </Button>
                  }
                  style={{
                    maxWidth: '600px',
                  }}
                  styles={{
                    input: {
                      height: '56px',
                      fontSize: '16px',
                      borderRadius: '12px 0 0 12px',
                      border: 'none',
                      boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
                    },
                  }}
                />

                {/* 统计数据 */}
                <Row gutter={24} style={{ marginTop: '60px' }}>
                  <Col span={8}>
                    <Statistic
                      title={
                        <span style={{ color: 'rgba(255,255,255,0.8)', fontSize: '14px' }}>
                          Total Jobs
                        </span>
                      }
                      value={stats?.total || 0}
                      suffix="+"
                      valueStyle={{ color: 'white', fontSize: '32px', fontWeight: 700 }}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title={
                        <span style={{ color: 'rgba(255,255,255,0.8)', fontSize: '14px' }}>
                          New This Week
                        </span>
                      }
                      value={stats?.week_new || 0}
                      prefix={<RiseOutlined />}
                      valueStyle={{ color: '#52c41a', fontSize: '32px', fontWeight: 700 }}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title={
                        <span style={{ color: 'rgba(255,255,255,0.8)', fontSize: '14px' }}>
                          Categories
                        </span>
                      }
                      value={3}
                      valueStyle={{ color: 'white', fontSize: '32px', fontWeight: 700 }}
                    />
                  </Col>
                </Row>
              </div>
            </Col>

            {/* 右侧：动态卡片预览 */}
            <Col xs={24} lg={10}>
              <div
                style={{
                  position: 'relative',
                  height: '500px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {/* 装饰性手机框架 */}
                <div
                  style={{
                    position: 'absolute',
                    width: '300px',
                    height: '450px',
                    background: 'rgba(255,255,255,0.15)',
                    backdropFilter: 'blur(20px)',
                    borderRadius: '32px',
                    border: '2px solid rgba(255,255,255,0.3)',
                    boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
                    padding: '20px',
                    animation: 'float 3s ease-in-out infinite',
                  }}
                >
                  <div
                    style={{
                      background: 'white',
                      borderRadius: '20px',
                      height: '100%',
                      padding: '20px',
                      overflow: 'hidden',
                    }}
                  >
                    {featuredJobs[0] && (
                      <div style={{ transform: 'scale(0.85)', transformOrigin: 'top left' }}>
                        <Text strong style={{ fontSize: '16px', display: 'block', marginBottom: '8px' }}>
                          {featuredJobs[0].title}
                        </Text>
                        <Space size="small" wrap style={{ marginBottom: '12px' }}>
                          <span
                            style={{
                              background: '#f0f0f0',
                              padding: '4px 12px',
                              borderRadius: '12px',
                              fontSize: '12px',
                            }}
                          >
                            {featuredJobs[0].type_name}
                          </span>
                          {featuredJobs[0].city_list && (
                            <span
                              style={{
                                background: '#f0f0f0',
                                padding: '4px 12px',
                                borderRadius: '12px',
                                fontSize: '12px',
                              }}
                            >
                              {featuredJobs[0].city_list}
                            </span>
                          )}
                        </Space>
                        <Button
                          type="primary"
                          block
                          style={{
                            background: '#1a1a1a',
                            border: 'none',
                            borderRadius: '8px',
                            height: '40px',
                            fontWeight: 600,
                            marginTop: '12px',
                          }}
                        >
                          Apply Now
                        </Button>
                      </div>
                    )}
                  </div>
                </div>

                {/* 装饰线条 */}
                <svg
                  style={{
                    position: 'absolute',
                    top: '-20%',
                    right: '-20%',
                    width: '200px',
                    opacity: 0.6,
                  }}
                  viewBox="0 0 200 200"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M 50 50 Q 100 20, 150 50 T 200 100"
                    stroke="#B388FF"
                    strokeWidth="3"
                    fill="none"
                    strokeDasharray="5,5"
                  />
                  <circle cx="150" cy="50" r="8" fill="#B388FF" />
                  <circle cx="200" cy="100" r="6" fill="#64B5F6" />
                </svg>
              </div>
            </Col>
          </Row>
        </div>

        {/* CSS动画 */}
        <style>{`
          @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
          }
        `}</style>
      </section>

      {/* Featured Jobs Section */}
      <section style={{ padding: '80px 0', background: 'white' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 24px' }}>
          <div style={{ textAlign: 'center', marginBottom: '60px' }}>
            <Title level={2} style={{ fontSize: '40px', fontWeight: 700, marginBottom: '16px' }}>
              Explore and Find Your Job Here
            </Title>
            <Paragraph style={{ fontSize: '16px', color: '#666', maxWidth: '600px', margin: '0 auto' }}>
              精选最新职位，为你量身定制职业道路
            </Paragraph>
          </div>

          <Row gutter={[24, 24]}>
            {featuredJobs.map((job) => (
              <Col key={job._id} xs={24} md={12} lg={8}>
                <ItemCard item={job} onClick={() => navigate('/jobs')} />
              </Col>
            ))}
          </Row>

          <div style={{ textAlign: 'center', marginTop: '40px' }}>
            <Button
              size="large"
              onClick={handleExploreAll}
              style={{
                height: '48px',
                padding: '0 40px',
                fontSize: '16px',
                fontWeight: 600,
                borderRadius: '24px',
                border: '2px solid #667eea',
                color: '#667eea',
              }}
            >
              Explore All Jobs <ArrowRightOutlined />
            </Button>
          </div>
        </div>
      </section>

      {/* Companies Section */}
      <section
        style={{
          padding: '80px 0',
          background: 'linear-gradient(180deg, #F7F9FC 0%, #FAFBFC 100%)',
        }}
      >
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 24px' }}>
          <div style={{ textAlign: 'center', marginBottom: '60px' }}>
            <div
              style={{
                display: 'inline-block',
                background: '#B388FF',
                color: 'white',
                padding: '8px 24px',
                borderRadius: '20px',
                fontSize: '14px',
                fontWeight: 600,
                marginBottom: '20px',
              }}
            >
              Best Places to Work 2024
            </div>
            <Title level={2} style={{ fontSize: '36px', fontWeight: 700 }}>
              Top Companies Hiring
            </Title>
          </div>

          <Row gutter={[24, 24]}>
            {companies.map((company, index) => (
              <Col key={index} xs={24} sm={12} md={8}>
                <Card
                  hoverable
                  style={{
                    borderRadius: '16px',
                    border: 'none',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                    transition: 'all 0.3s ease',
                  }}
                  styles={{
                    body: { padding: '32px', textAlign: 'center' },
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-8px)';
                    e.currentTarget.style.boxShadow = '0 12px 24px rgba(0,0,0,0.12)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)';
                  }}
                >
                  <Avatar
                    size={80}
                    style={{
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      fontSize: '40px',
                      marginBottom: '16px',
                    }}
                  >
                    {company.logo}
                  </Avatar>
                  <Title level={4} style={{ marginBottom: '8px' }}>
                    {company.name}
                  </Title>
                  <Text type="secondary" style={{ fontSize: '14px' }}>
                    {company.tagline}
                  </Text>
                </Card>
              </Col>
            ))}
          </Row>
        </div>
      </section>
    </div>
  );
};

export default Landing;

