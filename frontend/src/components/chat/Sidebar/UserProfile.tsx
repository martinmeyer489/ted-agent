'use client'

import { useState, useEffect } from 'react'
import { useStore } from '@/store'
import { Button } from '@/components/ui/button'
import Icon from '@/components/ui/icon'
import { motion, AnimatePresence } from 'framer-motion'

const industries = [
  'Technology',
  'Healthcare',
  'Construction',
  'Energy',
  'Transportation',
  'Education',
  'Finance',
  'Manufacturing',
  'Telecommunications',
  'Consulting',
  'Government',
  'Other'
]

const roles = [
  'Procurement Manager',
  'Business Development',
  'Project Manager',
  'C-Level Executive',
  'Consultant',
  'Analyst',
  'Other'
]

const companySizes = [
  'Solo / Freelancer',
  'Small (2-50)',
  'Medium (51-250)',
  'Large (251-1000)',
  'Enterprise (1000+)'
]

const interestOptions = [
  'IT Services',
  'Construction',
  'Healthcare',
  'Consulting',
  'Education',
  'Energy',
  'Transportation',
  'Research',
  'Defense',
  'Environmental'
]

export default function UserProfile() {
  const userProfile = useStore((s) => s.userProfile)
  const setUserProfile = useStore((s) => s.setUserProfile)
  const [isEditing, setIsEditing] = useState(!userProfile)
  const [isHovering, setIsHovering] = useState(false)
  
  const [formData, setFormData] = useState({
    industry: userProfile?.industry || '',
    role: userProfile?.role || '',
    companySize: userProfile?.companySize || '',
    interests: userProfile?.interests || []
  })

  useEffect(() => {
    if (userProfile) {
      setFormData({
        industry: userProfile.industry,
        role: userProfile.role,
        companySize: userProfile.companySize,
        interests: userProfile.interests
      })
    }
  }, [userProfile])

  const handleSave = () => {
    if (formData.industry && formData.role && formData.companySize) {
      setUserProfile(formData)
      setIsEditing(false)
      setIsHovering(false)
    }
  }

  const handleCancel = () => {
    if (userProfile) {
      setFormData({
        industry: userProfile.industry,
        role: userProfile.role,
        companySize: userProfile.companySize,
        interests: userProfile.interests
      })
      setIsEditing(false)
      setIsHovering(false)
    }
  }

  const toggleInterest = (interest: string) => {
    setFormData(prev => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest]
    }))
  }

  if (isEditing) {
    return (
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="text-xs font-medium uppercase text-gray-900">User Profile</div>
          {userProfile && (
            <Button
              variant="ghost"
              size="icon"
              onClick={handleCancel}
              className="h-6 w-6 hover:bg-gray-100"
            >
              <Icon type="x" size="xxs" />
            </Button>
          )}
        </div>

        {/* Industry */}
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-600">Industry *</label>
          <select
            value={formData.industry}
            onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
            className="h-9 rounded-xl border border-gray-200 bg-white px-3 text-xs text-gray-900 focus:border-blue-500 focus:outline-none"
          >
            <option value="">Select industry...</option>
            {industries.map((ind) => (
              <option key={ind} value={ind}>{ind}</option>
            ))}
          </select>
        </div>

        {/* Role */}
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-600">Role *</label>
          <select
            value={formData.role}
            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            className="h-9 rounded-xl border border-gray-200 bg-white px-3 text-xs text-gray-900 focus:border-blue-500 focus:outline-none"
          >
            <option value="">Select role...</option>
            {roles.map((role) => (
              <option key={role} value={role}>{role}</option>
            ))}
          </select>
        </div>

        {/* Company Size */}
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-600">Company Size *</label>
          <select
            value={formData.companySize}
            onChange={(e) => setFormData({ ...formData, companySize: e.target.value })}
            className="h-9 rounded-xl border border-gray-200 bg-white px-3 text-xs text-gray-900 focus:border-blue-500 focus:outline-none"
          >
            <option value="">Select size...</option>
            {companySizes.map((size) => (
              <option key={size} value={size}>{size}</option>
            ))}
          </select>
        </div>

        {/* Interests */}
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-600">Interests (optional)</label>
          <div className="flex flex-wrap gap-1">
            {interestOptions.map((interest) => (
              <button
                key={interest}
                onClick={() => toggleInterest(interest)}
                className={`rounded-full px-2 py-1 text-xs transition-colors ${
                  formData.interests.includes(interest)
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {interest}
              </button>
            ))}
          </div>
        </div>

        <Button
          onClick={handleSave}
          disabled={!formData.industry || !formData.role || !formData.companySize}
          className="h-9 rounded-xl bg-blue-600 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          Save Profile
        </Button>
      </div>
    )
  }

  // Display mode
  return (
    <div className="flex flex-col gap-2">
      <div className="text-xs font-medium uppercase text-gray-900">User Profile</div>
      
      <motion.div
        className="relative flex cursor-pointer flex-col gap-2 rounded-xl border border-gray-200 bg-gray-50 p-3"
        onMouseEnter={() => setIsHovering(true)}
        onMouseLeave={() => setIsHovering(false)}
        onClick={() => setIsEditing(true)}
      >
        <AnimatePresence mode="wait">
          {isHovering ? (
            <motion.div
              key="edit-overlay"
              className="absolute inset-0 flex items-center justify-center rounded-xl bg-blue-600/90"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <p className="flex items-center gap-2 text-xs font-medium text-white">
                <Icon type="edit" size="xxs" /> EDIT PROFILE
              </p>
            </motion.div>
          ) : (
            <motion.div
              key="profile-content"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <div className="text-xs text-gray-600">
                <div className="mb-1">
                  <span className="font-medium text-gray-900">{userProfile?.industry}</span>
                </div>
                <div className="mb-1 text-[10px]">
                  {userProfile?.role} • {userProfile?.companySize}
                </div>
                {userProfile?.interests && userProfile.interests.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {userProfile.interests.map((interest) => (
                      <span
                        key={interest}
                        className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] text-blue-700"
                      >
                        {interest}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  )
}
