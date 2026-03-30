'use client'

import { motion, HTMLMotionProps } from 'framer-motion'
import { ReactNode } from 'react'

interface AnimationWrapperProps extends HTMLMotionProps<'div'> {
  children: ReactNode
  delay?: number
  duration?: number
  variant?: 'fade' | 'slide-up' | 'slide-down' | 'scale'
}

export function AnimationWrapper({ 
  children, 
  delay = 0, 
  duration = 0.5, 
  variant = 'slide-up',
  ...props 
}: AnimationWrapperProps) {
  const variants = {
    fade: {
      hidden: { opacity: 0 },
      visible: { opacity: 1 }
    },
    'slide-up': {
      hidden: { opacity: 0, y: 20 },
      visible: { opacity: 1, y: 0 }
    },
    'slide-down': {
      hidden: { opacity: 0, y: -20 },
      visible: { opacity: 1, y: 0 }
    },
    scale: {
      hidden: { opacity: 0, scale: 0.95 },
      visible: { opacity: 1, scale: 1 }
    }
  }

  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-50px" }}
      transition={{ 
        duration, 
        delay, 
        ease: [0.22, 1, 0.36, 1] as [number, number, number, number] 
      }}
      variants={variants[variant]}
      {...props}
    >
      {children}
    </motion.div>
  )
}

export const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
}

export const staggerItem = {
  hidden: { opacity: 0, y: 15 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: {
      duration: 0.5,
      ease: [0.22, 1, 0.36, 1] as [number, number, number, number]
    }
  }
}
