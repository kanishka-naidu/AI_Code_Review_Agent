'use client'

import { useState, useRef } from 'react'
import { Upload, Play } from 'lucide-react'

interface InputPanelProps {
  onAnalyze: (code: string, language: string) => void
  isLoading?: boolean
}

const languages = ['Auto Detect', 'Python', 'Java']

export function InputPanel({
  onAnalyze,
  isLoading = false,
}: InputPanelProps) {
  const [language, setLanguage] = useState('Auto Detect')
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [error, setError] = useState('')
  const [isDragOver, setIsDragOver] = useState(false)

  const fileInputRef = useRef<HTMLInputElement>(null)

  const supportedExtensions = ['.py', '.java']

  const handleAnalyze = () => {
    if (!uploadedFile) return

    const reader = new FileReader()

    reader.onload = (e) => {
      const content = e.target?.result as string
      onAnalyze(content, language)
    }

    reader.readAsText(uploadedFile)
  }

  const handleFileSelect = (file: File) => {
    setError('')

    const ext = '.' + file.name.split('.').pop()?.toLowerCase()

    if (!supportedExtensions.includes(ext)) {
      setError('Only .py and .java files are allowed.')
      setUploadedFile(null)
      return
    }

    setUploadedFile(file)
    setIsDragOver(false)
  }

  const handleFileInputChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    if (e.target.files?.[0]) {
      handleFileSelect(e.target.files[0])
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)

    if (e.dataTransfer.files?.[0]) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleRemoveFile = () => {
    setUploadedFile(null)
    setError('')

    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="flex flex-col gap-4">

      {/* Language */}
      <div className="flex gap-3 items-center">
        <label className="text-sm text-muted-foreground">
          Language:
        </label>

        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="rounded-lg border border-border bg-input px-3 py-2 text-sm"
        >
          {languages.map((lang) => (
            <option key={lang}>{lang}</option>
          ))}
        </select>
      </div>

      {/* Upload Area */}

      {uploadedFile ? (
        <div className="flex h-96 w-full flex-col items-center justify-center rounded-lg border-2 border-dashed border-border bg-input/30">

          <input
            ref={fileInputRef}
            type="file"
            accept=".py,.java"
            onChange={handleFileInputChange}
            className="hidden"
          />

          <Upload className="h-12 w-12 text-primary" />

          <h3 className="mt-4 font-semibold">
            {uploadedFile.name}
          </h3>

          <p className="text-sm text-muted-foreground">
            {(uploadedFile.size / 1024).toFixed(2)} KB
          </p>

          <div className="mt-6 flex gap-3">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="rounded-lg bg-primary px-4 py-2 text-primary-foreground"
            >
              Change File
            </button>

            <button
              onClick={handleRemoveFile}
              className="rounded-lg border px-4 py-2"
            >
              Remove
            </button>
          </div>
        </div>
      ) : (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={`flex h-96 cursor-pointer items-center justify-center rounded-lg border-2 border-dashed transition ${
            isDragOver
              ? 'border-primary bg-primary/5'
              : 'border-border bg-input/30'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".py,.java"
            onChange={handleFileInputChange}
            className="hidden"
          />

          <div className="text-center">
            <Upload className="mx-auto h-12 w-12 text-primary" />

            <p className="mt-4 font-medium">
              Drag & Drop your file here
            </p>

            <p className="text-sm text-muted-foreground">
              or click to browse
            </p>

            <p className="mt-2 text-xs text-muted-foreground">
              Supported: .py, .java
            </p>
          </div>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-500 bg-red-50 p-3 text-red-600">
          {error}
        </div>
      )}

      <button
        onClick={handleAnalyze}
        disabled={isLoading || !uploadedFile}
        className="flex items-center justify-center gap-2 rounded-lg bg-primary px-6 py-3 text-primary-foreground disabled:opacity-50"
      >
        <Play className="h-4 w-4" />
        {isLoading ? 'Analyzing...' : 'Analyze Code'}
      </button>
    </div>
  )
}