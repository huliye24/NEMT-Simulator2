/**
 * Copyright 2026 NEMT Lab
 *
 * Notion 风格的文档阅读器组件
 * 横向布局：左侧目录 + 右侧内容
 */

import React, { useState, useEffect, useRef, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { BookOpen, Sun, Moon, ChevronRight, Menu, X } from 'lucide-react';

interface TOCItem {
  id: string;
  text: string;
  level: 1 | 2;
}

interface DocReaderProps {
  content: string;
  title?: string;
}

export function DocReader({ content, title }: DocReaderProps) {
  const [isDark, setIsDark] = useState(true);
  const [showSidebar, setShowSidebar] = useState(true);
  const [activeId, setActiveId] = useState<string>('');
  const [scrollProgress, setScrollProgress] = useState(0);
  const contentRef = useRef<HTMLDivElement>(null);

  // 解析目录
  const toc = useMemo<TOCItem[]>(() => {
    const lines = content.split('\n');
    const items: TOCItem[] = [];

    lines.forEach((line) => {
      const h1Match = line.match(/^#\s+(.+)$/);
      const h2Match = line.match(/^##\s+(.+)$/);

      if (h1Match) {
        const text = h1Match[1].trim();
        items.push({ id: textToId(text), text, level: 1 });
      } else if (h2Match) {
        const text = h2Match[1].trim();
        items.push({ id: textToId(text), text, level: 2 });
      }
    });

    return items;
  }, [content]);

  // 滚动监听
  useEffect(() => {
    const handleScroll = () => {
      const el = contentRef.current;
      if (!el) return;

      const scrollTop = el.scrollTop;
      const scrollHeight = el.scrollHeight - el.clientHeight;
      const progress = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;
      setScrollProgress(progress);
    };

    const contentEl = contentRef.current;
    contentEl?.addEventListener('scroll', handleScroll);
    return () => contentEl?.removeEventListener('scroll', handleScroll);
  }, []);

  // 观察当前可见章节
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id);
          }
        });
      },
      { root: contentRef.current, rootMargin: '-20% 0px -60% 0px' }
    );

    toc.forEach((item) => {
      const el = document.getElementById(item.id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, [toc]);

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  // 处理 Markdown 内容，添加 id 给标题
  const processedContent = useMemo(() => {
    return content
      .replace(/^### (.+)$/gm, (_, text) => `### <span id="${textToId(text.trim())}">${text}</span>`)
      .replace(/^## (.+)$/gm, (_, text) => `## <span id="${textToId(text.trim())}">${text}</span>`)
      .replace(/^# (.+)$/gm, (_, text) => `# <span id="${textToId(text.trim())}">${text}</span>`);
  }, [content]);

  return (
    <div
      data-theme={isDark ? 'dark' : 'light'}
      style={{
        display: 'flex',
        height: '100%',
        background: isDark ? '#0f172a' : '#ffffff',
        color: isDark ? '#e2e8f0' : '#1e293b',
        transition: 'background 0.3s, color 0.3s',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* 左侧目录 */}
      <aside
        style={{
          width: showSidebar ? '240px' : '0',
          minWidth: showSidebar ? '240px' : '0',
          height: '100%',
          overflow: 'hidden',
          background: isDark ? '#1e293b' : '#f8fafc',
          borderRight: `1px solid ${isDark ? '#334155' : '#e2e8f0'}`,
          transition: 'width 0.3s, min-width 0.3s',
          display: 'flex',
          flexDirection: 'column',
          flexShrink: 0
        }}
      >
        {/* 目录头部 */}
        <div style={{
          padding: '16px',
          borderBottom: `1px solid ${isDark ? '#334155' : '#e2e8f0'}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BookOpen size={16} style={{ color: '#8b5cf6' }} />
            <span style={{ fontSize: '13px', fontWeight: '600' }}>
              {title || '目录'}
            </span>
          </div>
          <button
            onClick={() => setIsDark(!isDark)}
            style={{
              padding: '6px',
              borderRadius: '6px',
              border: 'none',
              background: isDark ? '#334155' : '#e2e8f0',
              color: isDark ? '#94a3b8' : '#64748b',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            {isDark ? <Sun size={14} /> : <Moon size={14} />}
          </button>
        </div>

        {/* 目录列表 */}
        <nav style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
          {toc.map((item) => (
            <button
              key={item.id}
              onClick={() => scrollToSection(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                width: '100%',
                textAlign: 'left',
                padding: item.level === 1 ? '8px 12px' : '6px 12px 6px 20px',
                marginBottom: '2px',
                borderRadius: '6px',
                border: 'none',
                background: activeId === item.id
                  ? (isDark ? '#8b5cf620' : '#8b5cf610')
                  : 'transparent',
                color: activeId === item.id
                  ? '#a78bfa'
                  : (isDark ? '#94a3b8' : '#64748b'),
                cursor: 'pointer',
                fontSize: item.level === 1 ? '13px' : '12px',
                fontWeight: item.level === 1 ? '600' : '400',
                transition: 'all 0.15s'
              }}
            >
              {item.level === 2 && (
                <ChevronRight size={10} style={{ marginRight: '4px', opacity: 0.5, flexShrink: 0 }} />
              )}
              <span style={{
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}>
                {item.text}
              </span>
            </button>
          ))}
        </nav>
      </aside>

      {/* 主内容区 */}
      <main
        ref={contentRef}
        style={{
          flex: 1,
          height: '100%',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {/* 阅读进度条 */}
        <div
          style={{
            height: '3px',
            background: isDark ? '#1e293b' : '#e2e8f0',
            flexShrink: 0
          }}
        >
          <div
            style={{
              height: '100%',
              width: `${scrollProgress}%`,
              background: 'linear-gradient(90deg, #8b5cf6, #6366f1)',
              transition: 'width 0.1s'
            }}
          />
        </div>

        {/* 侧边栏切换按钮 */}
        <button
          onClick={() => setShowSidebar(!showSidebar)}
          style={{
            position: 'absolute',
            top: '12px',
            left: '12px',
            zIndex: 10,
            padding: '6px',
            borderRadius: '6px',
            border: 'none',
            background: isDark ? '#1e293b' : '#f1f5f9',
            color: isDark ? '#94a3b8' : '#64748b',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          {showSidebar ? <X size={16} /> : <Menu size={16} />}
        </button>

        {/* 内容 */}
        <div style={{
          maxWidth: '800px',
          width: '100%',
          margin: '0 auto',
          padding: '40px 48px'
        }}>
          <article className="doc-content">
            <style>{`
              .doc-content {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                font-size: 15px;
                line-height: 1.8;
                color: ${isDark ? '#e2e8f0' : '#1e293b'};
              }
              .doc-content h1 {
                font-size: 28px;
                font-weight: 700;
                margin: 0 0 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid ${isDark ? '#334155' : '#e2e8f0'};
                color: ${isDark ? '#f8fafc' : '#0f172a'};
              }
              .doc-content h2 {
                font-size: 20px;
                font-weight: 600;
                margin: 36px 0 12px;
                color: ${isDark ? '#f1f5f9' : '#1e293b'};
              }
              .doc-content h3 {
                font-size: 16px;
                font-weight: 600;
                margin: 24px 0 10px;
                color: ${isDark ? '#e2e8f0' : '#334155'};
              }
              .doc-content p { margin: 14px 0; }
              .doc-content ul, .doc-content ol { padding-left: 20px; margin: 14px 0; }
              .doc-content li { margin: 6px 0; }
              .doc-content code {
                background: ${isDark ? '#334155' : '#f1f5f9'};
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Fira Code', 'SF Mono', Monaco, monospace;
                font-size: 13px;
              }
              .doc-content pre {
                background: ${isDark ? '#1e293b' : '#f8fafc'};
                padding: 16px;
                border-radius: 8px;
                overflow-x: auto;
                margin: 16px 0;
                border: 1px solid ${isDark ? '#334155' : '#e2e8f0'};
              }
              .doc-content pre code { background: transparent; padding: 0; }
              .doc-content blockquote {
                border-left: 3px solid #8b5cf6;
                padding-left: 16px;
                margin: 16px 0;
                color: ${isDark ? '#94a3b8' : '#64748b'};
                font-style: italic;
              }
              .doc-content strong { color: #f59e0b; font-weight: 600; }
              .doc-content em { color: #60a5fa; }
              .doc-content a { color: #8b5cf6; text-decoration: none; }
              .doc-content a:hover { text-decoration: underline; }
              .doc-content table { width: 100%; border-collapse: collapse; margin: 16px 0; }
              .doc-content th, .doc-content td {
                border: 1px solid ${isDark ? '#334155' : '#e2e8f0'};
                padding: 10px;
                text-align: left;
              }
              .doc-content th { background: ${isDark ? '#1e293b' : '#f8fafc'}; font-weight: 600; }
              .doc-content hr { border: none; border-top: 1px solid ${isDark ? '#334155' : '#e2e8f0'}; margin: 24px 0; }
              .doc-content img { max-width: 100%; border-radius: 8px; }
            `}</style>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {processedContent}
            </ReactMarkdown>
          </article>
        </div>
      </main>
    </div>
  );
}

function textToId(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s\u4e00-\u9fa5]/g, '')
    .replace(/\s+/g, '-');
}

export default DocReader;
