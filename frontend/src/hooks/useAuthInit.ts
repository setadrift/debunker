import { useEffect } from 'react'
import { useAuthStore } from '../stores/authStore'

export const useAuthInit = () => {
  const initFromStorage = useAuthStore((state) => state.initFromStorage)

  useEffect(() => {
    initFromStorage()
  }, [initFromStorage])
} 