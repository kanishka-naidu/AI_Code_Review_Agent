'use client'

import Link from 'next/link'
import { LayoutWrapper } from '@/components/layout-wrapper'
import { Code2, Shield, BookOpen, Upload, Bot } from 'lucide-react'

export default function Dashboard() {
  const features = [
    {
      icon: Code2,
      title: 'AI Code Review',
      description: 'Detect maintainability and code quality issues.',
    },
    {
      icon: Shield,
      title: 'Security Analysis',
      description:
        'Identify common security vulnerabilities including SQL Injection, Hardcoded Secrets, Unsafe eval(), Runtime.exec() and more.',
    },
    {
      icon: BookOpen,
      title: 'OWASP & AI Recommendations',
      description:
        'Receive secure coding guidance, OWASP references and AI-generated fixes powered by Gemini and ChromaDB.',
    },
    {
      icon: Bot,
      title: 'AI Assistant',
      description: 'Get intelligent answers about your code, security issues, and best practices.',
    },
  ]

  return (
    <LayoutWrapper>
      <div className="mx-auto max-w-7xl px-6 py-16">
        {/* Hero Section */}
        <div className="space-y-8 mb-20 text-center">
          <div className="space-y-6">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-foreground leading-tight">
              Development of Smart Code Inspection Platform with Vulnerability Detection System
            </h1>

            <p className="text-lg md:text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              Analyze Python and Java code using AI-powered code review,
              security analysis, OWASP recommendations and
              Retrieval-Augmented Generation (RAG).
            </p>
          </div>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-20">
          {features.map((feature, idx) => {
            const Icon = feature.icon

            return (
              <div
                key={idx}
                className="rounded-xl border border-border bg-card p-6 hover:border-primary/50 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 cursor-default"
              >
                <div className="flex flex-col items-center text-center space-y-4">
                  <div className="rounded-xl bg-primary/10 p-4">
                    <Icon className="h-8 w-8 text-primary" />
                  </div>

                  <h3 className="font-semibold text-foreground text-lg">
                    {feature.title}
                  </h3>
                  
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </div>
            )
          })}
        </div>

        {/* Upload Card */}
        <div className="max-w-2xl mx-auto">
          <Link href="/upload">
            <div className="rounded-xl border border-border bg-card p-10 hover:border-primary/50 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 cursor-pointer group">
              <div className="flex items-center justify-center gap-6">
                <div className="rounded-xl bg-primary/10 p-6 group-hover:bg-primary/20 transition-all duration-300">
                  <Upload className="h-12 w-12 text-primary" />
                </div>

                <div className="text-left">
                  <h3 className="text-xl font-semibold text-foreground mb-2">
                    Upload Code
                  </h3>

                  <p className="text-base text-muted-foreground">
                    Upload .py or .java files for comprehensive AI analysis.
                  </p>
                </div>
              </div>
            </div>
          </Link>
        </div>
      </div>
    </LayoutWrapper>
  )
}