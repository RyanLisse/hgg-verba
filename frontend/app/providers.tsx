'use client'

import React, { Suspense } from 'react'
import posthog from 'posthog-js'
import { PostHogProvider } from 'posthog-js/react'
import { usePathname, useSearchParams } from 'next/navigation'
import { useEffect } from 'react'
import { onCLS, onFID, onLCP } from 'web-vitals'


if (typeof window !== 'undefined') {
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
    capture_pageview: false, // Disable automatic pageview capture
    autocapture: false, // Disable autocapture
    persistence: 'memory', // Use memory persistence to avoid using cookies
    loaded: (posthog) => {
      // Custom event to replace pageview
      posthog.capture('$pageview')
    }
  })
  posthog.register({
    app_version: '1.0.0',
    platform: 'web'
  })

  window.addEventListener('error', (e) => {
    posthog.capture('error', {
      message: e.message,
      stack: e.error?.stack
    })
  })

  onCLS((metric) => posthog.capture('Web Vital', { name: 'CLS', value: metric.value }))
  
  // Updated onFID to capture the FID metric with the relevant entry
  onFID((metric) => {
    posthog.capture('Web Vital', { name: 'FID', value: metric.value, entry: metric });
  });

  onLCP((metric) => posthog.capture('Web Vital', { name: 'LCP', value: metric.value }))
}

function PageviewTracker() {
  const pathname = usePathname()
  const searchParams = useSearchParams()

  useEffect(() => {
    if (pathname) {
      let url = window.origin + pathname
      if (searchParams.toString()) {
        url = url + `?${searchParams.toString()}`
      }
      posthog.capture('$pageview', {
        $current_url: url,
      })
    }
  }, [pathname, searchParams])

  return null
}

export function CSPostHogProvider({ children }: { children: React.ReactNode }) {
  return (
    <PostHogProvider client={posthog}>
      <Suspense fallback={null}>
        <PageviewTracker />
      </Suspense>
      {children}
    </PostHogProvider>
  )
}