'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const MAX_FILE_SIZE = 5 * 1024 * 1024 // 5MB
const ACCEPTED_FILE_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
]

const applicationSchema = z.object({
  resume: z
    .instanceof(FileList)
    .refine((files) => files.length > 0, 'Resume is required')
    .refine(
      (files) => files[0]?.size <= MAX_FILE_SIZE,
      'Resume file size must be less than 5MB'
    )
    .refine(
      (files) => ACCEPTED_FILE_TYPES.includes(files[0]?.type),
      'Only PDF, DOC, and DOCX files are accepted'
    ),
  coverLetter: z.string().optional(),
})

type ApplicationFormData = z.infer<typeof applicationSchema>

interface ApplicationFormProps {
  jobId: string
  jobTitle: string
  company: string
  onSubmit: (data: { resume: File; coverLetter?: string }) => Promise<void>
  onCancel: () => void
  isSubmitting: boolean
}

export function ApplicationForm({
  jobId,
  jobTitle,
  company,
  onSubmit,
  onCancel,
  isSubmitting,
}: ApplicationFormProps) {
  const [uploadProgress, setUploadProgress] = useState(0)
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<ApplicationFormData>({
    resolver: zodResolver(applicationSchema),
  })

  const resumeFiles = watch('resume')

  const handleFormSubmit = async (data: ApplicationFormData) => {
    const resume = data.resume[0]
    setUploadProgress(0)

    // Simulate upload progress
    const progressInterval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval)
          return 90
        }
        return prev + 10
      })
    }, 100)

    try {
      await onSubmit({
        resume,
        coverLetter: data.coverLetter,
      })
      setUploadProgress(100)
    } finally {
      clearInterval(progressInterval)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      setSelectedFileName(files[0].name)
    } else {
      setSelectedFileName(null)
    }
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {/* Job Info */}
      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-1">Applying to:</h3>
        <p className="text-gray-900 font-medium">{jobTitle}</p>
        <p className="text-gray-600">{company}</p>
      </div>

      {/* Resume Upload */}
      <div>
        <label htmlFor="resume" className="block text-sm font-medium text-gray-700 mb-2">
          Resume <span className="text-red-500">*</span>
        </label>
        <div className="mt-1">
          <label
            htmlFor="resume"
            className="flex items-center justify-center w-full px-4 py-6 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors"
          >
            <div className="text-center">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
                aria-hidden="true"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <div className="mt-2">
                {selectedFileName ? (
                  <p className="text-sm text-gray-900 font-medium">{selectedFileName}</p>
                ) : (
                  <>
                    <p className="text-sm text-gray-600">
                      <span className="font-medium text-blue-600">Click to upload</span> or drag and drop
                    </p>
                    <p className="text-xs text-gray-500 mt-1">PDF, DOC, or DOCX (max 5MB)</p>
                  </>
                )}
              </div>
            </div>
            <input
              {...register('resume')}
              type="file"
              id="resume"
              className="sr-only"
              accept=".pdf,.doc,.docx"
              onChange={handleFileChange}
              disabled={isSubmitting}
            />
          </label>
        </div>
        {errors.resume && (
          <p className="mt-1 text-sm text-red-600">{errors.resume.message as string}</p>
        )}
      </div>

      {/* Upload Progress */}
      {isSubmitting && uploadProgress > 0 && (
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-gray-700">Uploading resume...</span>
            <span className="text-sm text-gray-700">{uploadProgress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Cover Letter */}
      <div>
        <label htmlFor="coverLetter" className="block text-sm font-medium text-gray-700 mb-2">
          Cover Letter <span className="text-gray-500 text-sm">(Optional)</span>
        </label>
        <textarea
          {...register('coverLetter')}
          id="coverLetter"
          rows={8}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 resize-none"
          placeholder="Tell the employer why you're a great fit for this position..."
          disabled={isSubmitting}
        />
        {errors.coverLetter && (
          <p className="mt-1 text-sm text-red-600">{errors.coverLetter.message}</p>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 pt-4">
        <button
          type="submit"
          disabled={isSubmitting}
          className="flex-1 px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting ? 'Submitting...' : 'Submit Application'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={isSubmitting}
          className="px-6 py-3 bg-white text-gray-700 font-medium rounded-lg border border-gray-300 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}
