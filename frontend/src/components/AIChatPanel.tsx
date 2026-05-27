"use client";
import React, { useState, useEffect, useRef, KeyboardEvent } from 'react';
import { ChatRequest, ChatResponse, AnalysisSummary, RiskSummary } from '@/utils/api'; // We'll extend api.ts types later
import { fetchChat } from '@/utils/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface AIChatPanelProps {
  ticker: string;
}

export default function AIChatPanel({ ticker }: AIChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const scrollRef = useRef<HTMLDivElement>(null);

  const quickPrompts = [
    'Is this a good entry?',
    'What are the risks?',
    'Bullish vs bearish case',
    'Explain stop loss',
    'How strong is this setup?',
  ];

  const scrollToBottom = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const sendMessage = async (msg: string) => {
    if (!msg.trim()) return;
    const userMsg: Message = { role: 'user', content: msg };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setError('');
    try {
      const request: ChatRequest = {
        ticker,
        user_message: msg,
        conversation_history: messages.map((m) => ({ role: m.role, content: m.content })),
      };
      const response: ChatResponse = await fetchChat(request);
      // Append assistant response as a single message (including structured summary)
      const assistantMsg: Message = { role: 'assistant', content: response.response };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e: any) {
      console.error(e);
      setError(e.message || 'Chat request failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (loading) return;
    sendMessage(input);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!loading) sendMessage(input);
    }
  };

  const handleQuickPrompt = (prompt: string) => {
    if (loading) return;
    sendMessage(prompt);
  };

  return (
    <section className="max-w-2xl mx-auto w-full mt-8 flex flex-col gap-4">
      <h2 className="text-xl font-semibold text-slate-100">AI Trading Copilot</h2>
      <div
        className="flex-1 max-h-96 overflow-y-auto rounded-lg bg-slate-900/60 backdrop-blur-md p-4 space-y-3"
        ref={scrollRef}
      >
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'assistant' ? 'justify-start' : 'justify-end'} `}
          >
            <div
              className={`max-w-xs rounded-lg p-3 text-sm ${{
                assistant: 'bg-slate-800 text-slate-200',
                user: 'bg-emerald-800 text-emerald-100',
              }[msg.role]}`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="text-slate-400 animate-pulse">AI is thinking...</div>
          </div>
        )}
        {error && <div className="text-red-400 text-sm">{error}</div>}
      </div>

      {/* Quick prompt buttons */}
      <div className="flex flex-wrap gap-2">
        {quickPrompts.map((p) => (
          <button
            key={p}
            className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300 hover:bg-slate-700 transition"
            onClick={() => handleQuickPrompt(p)}
          >
            {p}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <textarea
          className="flex-1 rounded-md bg-slate-800 text-slate-100 p-2 resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500"
          rows={2}
          placeholder="Ask the copilot..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button
          type="submit"
          className="px-4 py-2 bg-emerald-600 text-slate-100 rounded-md hover:bg-emerald-500 disabled:opacity-50"
          disabled={loading || !input.trim()}
        >
          Send
        </button>
      </form>
    </section>
  );
}
